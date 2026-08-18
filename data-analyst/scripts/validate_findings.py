#!/usr/bin/env python3
"""Tie-out harness — independently re-computes every claimed number in a findings log.

SECURITY: findings.json IS EXECUTABLE CODE. The `pandas` expressions are run with
eval() and the `sql` with DuckDB — the restricted-builtins namespace is a guard rail,
not a sandbox. Treat a findings.json exactly like a Python script: only validate files
you (or your own analysis session) wrote. Never run this on a findings.json from an
untrusted source.

Reads a findings.json (format below), executes each claim's `pandas` expression and
`sql` query as two independent code paths, and compares both against the claimed value.

findings.json format:
{
  "dataset": {"files": {"subs": "data/subscriptions.csv"}},
  "claims": [
    {
      "id": "F3",
      "claim": "Partner-channel monthly churn averaged 8.1% in 2026-Q2",
      "value": 0.081,
      "tolerance_pct": 0.5,
      "recompute": {
        "file": "subs",
        "pandas": "df[(df.month>='2026-04')&(df.channel=='partner')].churned.mean()",
        "sql": "SELECT AVG(churned) FROM subs WHERE month>='2026-04' AND channel='partner'"
      }
    }
  ]
}

In SQL, every entry in dataset.files is available as a table under its key name.
In pandas expressions, `df` is the claim's file; all files are also available by key
(e.g. `subs`, `stores`), plus `pd` and `np`.

Severities:
  PASS     both paths ran, agree with each other AND with the claim (within tolerance)
  WARNING  only one path could run (e.g. no sql given / duckdb missing) but it agrees
           with the claim
  BLOCKER  recomputed value(s) contradict the claim, the two paths contradict each
           other, or a recompute failed to execute — a number in the report is not
           trustworthy

Usage: python validate_findings.py findings.json [--report OUT.md]
Exit code: 2 if any BLOCKER, else 0.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import duckdb
except ImportError:
    duckdb = None


def load_frames(files: dict, base: Path) -> dict:
    frames = {}
    for key, rel in files.items():
        p = Path(rel)
        if not p.is_absolute():
            p = (base / rel).resolve()
        if p.suffix.lower() in (".parquet", ".pq"):
            frames[key] = pd.read_parquet(p)
        else:
            frames[key] = pd.read_csv(p)
    return frames


def as_scalar(value):
    if isinstance(value, (pd.Series, pd.DataFrame)):
        arr = value.to_numpy().ravel()
        if arr.size != 1:
            raise ValueError(f"expression returned {arr.size} values, expected a scalar")
        value = arr[0]
    if isinstance(value, (np.generic,)):
        value = value.item()
    return float(value)


def rel_diff_pct(a: float, b: float) -> float:
    denom = max(abs(a), abs(b), 1e-12)
    return 100.0 * abs(a - b) / denom


def check_claim(claim: dict, frames: dict, con) -> dict:
    tol = float(claim.get("tolerance_pct", 0.5))
    claimed = float(claim["value"])
    rc = claim.get("recompute") or {}
    result = {"id": claim.get("id"), "claim": claim.get("claim"), "claimed": claimed,
              "pandas": None, "sql": None, "errors": []}

    if rc.get("pandas"):
        try:
            df = frames.get(rc.get("file")) if rc.get("file") else None
            namespace = {"pd": pd, "np": np, **frames}
            if df is not None:
                namespace["df"] = df
            result["pandas"] = as_scalar(eval(rc["pandas"], {"__builtins__": {}}, namespace))  # noqa: S307 — analyst-authored expression
        except Exception as exc:
            result["errors"].append(f"pandas path failed: {exc}")

    if rc.get("sql"):
        if con is None:
            result["errors"].append("sql path skipped: duckdb not installed")
        else:
            try:
                result["sql"] = as_scalar(con.execute(rc["sql"]).fetchone()[0])
            except Exception as exc:
                result["errors"].append(f"sql path failed: {exc}")

    ran = [v for v in (result["pandas"], result["sql"]) if v is not None]
    if not ran:
        result["severity"] = "BLOCKER"
        result["detail"] = "no recompute path could run: " + "; ".join(result["errors"] or ["no recompute spec"])
        return result

    if len(ran) == 2 and rel_diff_pct(ran[0], ran[1]) > tol:
        result["severity"] = "BLOCKER"
        result["detail"] = (f"independent paths disagree: pandas={ran[0]:.6g} vs sql={ran[1]:.6g} "
                            f"({rel_diff_pct(ran[0], ran[1]):.2f}% > {tol}%) — computation unstable")
        return result

    recomputed = ran[0]
    diff = rel_diff_pct(recomputed, claimed)
    if diff > tol:
        result["severity"] = "BLOCKER"
        result["detail"] = f"claim says {claimed:.6g}, recomputed {recomputed:.6g} ({diff:.2f}% > {tol}%) — fix the report"
    elif len(ran) == 1:
        result["severity"] = "WARNING"
        why = "no sql path" if not rc.get("sql") else "; ".join(result["errors"]) or "single path"
        result["detail"] = f"matches claim ({diff:.2f}% ≤ {tol}%) but verified through one path only ({why})"
    else:
        result["severity"] = "PASS"
        result["detail"] = f"both paths agree with claim ({diff:.2f}% ≤ {tol}%)"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("findings", help="path to findings.json")
    ap.add_argument("--report", default=None, help="output markdown path (default: alongside findings)")
    args = ap.parse_args()

    findings_path = Path(args.findings).resolve()
    spec = json.loads(findings_path.read_text())
    frames = load_frames(spec.get("dataset", {}).get("files", {}), findings_path.parent)

    con = None
    if duckdb is not None:
        con = duckdb.connect()
        for key, frame in frames.items():
            con.register(key, frame)

    results = [check_claim(c, frames, con) for c in spec.get("claims", [])]

    order = {"BLOCKER": 0, "WARNING": 1, "PASS": 2}
    counts = {s: sum(1 for r in results if r["severity"] == s) for s in order}
    gate = "HALT" if counts["BLOCKER"] else ("PROCEED WITH CAUTION" if counts["WARNING"] else "PROCEED")

    lines = ["# Findings tie-out", "",
             f"**Gate: {gate}**  (PASS {counts['PASS']} · WARNING {counts['WARNING']} · BLOCKER {counts['BLOCKER']})",
             "",
             "| id | severity | claimed | pandas | sql | detail |",
             "|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda r: order[r["severity"]]):
        fmt = lambda v: "—" if v is None else f"{v:.6g}"
        lines.append(f"| {r['id']} | {r['severity']} | {fmt(r['claimed'])} | {fmt(r['pandas'])} "
                     f"| {fmt(r['sql'])} | {r['detail']} |")
    report = "\n".join(lines) + "\n"

    out = Path(args.report) if args.report else findings_path.with_name("findings_validation.md")
    out.write_text(report)
    print(report)
    return 2 if counts["BLOCKER"] else 0


if __name__ == "__main__":
    sys.exit(main())
