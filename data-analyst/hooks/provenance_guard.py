#!/usr/bin/env python3
"""PostToolUse hook (opt-in): numeric-provenance guard for analysis deliverables.

When a Write/Edit touches a findings/report file and adds numeric claims without any
provenance marker (a notebook cell reference, script/csv citation, or source note),
this hook injects a gentle warning back into the session context. It never blocks.

Installed/removed by scripts/install_hook.sh. Reads the hook JSON from stdin.
Fails silent by design: a broken guard must never break the user's session.
"""
import json
import re
import sys

FILE_PATTERN = re.compile(r"(findings[^/]*\.md|report[^/]*\.md|[^/]*_report\.md)$", re.I)
# numbers that look like metric claims: percentages, currency, thousands, decimals
NUMBER = re.compile(r"(\d+(?:\.\d+)?\s?%|[$€]\s?\d|R\$\s?\d|\b\d{1,3}(?:,\d{3})+\b|\b\d+\.\d+\b)")
PROVENANCE = re.compile(r"(cell\s?\d|\.ipynb|\.py\b|\.csv\b|source:|fonte:|\[ASSUMED\]|notebook)", re.I)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool = payload.get("tool_name", "")
    if tool not in ("Write", "Edit"):
        return 0
    tin = payload.get("tool_input", {}) or {}
    path = tin.get("file_path", "") or ""
    if not FILE_PATTERN.search(path):
        return 0
    content = tin.get("content") or tin.get("new_string") or ""
    numbers = NUMBER.findall(content)
    if len(numbers) >= 2 and not PROVENANCE.search(content):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": (
                    f"provenance-guard: {path} gained {len(numbers)} numeric claims with no "
                    "provenance marker (notebook cell, script/csv citation, 'source:'). "
                    "Every reported number needs a traceable computation behind it — add the "
                    "citation or recompute before this reaches the report."
                ),
            }
        }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
