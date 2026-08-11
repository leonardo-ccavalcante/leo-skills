#!/bin/sh
# pre-tool-prod-guard.sh — Claude Code PreToolUse hook (generalized, public version)
#
# Blocks workflow-mutating MCP/Bash calls on protected n8n workflow IDs unless a
# fresh local backup exists. Protects production workflows from agent edits made
# without a restore point.
#
# Configuration (environment, e.g. via your gitignored .env):
#   N8N_PROTECTED_WORKFLOW_IDS   space-separated workflow IDs to guard (required to activate)
#   N8N_BACKUP_DIR               backup directory (default: ./backups)
#   N8N_BACKUP_MAX_AGE_MIN       max backup age in minutes (default: 60)
#
# Wire it in .claude/settings.json:
#   { "hooks": { "PreToolUse": [ { "matcher": "*", "hooks": [
#       { "type": "command", "command": "sh path/to/pre-tool-prod-guard.sh" } ] } ] } }
#
# One-off override: prefix the shell command with N8N_SKIP_PROD_GUARD=1.
# NOTE: backups are full workflow exports — keep the backup dir out of git
# (any secret hardcoded in a node parameter is in the file).

PROTECTED_IDS="${N8N_PROTECTED_WORKFLOW_IDS:-}"
BACKUP_DIR="${N8N_BACKUP_DIR:-./backups}"
MAX_AGE_MIN="${N8N_BACKUP_MAX_AGE_MIN:-60}"

# Not configured → guard inactive.
if [ -z "$PROTECTED_IDS" ]; then
  exit 0
fi

# One-off override.
if [ "${N8N_SKIP_PROD_GUARD:-0}" = "1" ]; then
  exit 0
fi

# Read tool invocation JSON from stdin (Claude Code hook protocol).
INPUT="$(cat)"

# Only act on n8n workflow mutation tools. Cheap string match; the hook protocol
# guarantees JSON but strict parsing is not needed to triage.
case "$INPUT" in
  # Community (czlonkowski n8n-mcp): n8n_update_partial_workflow / n8n_update_workflow / n8n_delete_workflow.
  # Official (n8n built-in MCP):     update_workflow / delete_workflow.
  # (*update_workflow* also matches n8n_update_workflow; *delete_workflow* matches both deletes.
  #  Create ops are not guarded — a new workflow has no prior state to back up.)
  *n8n_update_partial_workflow*|*update_workflow*|*delete_workflow*) ;;
  *) exit 0 ;;
esac

# Find the workflow id referenced in this call.
HIT_ID=""
for id in $PROTECTED_IDS; do
  case "$INPUT" in
    *"$id"*) HIT_ID="$id"; break ;;
  esac
done
if [ -z "$HIT_ID" ]; then
  exit 0
fi

# Look for a backup file `<dir>/<id>-*.json` newer than $MAX_AGE_MIN minutes.
mkdir -p "$BACKUP_DIR" 2>/dev/null
FRESH="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name "${HIT_ID}-*.json" -mmin -"${MAX_AGE_MIN}" 2>/dev/null | head -1)"

if [ -n "$FRESH" ]; then
  exit 0
fi

# No fresh backup → block.
cat >&2 <<EOF
[pre-tool-prod-guard] BLOCKED: mutating protected workflow $HIT_ID without a fresh backup.

Required: a file matching
  ${BACKUP_DIR}/${HIT_ID}-*.json
younger than ${MAX_AGE_MIN} minutes.

Backup command:
  mkdir -p "${BACKUP_DIR}"
  curl -s -H "X-N8N-API-KEY: \$N8N_API_KEY" \\
    "\$N8N_API_URL/api/v1/workflows/${HIT_ID}" \\
    > "${BACKUP_DIR}/${HIT_ID}-\$(date -u +%Y%m%dT%H%M%SZ).json"

To bypass for one call: prefix the command shell with N8N_SKIP_PROD_GUARD=1.

Known gotcha: this guard substring-matches the whole tool input — editing a FILE
whose text contains both a mutation tool name and a protected ID also trips it.
Make the backup (good practice anyway) or use the one-off override.
EOF
exit 2
