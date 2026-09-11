#!/bin/bash
# kb-verify -- hooks/kb-guard.sh
#
# PreToolUse entry point (see hooks/hooks.json). Thin, jq-free wrapper around
# guard-main.sh: a PreToolUse hook that exits with an unexpected status or
# prints nothing ALLOWS the tool, so every crash and every missing decision
# is converted here into a deny. Stdin (the hook payload) is passed through.
#
# guard-main.sh protocol: exit 0 and exactly one line on stdout, either the
# sentinel "KBV_ALLOW" (allow: this wrapper prints nothing) or the deny JSON
# (printed verbatim). Anything else is a crash.
out=$(bash "$(dirname -- "$0")/guard-main.sh"); rc=$?
if [ "$rc" -eq 0 ]; then
  case "$out" in
    *$'\n'*) ;;                                   # more than one line: crash
    KBV_ALLOW) exit 0 ;;                          # allow: silent
    '{"hookSpecificOutput"'*) printf '%s\n' "$out"; exit 0 ;;   # deny: pass through
  esac
fi
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"kb-verify: guard crashed (rc=%s)"}}\n' "$rc"
exit 0
