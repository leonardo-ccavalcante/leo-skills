#!/bin/bash
# tests/hooks/run.sh -- guard matrix for hooks/kb-guard.sh (cases in cases.tsv).
#
# Run:  /bin/bash tests/hooks/run.sh        (bash 3.2 on macOS, bash 5 on CI)
# TAP-style output ("ok N - group/name"), one summary line per case group,
# exit 1 on any failure. Self-contained: temp HOME, a copy of the plugin under
# $HOME/.claude/plugins/kb-verify (so CLAUDE_PLUGIN_ROOT is under ~/.claude),
# KB_VERIFY_DATA_DIR under that HOME, a fixture KB with config, articles,
# triage dir, plugin state, .git and two symlink traps.
#
# Each case builds a PreToolUse payload with jq, pipes it to kb-guard.sh from
# a directory that is NOT the payload cwd, and asserts:
#   allow -> empty stdout, exit 0
#   deny  -> exit 0, exactly one line, valid deny JSON (jq -e), reason starts
#            with "kb-verify:" and contains the case's substring.
# Needs: jq (resolved by lib/common.sh), realpath, sed, tr, find.

HERE=$(cd "$(dirname "$0")" && pwd -P)
SRC=$(cd "$HERE/../.." && pwd -P)
CASES="$HERE/cases.tsv"

unset KB_VERIFY_CONFIG KB_VERIFY_JQ KB_VERIFY_DATA_DIR CLAUDE_PLUGIN_DATA CLAUDE_PLUGIN_ROOT CDPATH
# shellcheck source=../../lib/common.sh
. "$SRC/lib/common.sh" || { echo "Bail out! cannot source $SRC/lib/common.sh"; exit 1; }
JQ=$(kbv_resolve_jq) || { echo "Bail out! jq not found; cannot build payloads"; exit 1; }
command -v realpath >/dev/null 2>&1 || { echo "Bail out! realpath not found"; exit 1; }

T=$(mktemp -d "${TMPDIR:-/tmp}/kbv-hooks-test.XXXXXX") || { echo "Bail out! mktemp failed"; exit 1; }
trap 'rm -rf "$T"' EXIT
TR=$(realpath "$T")

# ---------------------------------------------------------------- fixture --
HOME="$T/home"; export HOME
PLUGIN="$HOME/.claude/plugins/kb-verify"
DATA="$HOME/.claude/plugins/kb-verify-data"
KB="$T/kb"

mkdir -p "$PLUGIN" "$DATA/runs/r1/inbox" "$DATA/runs/r1/cache" "$T/elsewhere" "$T/nokb" "$T/bak" "$T/outside"
cp -R "$SRC/hooks" "$SRC/lib" "$PLUGIN/"
if [ -f "$SRC/scripts/kbv.sh" ]; then
  cp -R "$SRC/scripts" "$PLUGIN/"
else
  mkdir -p "$PLUGIN/scripts"
  printf '#!/bin/bash\n# test stub; the real kbv.sh is built separately\nexit 0\n' > "$PLUGIN/scripts/kbv.sh"
fi
mkdir -p "$PLUGIN/skills/kb-verify/references"
: > "$PLUGIN/skills/kb-verify/references/editing-contract.md"
cp "$PLUGIN/lib/common.sh" "$T/bak/common.sh"
cp "$PLUGIN/hooks/guard-main.sh" "$T/bak/guard-main.sh"
: > "$DATA/runs/r1/cache/x.ts"

# Protected and allowed locations under the temp HOME.
mkdir -p "$HOME/.ssh" "$HOME/.config/gh" "$HOME/.claude/projects/p" "$HOME/.claude/plans"
: > "$HOME/.ssh/id_rsa"; : > "$HOME/.ssh/known_hosts"; : > "$HOME/.config/gh/hosts.yml"
: > "$HOME/.claude/.credentials.json"; : > "$HOME/.claude/settings.json"; : > "$HOME/.claude/settings.local.json"
: > "$HOME/.claude/projects/p/x.jsonl"; : > "$HOME/.claude/plans/x.md"

# Fixture KB: config with absolute (physical) kb_root, like fixture/setup.sh.
mkdir -p "$KB/articles/billing" "$KB/articles/billing/deep" "$KB/kb-verify/triage/bugs" "$KB/.kb-verify" "$KB/.git/hooks"
"$JQ" -n --arg root "$TR/kb" '{version: 1, kb_root: $root, articles_dir: "articles",
  triage_dir: "kb-verify/triage/bugs", gh: {repo: "org/monorepo"},
  budgets: {search_calls_per_article: 15, fetch_calls_per_article: 40, index_i18n_files: 20},
  integration: {article_glob: "articles/**/*.md", locales: ["en", "pt-BR"],
    frontmatter_map: {title: "titulo", tags: "etiquetas", topic: "politica", status: "estado"},
    verify_when: {status_in: ["draft", "review"]},
    triage_labels: ["needs-triage", "needs-info", "ready-for-agent", "ready-for-human", "wontfix"]}}' \
  > "$KB/kb-verify.config.json"
printf -- '---\ntitulo: Cancelar assinatura\n---\n# Cancelar assinatura\n' > "$KB/articles/billing/cancelar-assinatura.md"
: > "$KB/articles/billing/deep/nested.md"
: > "$KB/articles/billing/evil.md"
: > "$KB/rootnote.md"                       # x.md beside a diff OUTSIDE articles_dir
: > "$KB/kb-verify/triage/bugs/0001-existing.md"
: > "$KB/kb-verify/triage/bugs/feedback.md"
printf '{"version":1,"topics":{}}\n' > "$KB/.kb-verify/mapping.json"
: > "$T/outside/x.md"
ln -s "$T/outside" "$KB/articles/link"                                   # symlink trap: dir outside the KB
ln -s "$HOME/.claude/evil.json" "$KB/articles/billing/evil.kb-verify.diff"  # symlink trap: dangling, points at ~/.claude

# Invalid configs, each in its own directory (used as payload cwd).
mkdir -p "$T/badjson" "$T/notriage" "$T/nokbroot"
printf '{not json' > "$T/badjson/kb-verify.config.json"
"$JQ" -n --arg root "$TR/kb" '{version: 1, kb_root: $root, articles_dir: "articles", gh: {repo: "org/monorepo"}}' > "$T/notriage/kb-verify.config.json"
"$JQ" -n '{version: 1, kb_root: "/nonexistent/kbv-root", articles_dir: "articles", triage_dir: "t", gh: {repo: "org/monorepo"}}' > "$T/nokbroot/kb-verify.config.json"

# fakebin: every tool the guard needs except realpath (NOREALPATH cases).
mkdir -p "$T/fakebin"
for c in bash sh sed tr cut cat dirname basename grep awk sort find mktemp date shasum head tail wc env rm mkdir ls cp mv touch chmod ln readlink id uname printf test expr true false sleep '['; do
  p=$(command -v "$c" 2>/dev/null) || continue
  case "$p" in /*) ln -s "$p" "$T/fakebin/$c" 2>/dev/null ;; esac
done
ln -s "$JQ" "$T/fakebin/jq"

A65=''
i=0; while [ "$i" -lt 65 ]; do A65="${A65}a"; i=$((i + 1)); done

# ---------------------------------------------------------------- harness --
N=0
FAILS=0
RESULTS="$T/results.tsv"
: > "$RESULTS"

pass() { N=$((N + 1)); printf 'ok %d - %s/%s\n' "$N" "$1" "$2"; printf '%s\tok\n' "$1" >> "$RESULTS"; }
fail() {
  N=$((N + 1)); FAILS=$((FAILS + 1))
  printf 'not ok %d - %s/%s\n' "$N" "$1" "$2"
  printf '#   %s\n' "$3"
  printf '%s\tfail\n' "$1" >> "$RESULTS"
}

# expand <s>: substitute placeholders; prints the value followed by "x" so
# callers can keep trailing newlines: v=$(expand "$s"); v=${v%x}
expand() {
  local s="$1"
  s=${s//@HOME@/$HOME}
  s=${s//@KB@/$KB}
  s=${s//@PLUGIN@/$PLUGIN}
  s=${s//@DATA@/$DATA}
  s=${s//@TMP@/$T}
  s=${s//@A65@/$A65}
  s=${s//@NL@/$'\n'}
  s=${s//@TAB@/$'\t'}
  [ "$s" != '@EMPTY@' ] || s=''
  printf '%sx' "$s"
}

lower() { printf '%s' "$1" | LC_ALL=C tr '[:upper:]' '[:lower:]'; }

# run_guard <stdin-text> <env assignments...>: sets OUT and RC.
run_guard() {
  local input="$1"
  shift
  OUT=$(cd "$T/elsewhere" && printf '%s' "$input" | env "$@" bash "$PLUGIN/hooks/kb-guard.sh" 2>"$T/stderr")
  RC=$?
}

# assert_allow / assert_deny <group> <name> <reason-substring>
assert_allow() {
  if [ "$RC" -eq 0 ] && [ -z "$OUT" ]; then pass "$1" "$2"; else fail "$1" "$2" "expected allow (rc 0, no stdout); got rc=$RC stdout=[$OUT]"; fi
}
assert_deny() {
  local sub
  sub=$(lower "$3")
  [ "$sub" != '-' ] || sub=''
  if [ "$RC" -ne 0 ]; then fail "$1" "$2" "expected deny with rc 0; got rc=$RC stdout=[$OUT]"; return; fi
  if [ -z "$OUT" ]; then fail "$1" "$2" "expected deny JSON; got empty stdout (allow) stderr=[$(head -c 300 "$T/stderr")]"; return; fi
  case "$OUT" in *$'\n'*) fail "$1" "$2" "deny output has more than one line: [$OUT]"; return ;; esac
  if printf '%s' "$OUT" | "$JQ" -e --arg sub "$sub" '
      (.hookSpecificOutput.hookEventName == "PreToolUse")
      and (.hookSpecificOutput.permissionDecision == "deny")
      and (.hookSpecificOutput.permissionDecisionReason | type == "string")
      and (.hookSpecificOutput.permissionDecisionReason | startswith("kb-verify:"))
      and ($sub == "" or (.hookSpecificOutput.permissionDecisionReason | ascii_downcase | contains($sub)))' >/dev/null 2>&1; then
    pass "$1" "$2"
  else
    fail "$1" "$2" "deny JSON invalid or reason lacks [$3]: $OUT"
  fi
}

# ------------------------------------------------------------ the matrix --
echo "# guard matrix from $CASES"
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in ''|'#'*) continue ;; esac
  IFS=$'\t' read -r group name tool f1 v1 f2 v2 cwd envspec expect reason extra <<< "$line"
  if [ -z "$reason" ] || [ -n "$extra" ]; then
    fail "${group:-?}" "${name:-?}" "malformed case row (need 11 tab-separated columns): $line"
    continue
  fi
  v1=$(expand "$v1"); v1=${v1%x}
  v2=$(expand "$v2"); v2=${v2%x}
  cwd=$(expand "$cwd"); cwd=${cwd%x}

  # Environment for this case (never inherits CLAUDE_PLUGIN_ROOT unless set here).
  envargs=(HOME="$HOME" KB_VERIFY_DATA_DIR="$DATA" PATH="$PATH")
  crash=0; nodecision=0; use_raw=0; raw=''; set_root=1
  oldifs=$IFS; IFS=','; set -- $envspec; IFS=$oldifs
  for flag in "$@"; do
    case "$flag" in
      -|'') ;;
      JQMISSING) envargs+=(KB_VERIFY_JQ=/nonexistent/jq PATH=/usr/bin:/bin) ;;
      NOREALPATH) envargs+=(PATH="$T/fakebin") ;;
      NOPLUGINROOT) set_root=0 ;;
      CRASH) crash=1 ;;
      NODECISION) nodecision=1 ;;
      ENVCFG=*) p=$(expand "${flag#ENVCFG=}"); envargs+=(KB_VERIFY_CONFIG="${p%x}") ;;
      RAWSTDIN=*) use_raw=1; raw=$(expand "${flag#RAWSTDIN=}"); raw=${raw%x} ;;
      *) fail "$group" "$name" "unknown env flag: $flag"; continue 2 ;;
    esac
  done
  [ "$set_root" -eq 0 ] || envargs+=(CLAUDE_PLUGIN_ROOT="$PLUGIN")

  if [ "$use_raw" -eq 1 ]; then
    input=$raw
  else
    input=$("$JQ" -c -n --arg tool "$tool" --arg cwd "$cwd" --arg f1 "$f1" --arg v1 "$v1" --arg f2 "$f2" --arg v2 "$v2" '
      {session_id: "test-session", transcript_path: "/dev/null", cwd: $cwd,
       hook_event_name: "PreToolUse", tool_name: $tool,
       tool_input: ({} | (if $f1 != "-" then .[$f1] = $v1 else . end)
                       | (if $f2 != "-" then .[$f2] = $v2 else . end))}')
  fi

  [ "$crash" -eq 0 ] || printf '\nfi\n' >> "$PLUGIN/lib/common.sh"
  [ "$nodecision" -eq 0 ] || printf '#!/bin/bash\nexit 0\n' > "$PLUGIN/hooks/guard-main.sh"
  run_guard "$input" "${envargs[@]}"
  [ "$crash" -eq 0 ] || cp "$T/bak/common.sh" "$PLUGIN/lib/common.sh"
  [ "$nodecision" -eq 0 ] || cp "$T/bak/guard-main.sh" "$PLUGIN/hooks/guard-main.sh"

  case "$expect" in
    allow) assert_allow "$group" "$name" ;;
    deny) assert_deny "$group" "$name" "$reason" ;;
    *) fail "$group" "$name" "unknown expectation: $expect" ;;
  esac
done < "$CASES"

# --------------------------------------------------- SessionStart (arming) --
echo "# kb-session-start.sh"
session_start() {
  local cwd="$1"
  printf '{"session_id":"t","cwd":"%s","hook_event_name":"SessionStart","source":"startup"}' "$cwd" \
    | env HOME="$HOME" KB_VERIFY_DATA_DIR="$DATA" CLAUDE_PLUGIN_ROOT="$PLUGIN" bash "$PLUGIN/hooks/kb-session-start.sh" 2>/dev/null
}
mkdir -p "$DATA/runs/old-run/inbox"
touch -t 202001010000 "$DATA/runs/old-run"
out=$(session_start "$KB")
case "$out" in
  "kb-verify: ARMED (config: $TR/kb/kb-verify.config.json, jq: /"*) pass arming session-start-armed ;;
  *) fail arming session-start-armed "unexpected banner: [$out]" ;;
esac
if [ ! -e "$DATA/runs/old-run" ] && [ -d "$DATA/runs/r1" ]; then pass arming session-start-cleanup; else fail arming session-start-cleanup "old-run not removed or r1 removed"; fi
out=$(session_start "$T/nokb")
case "$out" in
  "kb-verify: DISARMED (jq: /"*) pass arming session-start-disarmed ;;
  *) fail arming session-start-disarmed "unexpected banner: [$out]" ;;
esac
out=$(session_start "$T/badjson")
case "$out" in
  "kb-verify: ARMED ("*"WARNING config invalid (json)"*) pass arming session-start-warns-on-bad-config ;;
  *) fail arming session-start-warns-on-bad-config "unexpected banner: [$out]" ;;
esac

# ---------------------------------------------------------------- summary --
echo "# summary"
tab=$'\t'
for g in writes bash-allow bash-deny read-net arming; do
  total=$(grep -c "^$g$tab" "$RESULTS" || true)
  okc=$(grep -c "^$g${tab}ok\$" "$RESULTS" || true)
  printf '# %s: %s/%s passed\n' "$g" "${okc:-0}" "${total:-0}"
done
printf '1..%d\n' "$N"
if [ "$FAILS" -ne 0 ]; then
  printf '# FAILED %d of %d\n' "$FAILS" "$N"
  exit 1
fi
printf '# all %d passed\n' "$N"
exit 0
