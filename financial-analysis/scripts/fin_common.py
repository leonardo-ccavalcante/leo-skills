"""fin_common — shared contracts for the financial-analysis skill.

Every calculation script in this skill builds on three ideas:

1. Tagged inputs. A number without provenance is a liability. Every input
   carries a status — user | public | assumption | unknown — so the analysis
   never silently blends facts with guesses. `unknown` means value is None;
   it is NEVER replaced with a default.

2. The Result envelope. Scripts compute everything they can from partial
   data and report, machine-readably, what they could not compute and why
   (`not_computed`), and what inputs are missing ranked by impact
   (`missing`). The `missing` list is the interactive layer's interrogation
   agenda: the model asks for the highest-priority gap first.

3. Guarded formulas. Division by zero, negative denominators, or absent
   inputs produce a `not_computed` entry with a reason — never Infinity,
   never a magic default. A wrong-but-plausible number is worse than an
   honest gap.

Exit codes: 0 = OK or PARTIAL · 2 = INSUFFICIENT_DATA · 3 = validation
failure · 1 = unexpected error. JSON goes to stdout; diagnostics to stderr.

Stdlib-only except `load_table`, which lazily imports pandas (only needed
for CSV/Excel inputs — the conversation path never touches pandas).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field

VERSION = "1.0.0"

INPUT_STATUSES = ("user", "public", "assumption", "unknown")
CALC_STATUS = "calculation"

EXIT_OK = 0
EXIT_UNEXPECTED = 1
EXIT_INSUFFICIENT = 2
EXIT_VALIDATION = 3


# ---------------------------------------------------------------------------
# Tagged values
# ---------------------------------------------------------------------------

@dataclass
class Tagged:
    """One input number with provenance."""

    value: object  # float | int | str | list | None (None iff status == "unknown")
    status: str = "user"
    basis: str | None = None
    source_url: str | None = None
    confidence: str | None = None  # low | medium | high (optional)

    def is_known(self) -> bool:
        return self.status != "unknown" and self.value is not None

    def as_dict(self) -> dict:
        d = {"value": self.value, "status": self.status}
        if self.basis:
            d["basis"] = self.basis
        if self.source_url:
            d["source_url"] = self.source_url
        if self.confidence:
            d["confidence"] = self.confidence
        return d


def parse_inputs(raw: dict, warnings: list[str] | None = None) -> dict[str, Tagged]:
    """Convert a raw inputs dict into Tagged values.

    Accepts both the full form {"churn": {"value": 0.03, "status": "assumption",
    "basis": "..."}} and bare scalars {"churn": 0.03}. Bare scalars are
    auto-tagged `user` and a warning is recorded — explicit tags are always
    preferred because the tag is what keeps assumptions visible downstream.
    """
    out: dict[str, Tagged] = {}
    for name, v in raw.items():
        if isinstance(v, dict) and "value" in v:
            status = v.get("status", "user")
            if status not in INPUT_STATUSES:
                raise ValueError(
                    f"input '{name}': status '{status}' is not one of {INPUT_STATUSES}"
                )
            value = v.get("value")
            if status == "unknown" and value is not None:
                raise ValueError(
                    f"input '{name}': status 'unknown' requires value null — "
                    "a number you have should be tagged user/public/assumption"
                )
            if status != "unknown" and value is None:
                # A null value with a non-unknown tag is a silent downgrade risk.
                status = "unknown"
                if warnings is not None:
                    warnings.append(
                        f"input '{name}' had null value; treated as unknown"
                    )
            out[name] = Tagged(
                value=value,
                status=status,
                basis=v.get("basis"),
                source_url=v.get("source_url"),
                confidence=v.get("confidence"),
            )
        else:
            out[name] = Tagged(value=v, status="user")
            if warnings is not None:
                warnings.append(
                    f"input '{name}' was untagged; treated as user-provided — "
                    "prefer explicit tags (user/public/assumption/unknown)"
                )
    return out


def load_inputs(src: str, warnings: list[str] | None = None) -> dict[str, Tagged]:
    """Load tagged inputs from an inline JSON string or a .json file path."""
    if src.strip().startswith("{"):
        raw = json.loads(src)
    else:
        with open(src, "r", encoding="utf-8") as f:
            raw = json.load(f)
    if not isinstance(raw, dict):
        raise ValueError("inputs must be a JSON object")
    # Allow a top-level {"inputs": {...}} wrapper (the .fa.json state format).
    if "inputs" in raw and isinstance(raw["inputs"], dict):
        raw = raw["inputs"]
    return parse_inputs(raw, warnings)


def num(inputs: dict[str, Tagged], name: str) -> float | None:
    """Numeric value of an input, or None when absent/unknown/non-numeric."""
    t = inputs.get(name)
    if t is None or not t.is_known():
        return None
    try:
        return float(t.value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Table loading (the only pandas touchpoint)
# ---------------------------------------------------------------------------

def load_table(path: str, required_cols: list[str], rename: dict | None = None):
    """Load a CSV/Excel file into a DataFrame, verifying required columns.

    pandas is imported lazily so that every conversation-input analysis works
    on a machine without pandas installed.
    """
    try:
        import pandas as pd  # noqa: PLC0415
    except ImportError:
        raise SystemExit(
            "This input path requires pandas (and openpyxl for .xlsx).\n"
            "Install with: pip install pandas openpyxl\n"
            "Or restate the key figures in conversation as tagged JSON inputs."
        )
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    if rename:
        df = df.rename(columns=rename)
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise SystemExit(
            f"{os.path.basename(path)} is missing required column(s): {missing}. "
            f"Found columns: {list(df.columns)}. "
            "See references/input-formats.md — agree on a column mapping with "
            "the user instead of guessing."
        )
    return df


# ---------------------------------------------------------------------------
# Result envelope
# ---------------------------------------------------------------------------

@dataclass
class Result:
    """Accumulates computed metrics, gaps, and diagnostics for one script run."""

    script: str
    version: str = VERSION
    inputs_echo: dict = field(default_factory=dict)
    results: dict = field(default_factory=dict)
    not_computed: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    invariants: list = field(default_factory=list)
    status: str = "OK"

    # -- recording -----------------------------------------------------------

    def echo_inputs(self, inputs: dict[str, Tagged]) -> None:
        self.inputs_echo = {k: t.as_dict() for k, t in inputs.items()}

    def add(self, name: str, value, formula: str, inputs_used: list[str],
            unit: str | None = None) -> None:
        if isinstance(value, float):
            if value != value or value in (float("inf"), float("-inf")):
                # NaN/Inf must never appear in results — that's a guard bug.
                self.skip(name, "computation produced a non-finite value")
                return
            value = round(value, 6)
        entry = {"value": value, "status": CALC_STATUS, "formula": formula,
                 "inputs_used": inputs_used}
        if unit:
            entry["unit"] = unit
        self.results[name] = entry

    def add_table(self, name: str, rows: list[dict], formula: str) -> None:
        """A tabular result (e.g. monthly projection, ARR bridge)."""
        self.results[name] = {"value": rows, "status": CALC_STATUS,
                              "formula": formula, "inputs_used": []}

    def skip(self, name: str, reason: str, needed: list[str] | None = None) -> None:
        self.not_computed.append(
            {"metric": name, "reason": reason, "needed": needed or []}
        )

    def need(self, fieldname: str, why: str, priority: int) -> None:
        if not any(m["field"] == fieldname for m in self.missing):
            self.missing.append(
                {"field": fieldname, "why_needed": why, "priority": priority}
            )

    def warn(self, msg: str) -> None:
        if msg not in self.warnings:
            self.warnings.append(msg)

    def invariant(self, check: str, passed: bool, detail: str = "") -> None:
        self.invariants.append({"check": check, "passed": passed, "detail": detail})

    def require(self, inputs: dict[str, Tagged], spec: dict[str, str]) -> bool:
        """Check critical inputs. spec maps name -> why_needed.

        Missing/unknown criticals are recorded with priority 1 and the
        method returns False — callers should then finalize; status becomes
        INSUFFICIENT_DATA when nothing was computable.
        """
        ok = True
        for name, why in spec.items():
            if num(inputs, name) is None and not (
                name in inputs and inputs[name].is_known()
            ):
                self.need(name, why, priority=1)
                ok = False
        return ok

    # -- finishing -----------------------------------------------------------

    def finalize(self) -> int:
        self.missing.sort(key=lambda m: m["priority"])
        failed_invariants = [i for i in self.invariants if not i["passed"]]
        if failed_invariants:
            self.status = "VALIDATION_FAILED"
            return EXIT_VALIDATION
        if not self.results:
            self.status = "INSUFFICIENT_DATA"
            return EXIT_INSUFFICIENT
        self.status = "PARTIAL" if (self.missing or self.not_computed) else "OK"
        return EXIT_OK

    def as_dict(self) -> dict:
        return {
            "script": self.script,
            "version": self.version,
            "status": self.status,
            "inputs_echo": self.inputs_echo,
            "results": self.results,
            "not_computed": self.not_computed,
            "missing": self.missing,
            "warnings": self.warnings,
            "invariants": self.invariants,
        }

    def emit(self, as_json: bool) -> None:
        if as_json:
            print(json.dumps(self.as_dict(), indent=2, default=str))
            return
        # Human-readable fallback
        print(f"[{self.script}] status: {self.status}")
        for name, r in self.results.items():
            val = r["value"]
            if isinstance(val, list):
                print(f"  {name}: <table with {len(val)} rows> (use --json to inspect)")
            else:
                unit = f" {r.get('unit')}" if r.get("unit") else ""
                print(f"  {name}: {val}{unit}   [{r['formula']}]")
        for nc in self.not_computed:
            print(f"  ! not computed: {nc['metric']} — {nc['reason']}")
        for m in self.missing:
            print(f"  ? missing (p{m['priority']}): {m['field']} — {m['why_needed']}")
        for w in self.warnings:
            print(f"  ~ warning: {w}", file=sys.stderr)
        for i in self.invariants:
            mark = "ok" if i["passed"] else "FAILED"
            print(f"  # invariant {i['check']}: {mark} {i['detail']}")


# ---------------------------------------------------------------------------
# Guard helper
# ---------------------------------------------------------------------------

def guard(result: Result, metric: str, condition: bool, reason: str,
          needed: list[str] | None = None) -> bool:
    """Return True when the computation may proceed; else record why not."""
    if not condition:
        result.skip(metric, reason, needed)
        return False
    return True


# ---------------------------------------------------------------------------
# CLI scaffold
# ---------------------------------------------------------------------------

def cli(script_name: str, description: str, run, add_args=None) -> None:
    """Shared argparse scaffold.

    `run(args, warnings) -> Result` does the work. Standard flags:
      --inputs '<json>'      inline tagged JSON
      --inputs-file f.json   tagged JSON file (or .fa.json state file)
      --json                 machine output (recommended for the model)
    """
    parser = argparse.ArgumentParser(prog=script_name, description=description)
    parser.add_argument("--inputs", help="inline JSON object of tagged inputs")
    parser.add_argument("--inputs-file", help="path to JSON file of tagged inputs")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit machine-readable JSON to stdout")
    if add_args:
        add_args(parser)
    args = parser.parse_args()

    warnings: list[str] = []
    try:
        result = run(args, warnings)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 — one honest crash surface
        print(f"[{script_name}] unexpected error: {e}", file=sys.stderr)
        sys.exit(EXIT_UNEXPECTED)

    for w in warnings:
        result.warn(w)
    code = result.finalize()
    result.emit(args.as_json)
    sys.exit(code)


def gather_inputs(args, warnings: list[str]) -> dict[str, Tagged]:
    """Resolve --inputs / --inputs-file into Tagged inputs (may be empty)."""
    if args.inputs and args.inputs_file:
        raise SystemExit("pass either --inputs or --inputs-file, not both")
    src = args.inputs or args.inputs_file
    if not src:
        return {}
    return load_inputs(src, warnings)
