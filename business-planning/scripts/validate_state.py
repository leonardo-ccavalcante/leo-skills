"""validate_state — strict validation of a .bp.json tagged-inputs state file.

This is the STRICT counterpart to bp_common.parse_inputs' tolerant runtime
behavior. Where the runtime downgrades an uncited `public` input to
`assumption` with a warning, the validator fails hard (exit 3). The hook and
the pre-delivery workflow step run this so that a plan never ships on
silently-degraded provenance.

Checks:
  - top-level JSON object; inputs under an "inputs" wrapper (or the whole
    object when no wrapper is present)
  - every input is an explicit tagged dict ({"value": ..., "status": ...}) —
    bare scalars are a violation here (the runtime tolerates them)
  - status in user|public|assumption|unknown
  - unknown  => value null; non-unknown => value present
  - public   => source_url AND source_date present
  - assumption => basis present (an assumption without a basis is a guess)
  - confidence, when present, in low|medium|high
  - meta, when present: route/stage/depth values from the closed sets

Usage: validate_state.py <file.bp.json> [--json]
Exit codes: 0 valid · 3 violations found · 1 unexpected error.
"""

from __future__ import annotations

import json
import sys

from bp_common import (
    CONFIDENCES,
    DEPTHS,
    EXIT_UNEXPECTED,
    INPUT_STATUSES,
    ROUTES,
    STAGES,
    Result,
)


def validate_entry(name: str, v: object, res: Result) -> None:
    if not isinstance(v, dict) or "value" not in v:
        res.invariant(
            f"input '{name}' explicitly tagged", False,
            "bare scalar or malformed entry — use "
            '{"value": ..., "status": "user|public|assumption|unknown"}',
        )
        return
    status = v.get("status")
    if status not in INPUT_STATUSES:
        res.invariant(
            f"input '{name}' has a legal status", False,
            f"status '{status}' is not one of {INPUT_STATUSES}",
        )
        return
    value = v.get("value")
    if status == "unknown" and value is not None:
        res.invariant(
            f"input '{name}' unknown => null", False,
            "status 'unknown' requires value null — a number you have should "
            "be tagged user/public/assumption",
        )
    if status != "unknown" and value is None:
        res.invariant(
            f"input '{name}' value present", False,
            f"status '{status}' with null value — tag it unknown instead",
        )
    if status == "public":
        if not v.get("source_url"):
            res.invariant(
                f"input '{name}' public => source_url", False,
                "a public claim without a citation is an assumption wearing "
                "a suit — add source_url or retag as assumption",
            )
        if not v.get("source_date"):
            res.invariant(
                f"input '{name}' public => source_date", False,
                "add source_date (ISO date the source was accessed) — web "
                "data drifts and undated citations cannot be audited",
            )
    if status == "assumption" and not v.get("basis"):
        res.invariant(
            f"input '{name}' assumption => basis", False,
            "state the basis for the assumption so the reader can challenge it",
        )
    conf = v.get("confidence")
    if conf is not None and conf not in CONFIDENCES:
        res.invariant(
            f"input '{name}' confidence legal", False,
            f"confidence '{conf}' is not one of {CONFIDENCES}",
        )


def validate_meta(meta: object, res: Result) -> None:
    if not isinstance(meta, dict):
        res.invariant("meta is an object", False, f"got {type(meta).__name__}")
        return
    closed = {"route": ROUTES, "stage": STAGES, "depth": DEPTHS}
    for key, allowed in closed.items():
        val = meta.get(key)
        if val is not None and val not in allowed:
            res.invariant(
                f"meta.{key} in closed set", False,
                f"'{val}' is not one of {allowed}",
            )


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv[1:]
    if len(args) != 1:
        print("usage: validate_state.py <file.bp.json> [--json]", file=sys.stderr)
        sys.exit(EXIT_UNEXPECTED)

    res = Result(script="validate_state")
    try:
        with open(args[0], "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[validate_state] cannot read {args[0]}: {e}", file=sys.stderr)
        sys.exit(EXIT_UNEXPECTED)

    if not isinstance(raw, dict):
        res.invariant("top level is an object", False,
                      f"got {type(raw).__name__}")
    else:
        inputs = raw.get("inputs") if isinstance(raw.get("inputs"), dict) else (
            None if "inputs" in raw else raw
        )
        if inputs is None:
            res.invariant("inputs is an object", False,
                          "'inputs' key present but not an object")
            inputs = {}
        if "meta" in raw:
            validate_meta(raw["meta"], res)
        checked = 0
        for name, v in inputs.items():
            if name == "meta":
                continue
            validate_entry(name, v, res)
            checked += 1
        res.add("inputs_checked", checked, "count(inputs)", [])
        failed = [i for i in res.invariants if not i["passed"]]
        res.invariant("state file valid", not failed,
                      f"{len(failed)} violation(s)" if failed else "all checks passed")

    code = res.finalize()
    res.emit(as_json)
    sys.exit(code)


if __name__ == "__main__":
    main()
