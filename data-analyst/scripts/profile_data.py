#!/usr/bin/env python3
"""Deterministic data profiler — run BEFORE any interpretation of the data.

Reports schema, missingness, duplicates, candidate keys, numeric ranges, date
coverage/gaps, cardinality, and suspicious patterns, with severities:
  BLOCKER  analysis on this data is invalid until resolved/acknowledged
  WARNING  could distort conclusions; must be addressed or caveated
  INFO     worth knowing

Usage:
  python profile_data.py file1.csv [file2.parquet ...] [--outdir DIR] [--html]

Outputs per file: <outdir>/<stem>_profile.json and <stem>_profile.md
Plus <outdir>/summary.md with all findings sorted by severity.
Exit code: 2 if any BLOCKER, else 0.

Only requires pandas. --html additionally uses fg-data-profiling/ydata-profiling
if installed (optional).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

DATE_NAME_HINT = re.compile(r"(date|month|day|time|_at$|_dt$|week|year)", re.I)


def read_any(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in (".parquet", ".pq"):
        return pd.read_parquet(path)
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if suffix == ".json":
        return pd.read_json(path)
    return pd.read_csv(path)


def detect_datetime(series: pd.Series, name: str):
    """Return parsed datetime series if the column plausibly holds dates."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    if series.dtype == object or DATE_NAME_HINT.search(name):
        sample = series.dropna().astype(str).head(500)
        if sample.empty:
            return None
        try:
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
        except (ValueError, TypeError):
            return None
        if parsed.notna().mean() >= 0.95:
            try:
                return pd.to_datetime(series, errors="coerce", format="mixed")
            except (ValueError, TypeError):
                return None
    return None


def month_gaps(dates: pd.Series):
    """Missing calendar months between min and max observed month."""
    months = dates.dropna().dt.to_period("M")
    if months.empty:
        return []
    present = set(months.unique())
    full = pd.period_range(months.min(), months.max(), freq="M")
    return [str(m) for m in full if m not in present]


def profile_file(path: Path) -> dict:
    findings = []  # (severity, message)
    prof = {"file": str(path), "findings": findings}
    try:
        df = read_any(path)
    except Exception as exc:  # unreadable file is a hard stop
        findings.append(("BLOCKER", f"cannot read file: {exc}"))
        return prof

    n_rows, n_cols = df.shape
    prof["rows"] = int(n_rows)
    prof["columns"] = int(n_cols)
    if n_rows == 0:
        findings.append(("BLOCKER", "file has 0 rows"))
        return prof

    # Full-row duplicates
    dup = int(df.duplicated().sum())
    prof["duplicate_rows"] = dup
    if dup:
        pct = 100.0 * dup / n_rows
        sev = "BLOCKER" if pct >= 1.0 else "WARNING"
        findings.append((sev, f"{dup} duplicate rows ({pct:.2f}% of {n_rows}) — dedup or justify before any aggregate"))

    cols = {}
    candidate_keys = []
    for name in df.columns:
        s = df[name]
        info = {
            "dtype": str(s.dtype),
            "nulls": int(s.isna().sum()),
            "null_pct": round(100.0 * s.isna().mean(), 2),
            "n_unique": int(s.nunique(dropna=True)),
        }
        if info["null_pct"] >= 90:
            findings.append(("WARNING", f"column '{name}' is {info['null_pct']}% null — effectively empty"))
        elif info["null_pct"] >= 20:
            findings.append(("WARNING", f"column '{name}' is {info['null_pct']}% null"))
        if info["n_unique"] == 1 and n_rows > 1:
            findings.append(("INFO", f"column '{name}' is constant"))
        if info["n_unique"] == n_rows and info["nulls"] == 0:
            candidate_keys.append(name)

        if pd.api.types.is_numeric_dtype(s):
            desc = s.describe()
            info["min"] = None if pd.isna(desc.get("min")) else float(desc["min"])
            info["max"] = None if pd.isna(desc.get("max")) else float(desc["max"])
            info["mean"] = None if pd.isna(desc.get("mean")) else float(desc["mean"])
            info["sum"] = float(s.sum())
            negatives = int((s < 0).sum())
            if negatives and re.search(r"(amount|price|revenue|mrr|qty|units|count|total)", name, re.I):
                findings.append(("WARNING", f"column '{name}' has {negatives} negative values — refunds, corrections, or errors?"))
        else:
            top = s.dropna().astype(str).value_counts().head(5)
            info["top_values"] = {str(k): int(v) for k, v in top.items()}
            # mixed types hiding in object columns
            if s.dtype == object:
                kinds = s.dropna().map(lambda v: type(v).__name__).nunique()
                if kinds > 1:
                    findings.append(("WARNING", f"column '{name}' mixes python types — check parsing"))

        parsed = detect_datetime(s, name)
        if parsed is not None and parsed.notna().any():
            info["date_min"] = str(parsed.min().date())
            info["date_max"] = str(parsed.max().date())
            gaps = month_gaps(parsed)
            if gaps:
                info["missing_months"] = gaps
                findings.append(("WARNING", f"column '{name}' has missing calendar months: {', '.join(gaps[:6])}"
                                            + (" ..." if len(gaps) > 6 else "") + " — trend math over this range is broken until handled"))
        cols[name] = info

    prof["columns_detail"] = cols
    prof["candidate_keys"] = candidate_keys
    if not candidate_keys:
        findings.append(("INFO", "no single-column candidate key (unique, non-null) — dedup and joins need a composite key"))
    return prof


def to_markdown(prof: dict) -> str:
    lines = [f"# Profile: {prof['file']}", ""]
    if "rows" in prof:
        lines.append(f"Rows: {prof['rows']}  |  Columns: {prof['columns']}  |  "
                     f"Duplicate rows: {prof.get('duplicate_rows', 0)}  |  "
                     f"Candidate keys: {', '.join(prof.get('candidate_keys') or ['none'])}")
        lines.append("")
        lines.append("| column | dtype | null% | unique | range / top values |")
        lines.append("|---|---|---|---|---|")
        for name, c in prof["columns_detail"].items():
            if "min" in c:
                extra = f"min {c['min']}, max {c['max']}, sum {c['sum']:.4g}"
            elif "date_min" in c:
                extra = f"{c['date_min']} → {c['date_max']}"
                if c.get("missing_months"):
                    extra += f" (missing: {len(c['missing_months'])} months)"
            else:
                extra = ", ".join(list(c.get("top_values", {}))[:3])
            lines.append(f"| {name} | {c['dtype']} | {c['null_pct']} | {c['n_unique']} | {extra} |")
        lines.append("")
    lines.append("## Findings")
    if prof["findings"]:
        for sev, msg in sorted(prof["findings"], key=lambda f: {"BLOCKER": 0, "WARNING": 1, "INFO": 2}[f[0]]):
            lines.append(f"- **{sev}**: {msg}")
    else:
        lines.append("- no issues detected")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--outdir", default="profile")
    ap.add_argument("--html", action="store_true", help="also emit ydata/fg-data-profiling HTML if installed")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    all_findings = []
    for f in args.files:
        path = Path(f)
        prof = profile_file(path)
        stem = path.stem
        (outdir / f"{stem}_profile.json").write_text(json.dumps(prof, indent=2, default=str))
        (outdir / f"{stem}_profile.md").write_text(to_markdown(prof))
        for sev, msg in prof["findings"]:
            all_findings.append((sev, f"{path.name}: {msg}"))
        if args.html and "rows" in prof:
            try:
                try:
                    from data_profiling import ProfileReport  # fg-data-profiling
                except ImportError:
                    from ydata_profiling import ProfileReport
                ProfileReport(read_any(path), title=f"Profile {path.name}", minimal=True).to_file(outdir / f"{stem}_profile.html")
            except ImportError:
                print("note: --html skipped (fg-data-profiling/ydata-profiling not installed)", file=sys.stderr)

    order = {"BLOCKER": 0, "WARNING": 1, "INFO": 2}
    all_findings.sort(key=lambda f: order[f[0]])
    summary = ["# Profiling summary", ""]
    counts = {s: sum(1 for sev, _ in all_findings if sev == s) for s in order}
    summary.append(f"BLOCKER: {counts['BLOCKER']}  |  WARNING: {counts['WARNING']}  |  INFO: {counts['INFO']}")
    summary.append("")
    summary += [f"- **{sev}**: {msg}" for sev, msg in all_findings] or ["- clean"]
    (outdir / "summary.md").write_text("\n".join(summary) + "\n")

    print("\n".join(summary))
    return 2 if counts["BLOCKER"] else 0


if __name__ == "__main__":
    sys.exit(main())
