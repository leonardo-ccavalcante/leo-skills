#!/usr/bin/env bash
# validate_hook.sh — PostToolUse hook (matcher: Write|Edit).
#
# When Claude writes or edits a *.bp.json tagged-inputs state file, validate it
# immediately (`bp.sh validate`) and feed violations back to Claude (exit 2 +
# stderr). When Claude writes or edits a Markdown artifact inside a bp_<slug>/
# workspace, lint it (`bp.sh lint`) the same way. Any other file passes through
# untouched (exit 0).
#
# Install: merge hooks/settings-snippet.json into ~/.claude/settings.json
# (or use the /update-config skill). This hook is optional hardening — the
# skill's workflow runs `bp.sh validate` and `bp.sh lint` regardless.

set -uo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

payload="$(cat)"

file_path="$(printf '%s' "$payload" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
')"

# Decide which check applies. The *.bp.json case must come first: a state file
# inside a bp_<slug>/ workspace matches both patterns and gets validate, not
# lint. In a `case` pattern, `*` also matches `/`, so `*/bp_*/*.md` covers
# arbitrarily nested Markdown files under a bp_<slug>/ directory.
check=""
case "$file_path" in
  *.bp.json)                 check="validate" ;;
  bp_*/*.md | */bp_*/*.md)   check="lint" ;;
  *) exit 0 ;;
esac

[ -f "$file_path" ] || exit 0

out="$("$SKILL_DIR/scripts/bp.sh" "$check" "$file_path" 2>&1)"
code=$?

if [ $code -ne 0 ]; then
  {
    if [ "$check" = "validate" ]; then
      echo "business-planning: $file_path failed validation — fix before using it in calculations:"
    else
      echo "business-planning: $file_path failed lint — fix before delivering it:"
    fi
    # Cap relayed output — validator/linter messages are sanitized, but never
    # flood the agent's context regardless.
    printf '%s' "$out" | head -c 4000
    echo
  } >&2
  exit 2
fi
exit 0
