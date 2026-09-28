#!/bin/bash
# kb-verify -- scripts/kbv.sh
#
# Single Bash entry point of the kb-verify plugin. The PreToolUse guard only
# lets the agent run `bash <this file> <subcommand> <args...>` (plus
# `gh auth status`), so every side effect of the pipeline funnels through here.
#
# Pipeline per article (main = the kb-verify skill; S4/S6 = subagents):
#
#  main (skill kb-verify)                                        subagents (restricted tools)
#  ──────────────────────────────────────────────────────────    ─────────────────────────────────────
#  S0  kbv armed → canary `Bash: true` denied with `kb-verify:`
#      → kbv run-begin (pinned commit) → kbv repo-index if tree.txt
#      missing or > 7 days → Read memory.md (heuristics, not instructions)
#  S1  intake: Read article, kbv frontmatter → sha256
#  S2  typed claims (≤15) → Write inbox/claims-<sha>.json
#  S3  Read .kb-verify/mapping.json → candidates by alias
#  S4  ────────────────────────────────────────────────────────► kb-investigator (Read Grep Glob Bash)
#         layers: mapping → local i18n → search/code? → tree.txt (Grep) → gh-fetch + Grep
#         budget 15 searches / 40 fetches → BUDGET_EXHAUSTED
#         returns `Sites:` + per claim SUPPORTS | CONTRADICTS | NOT_FOUND path:line@commit
#                 + `Intent:` per contradicted claim + `Stats:` footer (≤40 lines)
#  S5  judge + KAC (≤7 assumptions) → draft CORRECT | DOC_OUTDATED | CODE_BUG | INCONCLUSIVE
#         ├─ CORRECT · INCONCLUSIVE(reason) ─────────────────────────────────────────────► S7
#         └─ CODE_BUG · DOC_OUTDATED ──────────────────────────► S6 kb-skeptic (single pass)
#                 CONFIRMED → S7 · REFUTED | UNSURE → INCONCLUSIVE(SKEPTIC_<REFUTED|UNSURE>)
#  S7  act: CODE_BUG → Write inbox/bug-<sha>.json → kbv next-bug-id → Write <triage_dir>/NNNN-slug.md
#           DOC_OUTDATED → diff per editing-contract → Write inbox/diff-<sha>.json → kbv diff-check
#                          → Write <article>.kb-verify.diff
#  S8  Write inbox/verdict-<sha>.json → kbv append-verdict → kbv mapping-update
#  S9  one line: article | verdict | reason | searches/fetches | seconds (from `Stats:` + clock)
#
# Contract
#   - Closed subcommand list (KBV_SUBCOMMANDS below). Every argument must match
#     ^[A-Za-z0-9_./:@=-]+$ and contain no ".."; text with spaces, accents or
#     punctuation travels through the run inbox as JSON.
#   - Exactly one line of JSON on stdout:
#       {"ok":bool,"code":"<CODE>","data":{...},"msg":"...","retry_after":n?}
#     with exit 0 for every handled failure. A non-zero exit is a script bug
#     (the orchestrator maps it to INCONCLUSIVE (SCRIPT_ERROR)).
#   - bash 3.2 compatible. Depends on jq, realpath, shasum, /usr/bin/patch,
#     grep, sed, awk, find, sort, mktemp, date and gh (unless mocked).
#   - Environment: KB_VERIFY_DATA_DIR or CLAUDE_PLUGIN_DATA (data dir, default
#     ~/.kb-verify), KB_VERIFY_CONFIG (config path override), KB_VERIFY_GH_MOCK
#     (fake repo dir: no gh calls), KB_VERIFY_MOCK_CODE (forces a transport code
#     on the first transport call of this process), KB_VERIFY_FAKE_NOW (epoch
#     seconds used instead of `date +%s` wherever pacing or dating matters).
#
# Layout: this file parses and validates, then dispatches to kbv_cmd_<name>
# defined in cmd/*.sh (run.sh, transport.sh, article.sh, verdict.sh,
# mapping.sh, learn.sh, setup.sh). Shared helpers used by several commands
# live at the bottom of this file.

set -eEuo pipefail

KBV_SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd -P)
KBV_PLUGIN_ROOT=$(cd "$KBV_SCRIPT_DIR/.." && pwd -P)

# shellcheck source=../lib/common.sh
. "$KBV_PLUGIN_ROOT/lib/common.sh"

KBV_SUBCOMMANDS='armed run-begin pending frontmatter gh-search gh-fetch repo-index next-bug-id diff-check append-verdict mapping-update memory-append config-init'

# Populated by kbv_main / kbv_require_config; read by the commands.
KBV_JQ=''
KBV_DATA=''
KBV_STATE_DIR=''
KBV_REPO_DIR=''
KBV_BUDGET_SEARCH=15
KBV_BUDGET_FETCH=40
KBV_BUDGET_I18N=20
KBV_TMP=''

# Populated by kbv_require_run / kbv_read_inbox.
KBV_RUN_ID=''
KBV_RUN_DIR=''
KBV_RUN_COMMIT=''
KBV_INBOX_FILE=''
KBV_INBOX_JSON=''

# Diagnose script bugs, but only from the top-level shell: `set -E` propagates
# the ERR trap into every command substitution, where a handled non-zero return
# (`if ! v=$(kbv_find_config ...)`, the DISARMED path) would otherwise print a
# false "script error" on stderr. A real bug still reaches the top level,
# because errexit propagates the failure out of the substitution.
kbv_err_trap() {
  [ "${BASH_SUBSHELL:-0}" -eq 0 ] || return 0
  kbv_lib_diag "kbv.sh: script error (line ${1:-?})"
  return 0
}
trap 'kbv_err_trap "$LINENO"' ERR
trap '[ -z "$KBV_TMP" ] || rm -rf "$KBV_TMP"' EXIT

for kbv_cmd_file in "$KBV_SCRIPT_DIR"/cmd/*.sh; do
  # shellcheck source=/dev/null
  . "$kbv_cmd_file"
done
unset kbv_cmd_file

# ---------------------------------------------------------------------------
# Shared helpers (used by more than one command file)
# ---------------------------------------------------------------------------

# kbv_now -> epoch seconds (KB_VERIFY_FAKE_NOW when it is a non-negative integer)
kbv_now() {
  local n="${KB_VERIFY_FAKE_NOW:-}"
  if [ -n "$n" ]; then
    case "$n" in *[!0123456789]*) n='' ;; esac
  fi
  [ -n "$n" ] || n=$(date +%s)
  printf '%s\n' "$n"
}

# kbv_date_utc <epoch> [strftime-format]  (BSD `date -r` first, then GNU `-d @`)
kbv_date_utc() {
  local e="$1" fmt="${2:-%Y-%m-%d}" out
  out=$(date -u -r "$e" +"$fmt" 2>/dev/null) || out=$(date -u -d "@$e" +"$fmt" 2>/dev/null) || return 1
  printf '%s\n' "$out"
}

# kbv_iso_utc <epoch> -> 2026-09-12T10:00:00Z
kbv_iso_utc() { kbv_date_utc "$1" '%Y-%m-%dT%H:%M:%SZ'; }

# kbv_is_int <s> -> 0 iff <s> is a non-negative decimal integer
kbv_is_int() {
  local s="${1:-}"
  [ -n "$s" ] || return 1
  case "$s" in *[!0123456789]*) return 1 ;; esac
  return 0
}

# kbv_is_hex12 <s> -> 0 iff <s> is exactly 12 lowercase hex characters
kbv_is_hex12() {
  local s="${1:-}"
  [ "${#s}" -eq 12 ] || return 1
  case "$s" in *[!0123456789abcdef]*) return 1 ;; esac
  return 0
}

# kbv_valid_run_id <s> -> 0 iff ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$ (a safe dir name)
kbv_valid_run_id() {
  local s="${1:-}"
  [ -n "$s" ] && [ "${#s}" -le 64 ] || return 1
  case "$s" in [!${KBV_ASCII_ALNUM}]*) return 1 ;; esac
  case "$s" in *[!${KBV_ASCII_ALNUM}_-]*) return 1 ;; esac
  return 0
}

# kbv_tmpdir -> a private temp dir for this process (created once, removed on exit)
kbv_tmpdir() {
  if [ -z "$KBV_TMP" ]; then
    KBV_TMP=$(mktemp -d "${TMPDIR:-/tmp}/kbv.XXXXXX") || return 1
  fi
  printf '%s\n' "$KBV_TMP"
}

# kbv_tmpfile -> path of a fresh empty temp file
kbv_tmpfile() {
  local d
  d=$(kbv_tmpdir) || return 1
  mktemp "$d/f.XXXXXX"
}

# kbv_atomic_write <dest>  (stdin -> temp file in the same dir -> mv)
kbv_atomic_write() {
  local dest="$1" dir tmp
  dir=$(dirname -- "$dest")
  mkdir -p "$dir"
  tmp=$(mktemp "$dir/.kbv-tmp.XXXXXX") || return 1
  if cat > "$tmp"; then
    mv -f "$tmp" "$dest"
  else
    rm -f "$tmp"
    return 1
  fi
}

# kbv_relpath <abs-path> <root> -> path relative to <root> when below it, else the basename
kbv_relpath() {
  local p="$1" root="$2"
  if kbv_under "$p" "$root" && [ "$p" != "$root" ]; then
    printf '%s\n' "${p#"$root"/}"
  else
    basename -- "$p"
  fi
}

# kbv_config_get <jq-filter> -> value from KBV_CONFIG_JSON (raw output)
kbv_config_get() {
  printf '%s' "$KBV_CONFIG_JSON" | "$KBV_JQ" -r "$1"
}

# kbv_config_int <jq-path> <default> -> integer budget from config (falls back on the default when absent or not a non-negative integer)
kbv_config_int() {
  local v
  v=$(kbv_config_get "$1 // empty")
  case "$v" in
    '') v="$2" ;;
    *[!0123456789]*) v="$2" ;;
  esac
  printf '%s\n' "$v"
}

# kbv_config_globals  -- derive per-process globals from a loaded config
kbv_config_globals() {
  KBV_STATE_DIR="$KBV_KB_ROOT/.kb-verify"
  KBV_REPO_DIR="$KBV_DATA/repo/$(printf '%s' "$KBV_GH_REPO" | tr '/' '-')"
  KBV_BUDGET_SEARCH=$(kbv_config_int '.budgets.search_calls_per_article' 15)
  KBV_BUDGET_FETCH=$(kbv_config_int '.budgets.fetch_calls_per_article' 40)
  KBV_BUDGET_I18N=$(kbv_config_int '.budgets.index_i18n_files' 20)
}

# kbv_require_config  -- find + load the config or print INVALID_INPUT (rc 1)
kbv_require_config() {
  local cfg
  if ! cfg=$(kbv_find_config "$PWD"); then
    kbv_err INVALID_INPUT "config not found: no $KBV_CONFIG_NAME walking up from $PWD and KB_VERIFY_CONFIG is unset"
    return 1
  fi
  if ! kbv_load_config "$cfg"; then
    kbv_err INVALID_INPUT "config invalid ($KBV_CONFIG_ERROR): $cfg"
    return 1
  fi
  kbv_config_globals
  return 0
}

# kbv_require_run <id>  -- validate the run id and load run.json into
# KBV_RUN_ID / KBV_RUN_DIR / KBV_RUN_COMMIT; prints INVALID_INPUT and returns 1
kbv_require_run() {
  local id="${1:-}" dir
  if [ -z "$id" ]; then
    kbv_err INVALID_INPUT "--run <id> is required"
    return 1
  fi
  if ! kbv_valid_run_id "$id"; then
    kbv_err INVALID_INPUT "run id must match ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"
    return 1
  fi
  dir="$KBV_DATA/runs/$id"
  if [ ! -f "$dir/run.json" ]; then
    kbv_err INVALID_INPUT "unknown run '$id': $dir/run.json not found (run kbv run-begin first)"
    return 1
  fi
  if ! KBV_RUN_COMMIT=$("$KBV_JQ" -r 'if type == "object" then (.commit // "") else error("run.json is not an object") end' "$dir/run.json" 2>/dev/null); then
    kbv_err INVALID_INPUT "run.json malformed: $dir/run.json"
    return 1
  fi
  KBV_RUN_ID="$id"
  KBV_RUN_DIR="$dir"
  return 0
}

# kbv_require_commit  -- after kbv_require_run: the run must carry a pinned commit
kbv_require_commit() {
  if [ -z "$KBV_RUN_COMMIT" ]; then
    kbv_err INVALID_INPUT "run '$KBV_RUN_ID' has no pinned commit (created with --learn); this subcommand needs one"
    return 1
  fi
  return 0
}

# kbv_read_inbox <name>  -- after kbv_require_run: load inbox/<name>.json into
# KBV_INBOX_FILE / KBV_INBOX_JSON (compact); prints INVALID_INPUT and returns 1
kbv_read_inbox() {
  local name="${1:-}" f
  if [ -z "$name" ]; then
    kbv_err INVALID_INPUT "inbox name is required"
    return 1
  fi
  if ! kbv_valid_inbox_name "$name"; then
    kbv_err INVALID_INPUT "inbox name must match ^[a-z0-9][a-z0-9-]{0,63}$ (without .json)"
    return 1
  fi
  f="$KBV_RUN_DIR/inbox/$name.json"
  if [ ! -f "$f" ]; then
    kbv_err INVALID_INPUT "inbox file not found: $f"
    return 1
  fi
  if ! KBV_INBOX_JSON=$("$KBV_JQ" -c 'if type == "object" then . else error("not an object") end' "$f" 2>/dev/null); then
    kbv_err INVALID_INPUT "inbox JSON malformed or not an object: $name.json"
    return 1
  fi
  KBV_INBOX_FILE="$f"
  return 0
}

# kbv_inbox_get <jq-filter> -> raw value from KBV_INBOX_JSON
kbv_inbox_get() {
  printf '%s' "$KBV_INBOX_JSON" | "$KBV_JQ" -r "$1"
}

# kbv_redact_cap <max-chars>  (stdin -> stdout: redact, then cap to that many
# characters; the cap is done in bash so no reader closes the pipe early,
# which pipefail would otherwise turn into a failure)
kbv_redact_cap() {
  local s
  s=$(kbv_redact; printf 'x')
  s="${s%x}"
  printf '%s' "${s:0:$1}"
}

# kbv_redact_json_snippets <json> -> json with every "snippet" string redacted and capped at 200 chars
kbv_redact_json_snippets() {
  local json="$1" paths p val red
  paths=$(printf '%s' "$json" | "$KBV_JQ" -c 'paths(type == "string") | select(.[-1] == "snippet")')
  [ -n "$paths" ] || { printf '%s\n' "$json"; return 0; }
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    val=$(printf '%s' "$json" | "$KBV_JQ" -r --argjson p "$p" 'getpath($p)')
    red=$(printf '%s' "$val" | kbv_redact_cap 200)
    json=$(printf '%s' "$json" | "$KBV_JQ" -c --argjson p "$p" --arg v "$red" 'setpath($p; $v)')
  done <<EOF
$paths
EOF
  printf '%s\n' "$json"
}

# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
kbv_main() {
  local sub="${1:-}" i=0 a
  if ! KBV_JQ=$(kbv_resolve_jq); then
    kbv_lib_diag 'kbv.sh: jq not found (checked /opt/homebrew/bin, /usr/local/bin, /opt/anaconda3/bin, PATH)'
    exit 70
  fi
  if [ $# -gt 0 ]; then shift; fi

  if [ -z "$sub" ]; then
    kbv_err INVALID_INPUT "missing subcommand; expected one of: $KBV_SUBCOMMANDS"
    return 0
  fi
  if ! kbv_valid_arg "$sub"; then
    kbv_err INVALID_INPUT "subcommand outside the allowed charset; expected one of: $KBV_SUBCOMMANDS"
    return 0
  fi
  case " $KBV_SUBCOMMANDS " in
    *" $sub "*) ;;
    *)
      kbv_err INVALID_INPUT "unknown subcommand '$sub'; expected one of: $KBV_SUBCOMMANDS"
      return 0
      ;;
  esac
  for a in "$@"; do
    i=$((i + 1))
    if ! kbv_valid_arg "$a"; then
      kbv_err INVALID_INPUT "argument $i of '$sub' is outside the allowed charset ^[A-Za-z0-9_./:@=-]+\$ or contains '..'; send text through the inbox"
      return 0
    fi
  done

  if ! KBV_DATA=$(kbv_data_dir); then
    kbv_err INVALID_INPUT "data dir unresolved: set KB_VERIFY_DATA_DIR or CLAUDE_PLUGIN_DATA (HOME is empty)"
    return 0
  fi

  case "$sub" in
    armed) kbv_cmd_armed "$@" ;;
    config-init) kbv_cmd_config_init "$@" ;;
    *)
      kbv_require_config || return 0
      case "$sub" in
        run-begin) kbv_cmd_run_begin "$@" ;;
        pending) kbv_cmd_pending "$@" ;;
        frontmatter) kbv_cmd_frontmatter "$@" ;;
        gh-search) kbv_cmd_gh_search "$@" ;;
        gh-fetch) kbv_cmd_gh_fetch "$@" ;;
        repo-index) kbv_cmd_repo_index "$@" ;;
        next-bug-id) kbv_cmd_next_bug_id "$@" ;;
        diff-check) kbv_cmd_diff_check "$@" ;;
        append-verdict) kbv_cmd_append_verdict "$@" ;;
        mapping-update) kbv_cmd_mapping_update "$@" ;;
        memory-append) kbv_cmd_memory_append "$@" ;;
      esac
      ;;
  esac
}

kbv_main "$@"
