#!/bin/bash
# kb-verify -- hooks/guard-main.sh
#
# PreToolUse decision logic. Invoked only through hooks/kb-guard.sh, which
# turns a crash or a missing decision into a deny.
#
# stdout protocol (consumed by the wrapper): exactly one line, either the
# deny JSON printed by kbv_deny or the literal sentinel "KBV_ALLOW". Exit 0
# in both cases; any other exit status is a script bug (=> wrapper denies).
#
# Decision tree (design spec, section "Guard"):
#
#  stdin JSON ──► kb-verify.config.json walking up from cwd? ──no──► allow (silent, no stdout)
#                   │yes (armed)
#                   ├─ jq or realpath missing ∨ config without kb_root|articles_dir|triage_dir
#                   │      ──► DENY "kb-verify: config invalid (<piece>)" for every tool in the matcher
#                   ├─ Read|Grep|Glob ──► inspected field normalized under ~/.ssh, ~/.config/gh,
#                   │      ~/.claude/.credentials.json or ~/.claude/settings*.json ? DENY : allow
#                   ├─ WebFetch|WebSearch|mcp__* ──► DENY
#                   ├─ NotebookEdit|MultiEdit ──► DENY
#                   ├─ Write|Edit ──► normalize (realpath of the existing prefix; ".." in the rest ⇒ DENY)
#                   │      ├─ Write ${CLAUDE_PLUGIN_DATA}/runs/*/inbox/[a-z0-9][a-z0-9-]{0,63}.json ⇒ allow
#                   │      ├─ Write <triage_dir>/NNNN-slug.md ∧ file does not exist ⇒ allow
#                   │      ├─ Write <articles_dir>/**/x.kb-verify.diff ∧ x.md exists beside it ⇒ allow
#                   │      └─ otherwise ⇒ DENY (includes every Edit, .kb-verify/, ~/.claude, .git, config)
#                   └─ Bash ──► metacharacter ; & | < > ( ) { } $ ` \ ~ * ? or newline ⇒ DENY
#                          ├─ "gh auth status" exactly ⇒ allow
#                          ├─ "bash <realpath = ${CLAUDE_PLUGIN_ROOT}/scripts/kbv.sh> <sub ∈ closed list>"
#                          │      ∧ every arg matches ^[A-Za-z0-9_./:@=-]+$ and has no ".." ⇒ allow
#                          └─ otherwise ⇒ DENY (reason names the token)
#    guard crash or no decision emitted ⇒ DENY "guard crashed" (wrapper kb-guard.sh)
#
# Inspected tool_input field per tool: file_path (Write, Edit, MultiEdit),
# notebook_path (NotebookEdit), command (Bash), path (Grep; Read also sends
# file_path, so both are checked), pattern AND path (Glob). Write/Edit/Bash
# without their field => DENY; Grep/Glob without path search from cwd.
#
# Implementation notes
#   - bash 3.2 clean; every external text tool runs under LC_ALL=C.
#   - jq is needed to parse the payload. When it is missing the guard cannot
#     even learn the cwd, so it fails closed with "config invalid (jq)"
#     before the arming check (the only deviation from the diagram order).
#   - Quotes (" and ') are rejected in Bash commands together with the
#     metacharacters: the allowed grammar never needs them, and rejecting
#     them removes any need to re-implement shell word splitting.
#   - The three write branches are Write-only, exactly as the spec writes
#     them: every Edit (and MultiEdit/NotebookEdit) is denied, because the
#     pipeline only ever creates those three files and never revisits them.
#   - A path the guard would have to rewrite to decide on it is denied
#     instead: a file_path or a script path ending in "/" names a directory,
#     so the guard never approves a string the tool will not act on.

set -eEuo pipefail
export LC_ALL=C

GUARD_DIR=$(cd "$(dirname -- "$0")" && pwd -P)
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
[ -n "$PLUGIN_ROOT" ] || PLUGIN_ROOT=$(cd "$GUARD_DIR/.." && pwd -P)

# shellcheck source=../lib/common.sh
. "$GUARD_DIR/../lib/common.sh"

KBV_SUBCOMMANDS='armed run-begin pending frontmatter gh-search gh-fetch repo-index next-bug-id diff-check append-verdict mapping-update memory-append config-init'
KBV_ALLOW_SENTINEL='KBV_ALLOW'

# Globals filled by field_get and normalize_or_deny.
FIELD_PRESENT=0
FIELD_VALUE=''
NORM=''

# ---------------------------------------------------------------- helpers --

# guard_allow: print the allow sentinel for the wrapper and exit 0.
guard_allow() {
  printf '%s\n' "$KBV_ALLOW_SENTINEL"
  kbv_allow
}

# tool_matched <tool_name>: rc 0 when the tool is in the hooks.json matcher.
tool_matched() {
  case "${1:-}" in
    Edit|Write|MultiEdit|NotebookEdit|Bash|Read|Grep|Glob|WebFetch|WebSearch|mcp__*) return 0 ;;
  esac
  return 1
}

# has_control <s>: rc 0 when <s> contains a control byte (0x00-0x1F, 0x7F).
has_control() {
  case "${1:-}" in *[[:cntrl:]]*) return 0 ;; esac
  return 1
}

# jstring <jq-filter>: echo the string produced by <filter> over the payload
# (trailing newlines of the value are lost; use only for tool_name and cwd).
jstring() {
  printf '%s' "$PAYLOAD" | "$JQ" -r "$1 | if type == \"string\" then . else \"\" end"
}

# field_get <name>: read tool_input.<name>. Sets FIELD_PRESENT=1 and
# FIELD_VALUE (verbatim, newlines included) when it is a string; otherwise
# FIELD_PRESENT=0. rc 1 when jq itself fails (malformed payload).
field_get() {
  local name="$1" out
  FIELD_PRESENT=0
  FIELD_VALUE=''
  out=$(printf '%s' "$PAYLOAD" | "$JQ" -j --arg k "$name" \
    '(.tool_input // {}) as $t
     | if ($t | type) == "object" and ($t | has($k)) and (($t[$k] | type) == "string")
       then "1" + $t[$k] else "0" end' && printf x) || return 1
  out=${out%x}
  case "$out" in
    1*) FIELD_PRESENT=1; FIELD_VALUE=${out#1} ;;
  esac
  return 0
}

# normalize_or_deny <path> <cwd> <label>: set NORM to the normalized path, or
# deny with a reason naming why it could not be normalized. Never call it
# inside $(...): kbv_deny must exit the script, not a subshell.
normalize_or_deny() {
  local value="$1" base="$2" label="$3" rc=0
  NORM=''
  if NORM=$(kbv_normalize_path "$value" "$base"); then
    return 0
  else
    rc=$?
  fi
  case "$rc" in
    1) kbv_deny "$TOOL denied: '..' or unresolvable segment in $label '$value'" ;;
    3) kbv_deny "$TOOL denied: dangling symlink or symlink loop in $label '$value'" ;;
    *) kbv_deny "$TOOL denied: cannot normalize $label '$value' (rc=$rc)" ;;
  esac
}

# ------------------------------------------------------- Read | Grep | Glob --

# read_check_path <path> <base> <label>: deny when the normalized path is a
# protected credential location; for the recursive tools (Grep, Glob) also
# deny when the search root CONTAINS one. Returns 0 otherwise.
read_check_path() {
  local norm d
  normalize_or_deny "$1" "$2" "$3"
  norm=$NORM
  for d in "$HOME_REAL/.ssh" "$HOME_REAL/.config/gh" "$HOME_REAL/.claude/.credentials.json"; do
    if kbv_under "$norm" "$d"; then
      kbv_deny "$TOOL denied: $3 '$1' resolves under protected location $d"
    fi
    case "$TOOL" in
      Grep|Glob)
        if kbv_under "$d" "$norm"; then
          kbv_deny "$TOOL denied: $3 '$1' would search $d (protected location)"
        fi
        ;;
    esac
  done
  case "$norm" in
    "$HOME_REAL"/.claude/settings*.json|"$HOME_REAL"/.claude/settings*.json/*)
      kbv_deny "$TOOL denied: $3 '$1' resolves to protected location $norm"
      ;;
  esac
  return 0
}

# read_check_field <name> <base>: rc 0 when the field was present, non-empty
# and checked; rc 1 when absent or empty (caller decides the default).
read_check_field() {
  field_get "$1" || kbv_deny "invalid hook payload (tool_input.$1)"
  if [ "$FIELD_PRESENT" -ne 1 ] || [ -z "$FIELD_VALUE" ]; then
    return 1
  fi
  if has_control "$FIELD_VALUE"; then
    kbv_deny "$TOOL denied: control character in tool_input.$1"
  fi
  read_check_path "$FIELD_VALUE" "$2" "$1"
  return 0
}

decide_read() {
  local base
  case "$TOOL" in
    Read)
      read_check_field file_path "$CWD" || true
      read_check_field path "$CWD" || true
      ;;
    Grep)
      read_check_field path "$CWD" || read_check_path "$CWD" / cwd
      ;;
    Glob)
      # The pattern is relative to tool_input.path when given, else to cwd.
      base="$CWD"
      field_get path || kbv_deny 'invalid hook payload (tool_input.path)'
      if [ "$FIELD_PRESENT" -eq 1 ] && [ -n "$FIELD_VALUE" ]; then
        if has_control "$FIELD_VALUE"; then
          kbv_deny "$TOOL denied: control character in tool_input.path"
        fi
        normalize_or_deny "$FIELD_VALUE" "$CWD" path
        base=$NORM
      fi
      read_check_path "$base" / path
      read_check_field pattern "$base" || true
      ;;
  esac
  guard_allow
}

# ------------------------------------------------------------ Write | Edit --

# write_is_inbox <path>: <data>/runs/<run-id>/inbox/<name>.json
write_is_inbox() {
  local path="$1" data rel run rest file
  data=$(kbv_data_dir) || return 1
  data=$(kbv_normalize_path "$data" /) || return 1
  kbv_under "$path" "$data/runs" || return 1
  rel=${path#"$data/runs/"}
  [ "$rel" != "$path" ] || return 1
  case "$rel" in */inbox/*) ;; *) return 1 ;; esac
  run=${rel%%/*}
  rest=${rel#*/}
  [ "${rest%%/*}" = inbox ] || return 1
  file=${rest#inbox/}
  case "$file" in ''|*/*) return 1 ;; esac
  kbv_valid_arg "$run" || return 1
  kbv_valid_inbox_file "$file"
}

# write_is_new_triage <path>: <triage_dir>/NNNN-slug.md that does not exist.
write_is_new_triage() {
  local path="$1" dir name
  dir=$(dirname -- "$path")
  name=$(basename -- "$path")
  [ "$dir" = "$KBV_TRIAGE_DIR" ] || return 1
  kbv_valid_triage_name "$name" || return 1
  [ ! -e "$path" ] && [ ! -L "$path" ]
}

# write_is_article_diff <path>: <articles_dir>/**/x.kb-verify.diff with x.md beside it.
# The sibling must be named x.md byte for byte: on a case-insensitive volume
# (APFS by default) `[ -f ]` alone is satisfied by X.MD, which would pair the
# diff with an article that does not carry that name.
write_is_article_diff() {
  local path="$1" dir name stem
  kbv_under "$path" "$KBV_ARTICLES_DIR" || return 1
  dir=$(dirname -- "$path")
  name=$(basename -- "$path")
  case "$name" in *.kb-verify.diff) ;; *) return 1 ;; esac
  stem=${name%.kb-verify.diff}
  [ -n "$stem" ] || return 1
  [ -f "$dir/$stem.md" ] || return 1
  kbv_name_exists "$dir" "$stem.md"
}

decide_write() {
  local path
  field_get file_path || kbv_deny 'invalid hook payload (tool_input.file_path)'
  if [ "$FIELD_PRESENT" -ne 1 ] || [ -z "$FIELD_VALUE" ]; then
    kbv_deny "$TOOL denied: missing file_path"
  fi
  if has_control "$FIELD_VALUE"; then
    kbv_deny "$TOOL denied: control character in file_path"
  fi
  # Decide on the string the tool will act on: normalization drops a trailing
  # "/", so "<allowed>.json/" would be approved as "<allowed>.json".
  case "$FIELD_VALUE" in
    */) kbv_deny "$TOOL denied: file_path '$FIELD_VALUE' ends in '/' and names a directory, not a file" ;;
  esac
  normalize_or_deny "$FIELD_VALUE" "$CWD" file_path
  path=$NORM

  # Explicit denies first: plugin state, the config file, anything in .git.
  case "/$path/" in
    */.git/*) kbv_deny "$TOOL denied: '$path' is inside a .git directory" ;;
  esac
  if kbv_under "$path" "$KBV_KB_ROOT/.kb-verify"; then
    kbv_deny "$TOOL denied: '$path' is kb-verify state (.kb-verify/), written only by kbv.sh"
  fi
  if [ "$path" = "$KBV_CONFIG_PATH" ]; then
    kbv_deny "$TOOL denied: the config file '$path' is read-only"
  fi

  # The three allow branches belong to Write only: the pipeline creates each
  # of those files once and never edits them, so every Edit falls through.
  if [ "$TOOL" = Write ]; then
    if write_is_inbox "$path"; then guard_allow; fi
    if write_is_new_triage "$path"; then guard_allow; fi
    if write_is_article_diff "$path"; then guard_allow; fi
  fi
  kbv_deny "$TOOL denied: '$path' is not an allowed target for $TOOL (only Write may create <data>/runs/<run>/inbox/<name>.json, a new $KBV_TRIAGE_DIR/NNNN-slug.md, or $KBV_ARTICLES_DIR/**/x.kb-verify.diff beside x.md)"
}

# -------------------------------------------------------------------- Bash --

# bash_reject_metachars <command>: deny on control characters, shell
# metacharacters and quotes; the reason names the offending token.
bash_reject_metachars() {
  local cmd="$1" ch
  if has_control "$cmd"; then
    kbv_deny 'Bash denied: newline or control character in command'
  fi
  for ch in ';' '&' '|' '<' '>' '(' ')' '{' '}' '$' '`' '\' '~' '*' '?' '"' "'"; do
    case "$cmd" in
      *"$ch"*) kbv_deny "Bash denied: metacharacter '$ch' in command" ;;
    esac
  done
  return 0
}

decide_bash() {
  local cmd script sub expected given arg
  field_get command || kbv_deny 'invalid hook payload (tool_input.command)'
  [ "$FIELD_PRESENT" -eq 1 ] || kbv_deny 'Bash denied: missing command'
  cmd=$FIELD_VALUE
  bash_reject_metachars "$cmd"
  if [ "$cmd" = 'gh auth status' ]; then guard_allow; fi

  # Word-split on spaces only: tabs and newlines are control bytes (rejected
  # above), quotes and globs are rejected too, so no shell parsing is needed.
  local IFS=' '
  set -f
  # shellcheck disable=SC2086
  set -- $cmd
  set +f
  [ "$#" -ge 1 ] || kbv_deny 'Bash denied: empty command'
  # A near miss on the gh allowlist is extra whitespace, not the 'gh' token:
  # say so, otherwise the reason tells the model to stop using a command the
  # same sentence lists as allowed.
  if [ "$1" = gh ] && [ "$*" = 'gh auth status' ]; then
    kbv_deny "Bash denied: 'gh' is allowed only as the exact command 'gh auth status' (this one carries extra whitespace)"
  fi
  [ "$1" = bash ] || kbv_deny "Bash denied: command '$1' is not allowed (only 'gh auth status' and 'bash <plugin>/scripts/kbv.sh <subcommand> [args]')"
  [ "$#" -ge 2 ] || kbv_deny 'Bash denied: missing script path after bash'
  script=$2
  # Same rule as file_path: a trailing "/" names a directory, and realpath
  # would silently collapse it onto the script file.
  case "$script" in
    */) kbv_deny "Bash denied: script path '$script' ends in '/' and names a directory, not the plugin's scripts/kbv.sh" ;;
  esac
  expected=$(kbv_normalize_path "$PLUGIN_ROOT/scripts/kbv.sh" /) || kbv_deny 'Bash denied: cannot resolve the plugin scripts/kbv.sh path'
  given=$(kbv_normalize_path "$script" "$CWD") || kbv_deny "Bash denied: cannot resolve script path '$script'"
  [ "$given" = "$expected" ] || kbv_deny "Bash denied: script '$script' is not the plugin's scripts/kbv.sh"
  [ "$#" -ge 3 ] || kbv_deny 'Bash denied: missing kbv.sh subcommand'
  sub=$3
  case " $KBV_SUBCOMMANDS " in
    *" $sub "*) ;;
    *) kbv_deny "Bash denied: unknown kbv.sh subcommand '$sub'" ;;
  esac
  shift 3
  for arg in "$@"; do
    kbv_valid_arg "$arg" || kbv_deny "Bash denied: argument '$arg' is outside ^[A-Za-z0-9_./:@=-]+\$ or contains '..'"
  done
  guard_allow
}

# -------------------------------------------------------------------- main --

PAYLOAD=$(cat && printf x)
PAYLOAD=${PAYLOAD%x}

# jq is needed to read the payload at all: fail closed when it is missing.
JQ=$(kbv_resolve_jq) || kbv_deny 'config invalid (jq): jq not found; cannot parse the hook payload'

if ! printf '%s' "$PAYLOAD" | "$JQ" -e 'type == "object"' >/dev/null 2>&1; then
  kbv_deny 'invalid hook payload (not a JSON object)'
fi
TOOL=$(jstring '.tool_name')
CWD=$(jstring '.cwd')
[ -n "$CWD" ] || CWD=$PWD

# Tools outside the matcher are never the guard's business.
tool_matched "$TOOL" || guard_allow

# A payload cwd that no longer exists (deleted mid-session) would make arming
# fail OPEN: the walk-up finds no config and the guard disarms. Fall back to the
# hook process's own directory, which is normally still inside the KB, before
# giving up. Denying outright instead would break every session everywhere the
# moment Claude Code sent a cwd this check dislikes, which is the larger risk.
[ -d "$CWD" ] || CWD=$PWD

# Arming: config found walking up from the payload cwd, or KB_VERIFY_CONFIG.
CONFIG=$(kbv_find_config "$CWD") || guard_allow

# Armed. Dependencies and config must be sound, otherwise deny everything.
command -v realpath >/dev/null 2>&1 || kbv_deny 'config invalid (realpath): realpath not found'
kbv_load_config "$CONFIG" || kbv_deny "config invalid (${KBV_CONFIG_ERROR:-unknown}): $CONFIG"
[ -n "${HOME:-}" ] || kbv_deny 'config invalid (HOME): HOME is not set'
HOME_REAL=$(kbv_normalize_path "$HOME" /) || HOME_REAL=$HOME

case "$TOOL" in
  Read|Grep|Glob) decide_read ;;
  WebFetch|WebSearch|mcp__*) kbv_deny "$TOOL denied: network and MCP tools are blocked while kb-verify is armed" ;;
  NotebookEdit|MultiEdit) kbv_deny "$TOOL denied: not allowed while kb-verify is armed (use Write for the allowed targets)" ;;
  Write|Edit) decide_write ;;
  Bash) decide_bash ;;
esac

# Every branch above ends in guard_allow or kbv_deny; reaching this line is a bug.
exit 70
