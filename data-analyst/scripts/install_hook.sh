#!/usr/bin/env bash
# Installs (or removes) the opt-in provenance-guard PostToolUse hook in
# ~/.claude/settings.json. Asks for confirmation and backs up settings first,
# because this file affects every Claude Code session on this machine.
#
# Usage:
#   bash install_hook.sh              # install (interactive confirm)
#   bash install_hook.sh --yes        # install without prompt
#   bash install_hook.sh --uninstall  # remove the hook
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_PATH="$(cd "$SCRIPT_DIR/../hooks" && pwd)/provenance_guard.py"
SETTINGS="$HOME/.claude/settings.json"
MODE="install"
CONFIRM="ask"

for arg in "$@"; do
  case "$arg" in
    --uninstall) MODE="uninstall" ;;
    --yes|-y) CONFIRM="yes" ;;
  esac
done

if [ "$MODE" = "install" ] && [ "$CONFIRM" = "ask" ]; then
  echo "This adds a PostToolUse hook to $SETTINGS (affects all Claude Code sessions):"
  echo "  on Write/Edit of findings/report .md files, warn when numeric claims lack provenance markers."
  printf "Proceed? [y/N] "
  read -r answer
  case "$answer" in y|Y|yes|YES) ;; *) echo "aborted."; exit 1 ;; esac
fi

mkdir -p "$HOME/.claude"
[ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak.$(date +%Y%m%d%H%M%S)"

HOOK_PATH="$HOOK_PATH" SETTINGS="$SETTINGS" MODE="$MODE" python3 <<'EOF'
import json, os, shlex

settings_path = os.environ["SETTINGS"]
# shlex.quote: the path lands in a persisted shell command — quotes/metachars in it
# must never break out of the argument
hook_cmd = f"python3 {shlex.quote(os.environ['HOOK_PATH'])}"
mode = os.environ["MODE"]

settings = {}
if os.path.exists(settings_path):
    with open(settings_path) as fh:
        content = fh.read().strip()
        settings = json.loads(content) if content else {}

hooks = settings.setdefault("hooks", {})
post = hooks.setdefault("PostToolUse", [])

# drop any existing provenance_guard entries (idempotent install, and uninstall)
for entry in post:
    entry["hooks"] = [h for h in entry.get("hooks", []) if "provenance_guard.py" not in h.get("command", "")]
post[:] = [e for e in post if e.get("hooks")]

if mode == "install":
    post.append({"matcher": "Write|Edit", "hooks": [{"type": "command", "command": hook_cmd}]})
    print(f"installed: PostToolUse Write|Edit -> {hook_cmd}")
else:
    print("uninstalled: provenance_guard hook removed")

if not post:
    hooks.pop("PostToolUse", None)
if not hooks:
    settings.pop("hooks", None)

with open(settings_path, "w") as fh:
    json.dump(settings, fh, indent=2)
    fh.write("\n")
EOF

echo "done. Restart or start a new Claude Code session for the change to take effect."
