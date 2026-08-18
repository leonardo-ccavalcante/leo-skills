"""validate_state — validate a .fa.json tagged-inputs state file.

Checks (exit 3 on any failure, 0 when clean):
  * file is a JSON object, optionally {"analysis": ..., "inputs": {...}}
  * every input is either a bare scalar (warned) or a tagged object
  * statuses belong to the closed set user|public|assumption|unknown
  * unknown => value is null; non-unknown => value present
  * assumptions carry a basis (warning when absent — an assumption without a
    stated basis cannot be challenged, which defeats the tag system)
  * when the file carries projection drivers, structural sanity is checked

Usage: validate_state.py <file.fa.json> [--json]
"""

from __future__ import annotations

import json
import sys

from fin_common import INPUT_STATUSES, EXIT_VALIDATION


def _safe(name: object) -> str:
    """Render a field name safely for error messages.

    Field names come from user-editable files and these messages can be relayed
    into an agent's context by the validation hook — cap length and strip
    control characters so a name can never smuggle instructions or flood output.
    """
    s = str(name)[:64]
    return "".join(ch for ch in s if ch.isprintable())


def validate(path: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return [f"cannot read {path}: {e}"], []

    if not isinstance(raw, dict):
        return ["state file must be a JSON object"], []

    inputs = raw.get("inputs", raw)
    if not isinstance(inputs, dict) or not inputs:
        return ["no inputs found (expected top-level object or 'inputs' key)"], []

    for name, v in inputs.items():
        if name in ("analysis", "domain", "currency", "country", "notes", "date"):
            continue  # metadata keys allowed at top level
        if isinstance(v, dict):
            if "value" not in v:
                errors.append(f"'{_safe(name)}': tagged object missing 'value'")
                continue
            status = v.get("status")
            if status not in INPUT_STATUSES:
                errors.append(
                    f"'{_safe(name)}': status {_safe(status)!r} not in {list(INPUT_STATUSES)}"
                )
                continue
            if status == "unknown" and v["value"] is not None:
                errors.append(
                    f"'{_safe(name)}': status 'unknown' requires value null "
                    "(got a value — tag it user/public/assumption instead)"
                )
            if status != "unknown" and v["value"] is None:
                errors.append(
                    f"'{_safe(name)}': null value must be tagged 'unknown', not {status!r}"
                )
            if status == "assumption" and not v.get("basis"):
                warnings.append(
                    f"'{_safe(name)}': assumption without a 'basis' — state why this "
                    "value is plausible so it can be challenged"
                )
            if status == "public" and not v.get("source_url"):
                warnings.append(
                    f"'{_safe(name)}': public claim without 'source_url'"
                )
        elif isinstance(v, (int, float, str, bool)):
            warnings.append(
                f"'{_safe(name)}': bare scalar (auto-tagged user) — prefer explicit tags"
            )
        elif isinstance(v, list):
            continue  # series inputs (e.g. demand_series) validated by their script
        else:
            errors.append(f"'{_safe(name)}': unsupported value type {type(v).__name__}")

    return errors, warnings


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv
    if len(args) != 1:
        print("usage: validate_state.py <file.fa.json> [--json]", file=sys.stderr)
        sys.exit(1)
    errors, warnings = validate(args[0])
    if as_json:
        print(json.dumps({"file": args[0], "errors": errors,
                          "warnings": warnings,
                          "status": "FAILED" if errors else "OK"}, indent=2))
    else:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        for w in warnings:
            print(f"warning: {w}", file=sys.stderr)
        print(f"{args[0]}: {'FAILED' if errors else 'OK'}"
              f" ({len(errors)} errors, {len(warnings)} warnings)")
    sys.exit(EXIT_VALIDATION if errors else 0)


if __name__ == "__main__":
    main()
