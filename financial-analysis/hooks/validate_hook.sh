#!/usr/bin/env bash
# validate_hook.sh — PostToolUse hook (matcher: Write|Edit).
#
# When Claude writes or edits a *.fa.json tagged-inputs state file, validate it
# immediately and feed violations back to Claude (exit 2 + stderr). Any other
# file passes through untouched (exit 0).
#
# Install: merge hooks/settings-snippet.json into ~/.claude/settings.json
# (or use the /update-config skill). This hook is optional hardening — the
# skill's workflow runs `fa.sh validate` regardless.

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

case "$file_path" in
  *.fa.json) ;;
  *) exit 0 ;;
esac

[ -f "$file_path" ] || exit 0

out="$("$SKILL_DIR/scripts/fa.sh" validate "$file_path" 2>&1)"
code=$?

if [ $code -ne 0 ]; then
  {
    echo "financial-analysis: $file_path failed validation — fix before using it in calculations:"
    # Cap relayed output — validator messages are sanitized, but never flood
    # the agent's context regardless.
    printf '%s' "$out" | head -c 4000
    echo
  } >&2
  exit 2
fi
exit 0
