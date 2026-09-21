#!/bin/bash
# kb-verify -- hooks/kb-session-start.sh
#
# SessionStart hook. Prints one banner line so the operator (and the model)
# can see whether the guard is armed for this session:
#   kb-verify: ARMED (config: <path>, jq: <path>)
#   kb-verify: DISARMED (jq: <path|not found>)
# followed by a WARNING line when the guard is armed but would deny every
# tool (jq or realpath missing, config invalid). Then removes run
# directories older than one day: find <data>/runs -mtime +1.
#
# Never fails the session: every error path exits 0.

set -u
export LC_ALL=C

HERE=$(cd "$(dirname -- "$0")" && pwd -P) || exit 0
# shellcheck source=../lib/common.sh
. "$HERE/../lib/common.sh" || { echo 'kb-verify: cannot load lib/common.sh'; exit 0; }

payload=''
if [ ! -t 0 ]; then
  payload=$(cat 2>/dev/null) || payload=''
fi

jq_path=$(kbv_resolve_jq) || jq_path=''
cwd=''
if [ -n "$jq_path" ] && [ -n "$payload" ]; then
  cwd=$(printf '%s' "$payload" | "$jq_path" -r '.cwd // empty | if type == "string" then . else empty end' 2>/dev/null) || cwd=''
fi
[ -n "$cwd" ] || cwd=$PWD

if cfg=$(kbv_find_config "$cwd"); then
  printf 'kb-verify: ARMED (config: %s, jq: %s)\n' "$cfg" "${jq_path:-not found}"
  if [ -z "$jq_path" ]; then
    echo 'kb-verify: WARNING jq not found; the guard will deny every matched tool'
  elif ! command -v realpath >/dev/null 2>&1; then
    echo 'kb-verify: WARNING realpath not found; the guard will deny every matched tool'
  elif ! kbv_load_config "$cfg"; then
    printf 'kb-verify: WARNING config invalid (%s); the guard will deny every matched tool\n' "${KBV_CONFIG_ERROR:-unknown}"
  fi
else
  printf 'kb-verify: DISARMED (jq: %s)\n' "${jq_path:-not found}"
fi

# Runs older than one day are garbage (the spec keeps them for 24 h only).
data=$(kbv_data_dir) || exit 0
if [ -n "$data" ] && [ -d "$data/runs" ]; then
  find "$data/runs" -mindepth 1 -maxdepth 1 -mtime +1 -exec rm -rf {} + 2>/dev/null || true
fi
exit 0
