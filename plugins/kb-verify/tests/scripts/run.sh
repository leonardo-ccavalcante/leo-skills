#!/bin/bash
# tests/scripts/run.sh -- kbv.sh under KB_VERIFY_GH_MOCK (no gh, no network).
#
# Run:  /bin/bash tests/scripts/run.sh        (bash 3.2 on macOS, bash 5 on CI)
# TAP-style output ("ok N - ..." / "not ok N - ..."); exit 1 on any failure.
# Self-contained: builds a temp KB and a temp fake repo, redirects HOME and the
# data dir into a temp directory, and removes everything on exit.
# Needs: jq (resolved by lib/common.sh), realpath, shasum, /usr/bin/patch.

set -u

HERE=$(cd "$(dirname "$0")" && pwd -P)
PLUGIN_ROOT=$(cd "$HERE/../.." && pwd -P)
KBV="$PLUGIN_ROOT/scripts/kbv.sh"
GOLDEN="$PLUGIN_ROOT/tests/golden/frontmatter"

unset KB_VERIFY_CONFIG KB_VERIFY_JQ KB_VERIFY_DATA_DIR CLAUDE_PLUGIN_DATA KB_VERIFY_GH_MOCK KB_VERIFY_MOCK_CODE KB_VERIFY_FAKE_NOW CDPATH
T=$(mktemp -d "${TMPDIR:-/tmp}/kbv-scripts-test.XXXXXX") || { echo "mktemp failed"; exit 1; }
trap 'rm -rf "$T"' EXIT
T=$(realpath "$T")
HOME="$T/home"; export HOME; mkdir -p "$HOME"
DATA="$T/data"; export KB_VERIFY_DATA_DIR="$DATA"

# shellcheck source=../../lib/common.sh
. "$PLUGIN_ROOT/lib/common.sh" || { echo "cannot source lib/common.sh"; exit 1; }
JQ=$(kbv_resolve_jq) || { echo "Bail out! jq not found"; exit 1; }

# ---------------------------------------------------------------- harness --
N=0
FAILS=0
pass() { N=$((N + 1)); printf 'ok %d - %s\n' "$N" "$1"; }
fail() {
  N=$((N + 1)); FAILS=$((FAILS + 1))
  printf 'not ok %d - %s\n' "$N" "$1"
  [ -z "${2:-}" ] || printf '#   %s\n' "$2"
  return 0
}
eq() { if [ "$2" = "$3" ]; then pass "$1"; else fail "$1" "expected [$2] got [$3]"; fi; }
is_true() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then pass "$d"; else fail "$d" "expected success"; fi; }
is_false() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then fail "$d" "expected failure"; else pass "$d"; fi; }
jqcheck() { printf '%s' "$1" | "$JQ" -e "$2" >/dev/null 2>&1; }
lines_of() { if [ -f "$1" ]; then wc -l < "$1" | tr -d ' '; else printf '0'; fi; }
sha_of() { shasum -a 256 < "$1" | cut -d' ' -f1; }

OUT=''; RC=0; ERR=''
# kbv <args...>  -> runs kbv.sh, captures OUT/RC/ERR.
# Per-call environment goes through prefix assignments on the caller, e.g.
#   KBV_ENV='KB_VERIFY_MOCK_CODE=RATE_LIMITED' code_cmd ...   (env args, "-u VAR" unsets)
#   KBV_CWD="$T/empty" kbv armed                              (working directory)
# No `( ... )` groups: a subshell would lose the pass/fail counters.
KBV_ENV=''; KBV_CWD=''
kbv() {
  # shellcheck disable=SC2086
  OUT=$(cd "${KBV_CWD:-$PWD}" && env $KBV_ENV /bin/bash "$KBV" "$@" 2>"$T/stderr"); RC=$?; ERR=$(cat "$T/stderr")
}
# env_ok <desc> -> rc 0, exactly one line, valid envelope (silent on success)
env_ok() {
  local d="$1" n
  n=$(printf '%s\n' "$OUT" | wc -l | tr -d ' ')
  if [ "$RC" -ne 0 ]; then fail "$d" "rc=$RC stderr=[$ERR] out=[$OUT]"; return 1; fi
  if [ "$n" -ne 1 ]; then fail "$d" "expected exactly 1 line, got $n: [$OUT]"; return 1; fi
  if ! jqcheck "$OUT" 'type == "object" and (.ok | type) == "boolean" and (.code | type) == "string" and (.data | type) == "object" and (.msg | type) == "string"'; then
    fail "$d" "malformed envelope: [$OUT]"; return 1
  fi
  return 0
}
# ok_cmd <desc> <args...>   -> expects ok:true/code:OK
ok_cmd() { local d="$1"; shift; kbv "$@"; env_ok "$d" || return 1; if jqcheck "$OUT" '.ok == true and .code == "OK"'; then pass "$d"; else fail "$d" "got $OUT"; return 1; fi; }
# code_cmd <desc> <CODE> <args...> -> expects ok:false with that code
code_cmd() {
  local d="$1" want="$2"; shift 2; kbv "$@"; env_ok "$d" || return 1
  if printf '%s' "$OUT" | "$JQ" -e --arg c "$want" '.ok == false and .code == $c' >/dev/null 2>&1; then pass "$d"; else fail "$d" "expected $want got $OUT"; return 1; fi
}
f() { printf '%s' "$OUT" | "$JQ" -r "$1"; }          # raw field of the last envelope
fj() { printf '%s' "$OUT" | "$JQ" -c "$1"; }         # json field of the last envelope
msg_has() { case "$(f .msg)" in *"$1"*) return 0 ;; *) return 1 ;; esac; }
# inbox <run> <name> <json-text>
inbox() { mkdir -p "$DATA/runs/$1/inbox"; printf '%s' "$3" > "$DATA/runs/$1/inbox/$2.json"; }

# ------------------------------------------------------------ fake repo --
REPO="$T/repo"
mkdir -p "$REPO/apps/billing/src" "$REPO/apps/billing/tests" "$REPO/apps/web/locales" "$REPO/apps/web/i18n" \
  "$REPO/apps/web/messages" "$REPO/.github/workflows" "$REPO/node_modules/x" "$REPO/vendor" "$REPO/dist" "$REPO/docs"
printf 'export const REFUND_WINDOW_DAYS = 7;\nexport function cancelSubscription(id: string) {\n  return { status: "canceled", refundWindow: REFUND_WINDOW_DAYS };\n}\n' > "$REPO/apps/billing/src/cancel.ts"
printf 'export const ERR_REFUND_WINDOW = "refund_window_expired";\nexport const REFUND_WINDOW_DAYS_LABEL = "days";\n' > "$REPO/apps/billing/src/constants.ts"
printf 'test("refund window is 10 days", () => { expect(cancelSubscription("x").refundWindow).toBe(10); });\n' > "$REPO/apps/billing/tests/cancel.test.ts"
printf '{"cancel_subscription": "Cancel subscription"}\n' > "$REPO/apps/web/locales/en.json"
printf '{"cancel_subscription": "Cancelar assinatura"}\n' > "$REPO/apps/web/locales/pt-BR.json"
printf '{"cancel_subscription": "Cancelar suscripción"}\n' > "$REPO/apps/web/locales/es.json"
printf 'Locale files live here.\n' > "$REPO/apps/web/locales/README.md"
printf '{"common": {"save": "Save"}}\n' > "$REPO/apps/web/i18n/en.common.json"
printf '{"greeting": "Olá"}\n' > "$REPO/apps/web/messages/pt-BR.messages.json"
printf 'name: ci\non: push\n' > "$REPO/.github/workflows/ci.yml"
printf 'module.exports = 1; // cancelSubscription in a dependency\n' > "$REPO/node_modules/x/index.js"
printf '// vendored\n' > "$REPO/vendor/lib.js"
printf '// built cancelSubscription\n' > "$REPO/dist/bundle.js"
printf '# Guide\n\nCall cancelSubscription from the billing page.\n' > "$REPO/docs/guide.md"
export KB_VERIFY_GH_MOCK="$REPO"

# ------------------------------------------------------------------- KB --
KB="$T/kb"
mkdir -p "$KB/articles/billing" "$KB/drafts"
ART="$KB/articles/billing/cancelar-assinatura.md"
cp "$GOLDEN/mapped-basic.md" "$ART"
printf '# Outro artigo\n\nSem frontmatter. Se falhar, tente de novo.\n' > "$KB/articles/other.md"
printf 'not an article\n' > "$KB/articles/notes.txt"
printf '# Draft outside the glob base\n' > "$KB/drafts/x.md"
CFG="$KB/kb-verify.config.json"
"$JQ" -n --arg root "$KB" '{version: 1, kb_root: $root, articles_dir: "articles", triage_dir: "triage",
  gh: {repo: "acme/monorepo"},
  budgets: {search_calls_per_article: 2, fetch_calls_per_article: 3, index_i18n_files: 2},
  integration: {article_glob: "articles/**/*.md", locales: ["en", "pt-BR"],
                frontmatter_map: {title: "titulo", tags: "etiquetas", topic: "politica", status: "estado"},
                verify_when: {status_in: ["draft", "review"]}}}' > "$CFG"
export KB_VERIFY_CONFIG="$CFG"
ART_SHA=$(sha_of "$ART"); ART12=$(printf '%s' "$ART_SHA" | cut -c1-12)
ART_ID='articles/billing/cancelar-assinatura.md'
export KB_VERIFY_FAKE_NOW=1700000000       # 2023-11-14T22:13:20Z

# ============================================================ dispatcher ==
echo "# dispatcher and envelope"
code_cmd "unknown subcommand -> INVALID_INPUT" INVALID_INPUT bogus
code_cmd "missing subcommand -> INVALID_INPUT" INVALID_INPUT
code_cmd "argument with metacharacter -> INVALID_INPUT" INVALID_INPUT gh-fetch --run r1 --article abc 'x;y'
code_cmd "argument with space -> INVALID_INPUT" INVALID_INPUT frontmatter 'a b.md'
code_cmd "argument with .. -> INVALID_INPUT" INVALID_INPUT frontmatter ../x.md
is_true "INVALID_INPUT names the argument position" msg_has "argument 1 of 'frontmatter'"
code_cmd "subcommand names are case-sensitive" INVALID_INPUT Armed
is_true "unknown-subcommand message lists the closed list" msg_has "config-init"

echo "# armed"
ok_cmd "armed with a valid config" armed
eq "armed state" ARMED "$(f .data.state)"
eq "armed reports kb_root resolved" "$KB" "$(f .data.config.kb_root)"
eq "armed reports absolute articles_dir" "$KB/articles" "$(f .data.config.articles_dir)"
eq "armed reports gh.repo" acme/monorepo "$(f .data.config.gh.repo)"
eq "armed reports budgets with defaults applied" 2 "$(f .data.config.budgets.search_calls_per_article)"
eq "armed reports mock mode" true "$(f .data.mock)"
mkdir -p "$T/empty"
KBV_CWD="$T/empty" KBV_ENV='-u KB_VERIFY_CONFIG' ok_cmd "armed outside any KB" armed
eq "armed outside any KB -> DISARMED" DISARMED "$(f .data.state)"
eq "DISARMED is a handled state: nothing on stderr" '' "$ERR"
KBV_ENV="KB_VERIFY_CONFIG=$T/missing.json" code_cmd "armed with a missing config file -> INVALID_INPUT" INVALID_INPUT armed
is_true "invalid config names the piece (file)" msg_has "config invalid (file)"
printf '{"kb_root":"%s","articles_dir":"a","triage_dir":"t"}' "$KB" > "$T/norepo.json"
KBV_ENV="KB_VERIFY_CONFIG=$T/norepo.json" code_cmd "config without gh.repo -> INVALID_INPUT" INVALID_INPUT armed
is_true "invalid config names the piece (gh.repo)" msg_has "config invalid (gh.repo)"
KBV_ENV="KB_VERIFY_CONFIG=$T/norepo.json" code_cmd "run-begin with invalid config -> INVALID_INPUT" INVALID_INPUT run-begin
code_cmd "armed rejects arguments" INVALID_INPUT armed extra

# ============================================================= run-begin ==
echo "# run-begin"
ok_cmd "run-begin creates a run" run-begin
RUN=$(f .data.run)
is_true "run id is yyyymmdd-HHMMSS-4hex" jqcheck "$OUT" '.data.run | test("^[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$")'
eq "run-begin pins the mock commit" mock0000commit "$(f .data.commit)"
is_true "run dir, inbox and cache exist" test -d "$DATA/runs/$RUN/inbox" -a -d "$DATA/runs/$RUN/cache" -a -f "$DATA/runs/$RUN/run.json"
eq "run.json carries the commit" mock0000commit "$("$JQ" -r .commit "$DATA/runs/$RUN/run.json")"
eq "run.json starts with search_available true" true "$("$JQ" -r .search_available "$DATA/runs/$RUN/run.json")"
ok_cmd "run-begin --resume reuses the run" run-begin --resume "$RUN"
eq "resume keeps the commit" mock0000commit "$(f .data.commit)"
eq "resume flags resumed" true "$(f .data.resumed)"
code_cmd "run-begin --resume unknown -> INVALID_INPUT" INVALID_INPUT run-begin --resume 20200101-000000-dead
code_cmd "run-begin --resume with a bad id -> INVALID_INPUT" INVALID_INPUT run-begin --resume a/b
code_cmd "run-begin rejects unknown flags" INVALID_INPUT run-begin --bogus
ok_cmd "run-begin --learn creates a run without a commit" run-begin --learn
LEARN_RUN=$(f .data.run)
eq "learn run has commit null" null "$(f .data.commit)"
eq "learn run is flagged" true "$(f .data.learn)"
KBV_ENV='KB_VERIFY_MOCK_CODE=GH_AUTH' code_cmd "run-begin with forced GH_AUTH" GH_AUTH run-begin
KBV_ENV='KB_VERIFY_MOCK_CODE=RATE_LIMITED' code_cmd "run-begin with forced RATE_LIMITED" RATE_LIMITED run-begin
eq "RATE_LIMITED carries retry_after" 60 "$(f .retry_after)"

# =========================================================== frontmatter ==
echo "# frontmatter goldens"
GOLD_N=0
for md in "$GOLDEN"/*.md; do
  name=$(basename "$md" .md)
  GOLD_N=$((GOLD_N + 1))
  kbv frontmatter "$md"
  env_ok "golden $name envelope" || continue
  got=$(printf '%s' "$OUT" | "$JQ" -S -c '.data | del(.path, .article_id, .sha256, .sha12)')
  want=$("$JQ" -S -c . "$GOLDEN/$name.expected.json")
  eq "golden $name" "$want" "$got"
  eq "golden $name sha256" "$(sha_of "$md")" "$(f .data.sha256)"
done
eq "five goldens present" 5 "$GOLD_N"
ok_cmd "frontmatter of a KB article" frontmatter "$ART"
eq "article_id is relative to kb_root" "$ART_ID" "$(f .data.article_id)"
eq "sha12 is the sha256 prefix" "$ART12" "$(f .data.sha12)"
code_cmd "frontmatter of a missing file -> INVALID_INPUT" INVALID_INPUT frontmatter "$KB/articles/nope.md"
code_cmd "frontmatter without argument -> INVALID_INPUT" INVALID_INPUT frontmatter

# ============================================================= gh-search ==
echo "# gh-search"
inbox "$RUN" "claims-$ART12" '{"article":"articles/billing/cancelar-assinatura.md","claims":[{"id":"c1","type":"limit","material":true,"text":"reembolso em 10 dias","anchor":"REFUND_WINDOW_DAYS"},{"id":"c2","type":"step","material":false,"text":"cancelar","anchor":"cancelSubscription"},{"id":"c3","type":"behavior","material":true,"text":"ambos","anchor":"REFUND_WINDOW_DAYS + cancelSubscription()"},{"id":"c4","type":"step","material":false,"text":"x","anchor":"!!"}]}'
ok_cmd "search hits by anchor" gh-search --run "$RUN" --article "$ART12" --claim c1
eq "search hit paths (sorted)" '["apps/billing/src/cancel.ts","apps/billing/src/constants.ts"]' "$(fj '.data.hits | map(.path)')"
eq "search fragment is the matching line" 'export const REFUND_WINDOW_DAYS = 7;' "$(f '.data.hits[0].fragment')"
eq "first search is not cached" false "$(f .data.cached)"
eq "first search counts 1/2" 1 "$(f .data.search_calls)"
eq "first search in a run waits 0" 0 "$(f .data.waited)"
ok_cmd "identical search is served from cache" gh-search --run "$RUN" --article "$ART12" --claim c1
eq "cache hit flagged" true "$(f .data.cached)"
eq "cache hit does not consume budget" 1 "$(f .data.search_calls)"
is_true "cache file exists under cache/search" test -n "$(ls "$DATA/runs/$RUN/cache/search/"*.json 2>/dev/null)"
ok_cmd "AND of terms narrows the hits" gh-search --run "$RUN" --article "$ART12" --claim c3
eq "AND query" 'REFUND_WINDOW_DAYS cancelSubscription' "$(f .data.query)"
eq "AND hits only the file with both terms" '["apps/billing/src/cancel.ts"]' "$(fj '.data.hits | map(.path)')"
eq "second real search within 6 s waits the remainder" 6 "$(f .data.waited)"
eq "budget now 2/2" 2 "$(f .data.search_calls)"
code_cmd "call N+1 -> BUDGET_EXHAUSTED" BUDGET_EXHAUSTED gh-search --run "$RUN" --article "$ART12" --claim c2
ok_cmd "cached search still works after the budget is exhausted" gh-search --run "$RUN" --article "$ART12" --claim c1
ART2='bbbbbbbbbbbb'
inbox "$RUN" "claims-$ART2" '{"claims":[{"id":"k1","anchor":"cancelSubscription"},{"id":"k2","anchor":"REFUND_WINDOW_DAYS_LABEL"}]}'
# The previous real search waited 6 s at t=1700000000, so the pacing clock is at 1700000006.
KBV_ENV='KB_VERIFY_FAKE_NOW=1700000009' ok_cmd "search 3 s after the pacing clock waits 3" gh-search --run "$RUN" --article "$ART2" --claim k2
eq "partial wait" 3 "$(f .data.waited)"
KBV_ENV='KB_VERIFY_FAKE_NOW=1700000018' ok_cmd "search 6 s after the pacing clock waits 0" gh-search --run "$RUN" --article "$ART2" --claim k1 --path apps/billing/src
eq "pacing satisfied" 0 "$(f .data.waited)"
eq "--path restricts hits to the prefix" '["apps/billing/src/cancel.ts"]' "$(fj '.data.hits | map(.path)')"
eq "--path is part of the query" 'cancelSubscription path:apps/billing/src' "$(f .data.query)"
eq "search.last holds the effective clock" 1700000018 "$(cat "$DATA/runs/$RUN/search.last")"
ART4='eeeeeeeeeeee'
inbox "$RUN" "claims-$ART4" '{"claims":[{"id":"k1","anchor":"cancelSubscription"}]}'
ok_cmd "same terms without --path is a different query" gh-search --run "$RUN" --article "$ART4" --claim k1
eq "unrestricted search finds every file with the term" '["apps/billing/src/cancel.ts","apps/billing/tests/cancel.test.ts","dist/bundle.js","docs/guide.md","node_modules/x/index.js"]' "$(fj '.data.hits | map(.path)')"
eq "hits are capped at 30" true "$(f '(.data.hits | length) <= 30')"
eq "search budget is per article: the first article stays exhausted" 2 "$("$JQ" -r .search_calls "$DATA/runs/$RUN/budget/$ART12.json")"
eq "budget of the new article is 1" 1 "$(f .data.search_calls)"
code_cmd "unknown claim id -> INVALID_INPUT" INVALID_INPUT gh-search --run "$RUN" --article "$ART12" --claim c99
code_cmd "anchor without searchable terms -> INVALID_INPUT" INVALID_INPUT gh-search --run "$RUN" --article "$ART12" --claim c4
code_cmd "--article must be 12 hex" INVALID_INPUT gh-search --run "$RUN" --article abc --claim c1
code_cmd "missing claims file -> INVALID_INPUT" INVALID_INPUT gh-search --run "$RUN" --article cccccccccccc --claim c1
code_cmd "unknown run -> INVALID_INPUT" INVALID_INPUT gh-search --run nope --article "$ART12" --claim c1
code_cmd "learn run has no commit -> INVALID_INPUT" INVALID_INPUT gh-search --run "$LEARN_RUN" --article "$ART12" --claim c1
ART3='dddddddddddd'
inbox "$RUN" "claims-$ART3" '{"claims":[{"id":"k3","anchor":"ERR_REFUND_WINDOW"},{"id":"k4","anchor":"REFUND_WINDOW_DAYS_LABEL"}]}'
KBV_ENV='KB_VERIFY_MOCK_CODE=RATE_LIMITED' code_cmd "forced RATE_LIMITED on search" RATE_LIMITED gh-search --run "$RUN" --article "$ART3" --claim k3
eq "RATE_LIMITED search carries retry_after" 60 "$(f .retry_after)"
eq "a rate-limited call still counts against the budget" 1 "$("$JQ" -r .search_calls "$DATA/runs/$RUN/budget/$ART3.json")"
is_false "a rate-limited call is not cached" test -n "$(grep -l 'ERR_REFUND_WINDOW' "$DATA/runs/$RUN/cache/search/"*.json 2>/dev/null)"
ok_cmd "the same search succeeds once the limit clears" gh-search --run "$RUN" --article "$ART3" --claim k3
eq "hit after retry" '["apps/billing/src/constants.ts"]' "$(fj '.data.hits | map(.path)')"
ok_cmd "run-begin a second run for SEARCH_UNAVAILABLE" run-begin
RUN2=$(f .data.run)
inbox "$RUN2" "claims-$ART2" '{"claims":[{"id":"k1","anchor":"cancelSubscription"},{"id":"k3","anchor":"ERR_REFUND_WINDOW"}]}'
KBV_ENV='KB_VERIFY_MOCK_CODE=SEARCH_UNAVAILABLE' code_cmd "forced SEARCH_UNAVAILABLE" SEARCH_UNAVAILABLE gh-search --run "$RUN2" --article "$ART2" --claim k1
eq "run.json persists search_available:false" false "$("$JQ" -r .search_available "$DATA/runs/$RUN2/run.json")"
eq "mapping.json repo.search_available:false" false "$("$JQ" -r .repo.search_available "$KB/.kb-verify/mapping.json")"
BUDGET_BEFORE=$("$JQ" -r '.search_calls' "$DATA/runs/$RUN2/budget/$ART2.json")
code_cmd "later searches in the run short-circuit to SEARCH_UNAVAILABLE" SEARCH_UNAVAILABLE gh-search --run "$RUN2" --article "$ART2" --claim k3
eq "short-circuit consumes no budget" "$BUDGET_BEFORE" "$("$JQ" -r '.search_calls' "$DATA/runs/$RUN2/budget/$ART2.json")"
ok_cmd "search still works in the first run" gh-search --run "$RUN" --article "$ART2" --claim k1

# ============================================================== gh-fetch ==
echo "# gh-fetch"
ok_cmd "fetch a file" gh-fetch --run "$RUN" --article "$ART12" apps/billing/src/cancel.ts
LP=$(f .data.local_path)
eq "local_path under cache/<commit>" "$DATA/runs/$RUN/cache/mock0000commit/apps/billing/src/cancel.ts" "$LP"
is_true "fetched content is identical" cmp -s "$LP" "$REPO/apps/billing/src/cancel.ts"
eq "fetch counts 1/3" 1 "$(f .data.fetch_calls)"
ok_cmd "fetch a dot path" gh-fetch --run "$RUN" --article "$ART12" .github/workflows/ci.yml
eq "leading-dot segment becomes _dot_" "$DATA/runs/$RUN/cache/mock0000commit/_dot_github/workflows/ci.yml" "$(f .data.local_path)"
is_true "grep -r finds the dot-path file in the cache" grep -rq 'name: ci' "$DATA/runs/$RUN/cache/mock0000commit"
ok_cmd "re-fetch of a cached file" gh-fetch --run "$RUN" --article "$ART12" apps/billing/src/cancel.ts
eq "re-fetch flagged cached" true "$(f .data.cached)"
eq "re-fetch consumes no budget" 2 "$(f .data.fetch_calls)"
code_cmd "missing file -> NOT_FOUND" NOT_FOUND gh-fetch --run "$RUN" --article "$ART12" apps/nope.ts
code_cmd "call N+1 -> BUDGET_EXHAUSTED" BUDGET_EXHAUSTED gh-fetch --run "$RUN" --article "$ART12" docs/guide.md
ok_cmd "cached fetch still works after the budget is exhausted" gh-fetch --run "$RUN" --article "$ART12" .github/workflows/ci.yml
KBV_ENV='KB_VERIFY_MOCK_CODE=NOT_FOUND' code_cmd "forced NOT_FOUND on an existing file" NOT_FOUND gh-fetch --run "$RUN" --article "$ART2" docs/guide.md
is_false "forced NOT_FOUND wrote nothing" test -e "$DATA/runs/$RUN/cache/mock0000commit/docs/guide.md"
code_cmd "absolute path -> INVALID_INPUT" INVALID_INPUT gh-fetch --run "$RUN" --article "$ART2" /etc/passwd
code_cmd "missing path -> INVALID_INPUT" INVALID_INPUT gh-fetch --run "$RUN" --article "$ART2"
code_cmd "learn run cannot fetch" INVALID_INPUT gh-fetch --run "$LEARN_RUN" --article "$ART2" docs/guide.md

# ============================================================ repo-index ==
echo "# repo-index"
IDX="$DATA/repo/acme-monorepo"
ok_cmd "repo-index builds the index" repo-index
eq "index dir" "$IDX" "$(f .data.index_dir)"
eq "one tree call when not truncated" 1 "$(f .data.tree_calls)"
eq "tree_partial false" false "$(f .data.tree_partial)"
eq "refreshed true" true "$(f .data.refreshed)"
is_true "tree.txt lists a blob" grep -qx 'apps/billing/src/cancel.ts' "$IDX/tree.txt"
is_true "tree.txt lists the dot path" grep -qx '.github/workflows/ci.yml' "$IDX/tree.txt"
is_true "full recursive listing includes node_modules" grep -qx 'node_modules/x/index.js' "$IDX/tree.txt"
eq "i18n candidates are locale-filtered (4 of 6 files)" 4 "$(f .data.i18n_candidates)"
eq "i18n fetch capped by budgets.index_i18n_files" 2 "$(f .data.i18n_files)"
eq "i18n_partial true when capped" true "$(f .data.i18n_partial)"
is_true "i18n/ holds en.common.json" test -f "$IDX/i18n/apps/web/i18n/en.common.json"
is_true "i18n/ holds locales/en.json" test -f "$IDX/i18n/apps/web/locales/en.json"
is_false "i18n/ skips es.json (not a configured locale)" test -e "$IDX/i18n/apps/web/locales/es.json"
is_false "i18n/ skips README.md" test -e "$IDX/i18n/apps/web/locales/README.md"
eq "mapping.json repo.index_commit" mock0000commit "$("$JQ" -r .repo.index_commit "$KB/.kb-verify/mapping.json")"
eq "mapping.json repo.indexed_at from the clock" 2023-11-14 "$("$JQ" -r .repo.indexed_at "$KB/.kb-verify/mapping.json")"
eq "mapping.json repo.i18n_partial" true "$("$JQ" -r .repo.i18n_partial "$KB/.kb-verify/mapping.json")"
eq "mapping.json repo.search_available untouched by repo-index" false "$("$JQ" -r .repo.search_available "$KB/.kb-verify/mapping.json")"
ok_cmd "repo-index without --refresh reuses a fresh index" repo-index
eq "refreshed false" false "$(f .data.refreshed)"
ok_cmd "repo-index --refresh rebuilds" repo-index --refresh
eq "refreshed true after --refresh" true "$(f .data.refreshed)"
touch "$REPO/.kbv-truncated"
ok_cmd "truncated root triggers descent" repo-index --refresh
eq "descent: root + 3 top dirs (node_modules, vendor, dist skipped)" 4 "$(f .data.tree_calls)"
eq "descent completes: tree_partial false" false "$(f .data.tree_partial)"
is_true "descent lists deep blobs" grep -qx 'apps/billing/src/cancel.ts' "$IDX/tree.txt"
is_true "descent lists dot paths" grep -qx '.github/workflows/ci.yml' "$IDX/tree.txt"
is_false "descent skips node_modules" grep -q '^node_modules/' "$IDX/tree.txt"
is_false "descent skips vendor" grep -q '^vendor/' "$IDX/tree.txt"
is_false "descent skips dist" grep -q '^dist/' "$IDX/tree.txt"
is_false "marker file is not listed" grep -q 'kbv-truncated' "$IDX/tree.txt"
touch "$REPO/apps/.kbv-truncated"
ok_cmd "truncated subtree descends one more level" repo-index --refresh
eq "descent: root + 3 top dirs + apps/billing + apps/web" 6 "$(f .data.tree_calls)"
eq "subtree descent complete" false "$(f .data.tree_partial)"
is_true "subtree descent lists apps/web files" grep -qx 'apps/web/locales/pt-BR.json' "$IDX/tree.txt"
is_true "subtree descent lists apps/billing files" grep -qx 'apps/billing/tests/cancel.test.ts' "$IDX/tree.txt"
rm -f "$REPO/apps/.kbv-truncated"
i=1; while [ "$i" -le 310 ]; do d=$(printf 'd%03d' "$i"); mkdir -p "$REPO/$d"; : > "$REPO/$d/f.txt"; i=$((i + 1)); done
ok_cmd "300-call cap" repo-index --refresh
eq "cap: exactly 300 tree calls" 300 "$(f .data.tree_calls)"
eq "cap: tree_partial true" true "$(f .data.tree_partial)"
eq "cap: mapping.json repo.tree_partial true" true "$("$JQ" -r .repo.tree_partial "$KB/.kb-verify/mapping.json")"
rm -rf "$REPO"/d[0-9][0-9][0-9] "$REPO/.kbv-truncated"
cp "$IDX/tree.txt" "$T/tree.before"
KBV_ENV='KB_VERIFY_MOCK_CODE=RATE_LIMITED' code_cmd "forced RATE_LIMITED on repo-index" RATE_LIMITED repo-index --refresh
is_true "failed refresh leaves tree.txt untouched" cmp -s "$IDX/tree.txt" "$T/tree.before"
code_cmd "repo-index rejects unknown args" INVALID_INPUT repo-index --now
ok_cmd "repo-index --refresh restores a clean index" repo-index --refresh

# =========================================================== next-bug-id ==
echo "# next-bug-id (slugify + redact)"
inbox "$RUN" bug-1 '{"title":"Janela de reembolso é 7 dias no código; artigo diz 10","topic":"cancel-subscription","evidence":[{"file":"apps/billing/src/cancel.ts","line":1,"commit":"mock0000commit","snippet":"Authorization: Bearer abc.DEF-123"},{"file":"a.ts","line":2,"commit":"c","snippet":"password=hunter2&next=1 AKIAABCDEFGHIJKLMNOP ghp_abcdefghijklmnop github_pat_11ABC_def"},"-----BEGIN RSA PRIVATE KEY-----\nMIIE\n-----END RSA PRIVATE KEY----- tail"]}'
ok_cmd "next-bug-id on an empty triage dir" next-bug-id --run "$RUN" bug-1
eq "first id is 0001" 0001 "$(f .data.id)"
eq "slug strips accents and punctuation" janela-de-reembolso-e-7-dias-no-codigo-artigo-diz-10 "$(f .data.slug)"
eq "path is <triage_dir>/NNNN-<slug>.md" "$KB/triage/0001-janela-de-reembolso-e-7-dias-no-codigo-artigo-diz-10.md" "$(f .data.path)"
is_true "filename passes the triage grammar" kbv_valid_triage_name "$(f .data.filename)"
eq "topic passed through" cancel-subscription "$(f .data.topic)"
eq "Bearer token redacted" 'Authorization: Bearer [REDACTED]' "$(f '.data.evidence[0].snippet')"
eq "password=, AKIA, ghp_ and github_pat_ redacted" 'password=[REDACTED]&next=1 AKIA[REDACTED] ghp_[REDACTED] github_pat_[REDACTED]' "$(f '.data.evidence[1].snippet')"
eq "string evidence becomes {snippet} and private key redacted" '[REDACTED PRIVATE KEY]' "$(f '.data.evidence[2].snippet')"
eq "evidence file/line/commit preserved" 'apps/billing/src/cancel.ts:1@mock0000commit' "$(f '.data.evidence[0] | "\(.file):\(.line)@\(.commit)"')"
mkdir -p "$KB/triage"; : > "$KB/triage/0007-existing-bug.md"; : > "$KB/triage/feedback.md"
inbox "$RUN" bug-2 '{"title":"   Ação com espaços   e ÇÉDILHA/barra_underscore","evidence":[]}'
ok_cmd "next-bug-id with an existing 0007" next-bug-id --run "$RUN" bug-2
eq "next id is 0008" 0008 "$(f .data.id)"
eq "slug collapses spaces and separators" acao-com-espacos-e-cedilha-barra-underscore "$(f .data.slug)"
inbox "$RUN" bug-3 '{"title":"Refund window is seven days in code but the article says ten days for annual plans and monthly plans alike","evidence":[]}'
ok_cmd "next-bug-id with a long title" next-bug-id --run "$RUN" bug-3
is_true "slug capped at 60 chars" test "$(f '.data.slug | length')" -le 60
is_true "capped slug has no trailing hyphen" jqcheck "$OUT" '.data.slug | test("^[a-z0-9]+(-[a-z0-9]+)*$")'
inbox "$RUN" bug-4 '{"title":"","evidence":[]}'
ok_cmd "next-bug-id with an empty title" next-bug-id --run "$RUN" bug-4
eq "empty title -> untitled" untitled "$(f .data.slug)"
LONG=$(printf 'A%.0s' $(seq 1 260))
inbox "$RUN" bug-5 "{\"title\":\"x\",\"evidence\":[{\"file\":\"f\",\"line\":1,\"commit\":\"c\",\"snippet\":\"$LONG\"}]}"
ok_cmd "next-bug-id with a long snippet" next-bug-id --run "$RUN" bug-5
eq "snippet capped at 200 chars" 200 "$(f '.data.evidence[0].snippet | length')"
printf '{not json' > "$DATA/runs/$RUN/inbox/bug-6.json"
code_cmd "malformed inbox JSON -> INVALID_INPUT" INVALID_INPUT next-bug-id --run "$RUN" bug-6
printf '[1,2]' > "$DATA/runs/$RUN/inbox/bug-7.json"
code_cmd "inbox JSON that is not an object -> INVALID_INPUT" INVALID_INPUT next-bug-id --run "$RUN" bug-7
inbox "$RUN" bug-8 '{"title":["x"],"evidence":[]}'
code_cmd "title not a string -> INVALID_INPUT" INVALID_INPUT next-bug-id --run "$RUN" bug-8
code_cmd "inbox name outside the grammar -> INVALID_INPUT" INVALID_INPUT next-bug-id --run "$RUN" V1
code_cmd "missing inbox file -> INVALID_INPUT" INVALID_INPUT next-bug-id --run "$RUN" bug-404

# ============================================================ diff-check ==
echo "# diff-check"
GOOD_DIFF=$(printf -- '--- a/articles/billing/cancelar-assinatura.md\n+++ b/articles/billing/cancelar-assinatura.md\n@@ -9,4 +9,4 @@\n # Como cancelar a assinatura\n \n 1. Abra Configurações.\n-2. Se o plano for anual, o reembolso leva 10 dias.\n+2. Se o plano for anual, o reembolso leva 7 dias.\n')
"$JQ" -n -c --arg d "$GOOD_DIFF" '{article: "articles/billing/cancelar-assinatura.md", diff: $d, claims: ["c1", "c3"]}' > "$DATA/runs/$RUN/inbox/diff-good.json"
ok_cmd "diff-check accepts an applicable diff" diff-check --run "$RUN" diff-good
eq "base_sha256 is the article sha" "$ART_SHA" "$(f .data.base_sha256)"
eq "header line format" "# kb-verify $RUN base_sha256:$ART_SHA claims:c1,c3" "$(f .data.header)"
eq "diff text starts with the header" "# kb-verify $RUN base_sha256:$ART_SHA claims:c1,c3" "$(f '.data.diff | split("\n")[0]')"
eq "diff text keeps the hunk" "$GOOD_DIFF" "$(f '.data.diff | split("\n")[1:] | join("\n")' | sed '$d')"
eq "diff_path is the sibling .kb-verify.diff" "$KB/articles/billing/cancelar-assinatura.kb-verify.diff" "$(f .data.diff_path)"
eq "hunk count" 1 "$(f .data.hunks)"
"$JQ" -n -c --arg d "# kb-verify old base_sha256:x claims:c9
$GOOD_DIFF" '{article: "articles/billing/cancelar-assinatura.md", diff: $d}' > "$DATA/runs/$RUN/inbox/diff-hdr.json"
ok_cmd "diff-check with a caller-supplied header" diff-check --run "$RUN" diff-hdr
eq "header is replaced, not duplicated" 1 "$(f '.data.diff' | grep -c '^# kb-verify')"
eq "claims default to empty" "# kb-verify $RUN base_sha256:$ART_SHA claims:" "$(f .data.header)"
BAD_DIFF=$(printf '%s\n' "$GOOD_DIFF" | sed 's/-2\. Se o plano for anual, o reembolso leva 10 dias\./-2. linha que nao existe no artigo./')
"$JQ" -n -c --arg d "$BAD_DIFF" '{article: "articles/billing/cancelar-assinatura.md", diff: $d, claims: ["c1"]}' > "$DATA/runs/$RUN/inbox/diff-bad.json"
code_cmd "diff that does not apply -> DIFF_APPLY_FAILED" DIFF_APPLY_FAILED diff-check --run "$RUN" diff-bad
is_true "DIFF_APPLY_FAILED message says which hunk failed" msg_has "hunks failed"
is_false "no .kb-verify.diff written anywhere" test -n "$(find "$KB" -name '*.kb-verify.diff' 2>/dev/null)"
is_true "article untouched" test "$(sha_of "$ART")" = "$ART_SHA"
"$JQ" -n -c --arg d "$GOOD_DIFF" '{article: "drafts/x.md", diff: $d}' > "$DATA/runs/$RUN/inbox/diff-outside.json"
code_cmd "article outside articles_dir -> INVALID_INPUT" INVALID_INPUT diff-check --run "$RUN" diff-outside
"$JQ" -n -c --arg d "$GOOD_DIFF" '{article: "articles/nope.md", diff: $d}' > "$DATA/runs/$RUN/inbox/diff-missing.json"
code_cmd "missing article -> INVALID_INPUT" INVALID_INPUT diff-check --run "$RUN" diff-missing
inbox "$RUN" diff-nodiff '{"article":"articles/billing/cancelar-assinatura.md","diff":""}'
code_cmd "empty diff -> INVALID_INPUT" INVALID_INPUT diff-check --run "$RUN" diff-nodiff
inbox "$RUN" diff-badclaims '{"article":"articles/billing/cancelar-assinatura.md","diff":"x","claims":"c1"}'
code_cmd "claims not an array -> INVALID_INPUT" INVALID_INPUT diff-check --run "$RUN" diff-badclaims

# ======================================================== append-verdict ==
echo "# append-verdict"
VFILE="$KB/.kb-verify/verdicts.jsonl"
verdict_base() {
  "$JQ" -n -c --arg sha "$ART_SHA" --arg run "$RUN" --arg id "$ART_ID" '{run: $run, commit: "mock0000commit",
    article: {id: $id, sha256: $sha, title: "Cancelar assinatura"}, verdict: "CORRECT",
    claims: [{id: "c1", type: "limit", material: true, text: "10 dias", status: "SUPPORTED",
              evidence: [{file: "apps/billing/src/cancel.ts", line: 1, commit: "mock0000commit", snippet: "header Bearer abc.def and password=pw1"}]},
             {id: "c2", type: "step", material: false, text: "abrir", status: "NOT_FOUND", evidence: []}],
    kac: [{assumption: "served locale is pt-BR", class: "locale", if_false: "wrong string", tested: true}],
    investigator: {layer: "e", anchor_type: "symbol", search_calls: 1, fetch_calls: 2, seconds: 12},
    notes: []}'
}
CODE_BUG_MUT='.verdict = "CODE_BUG" | .claims[0].status = "CONTRADICTED" | .claims[0].intent = {kind: "test", file: "apps/billing/tests/cancel.test.ts", line: 1, commit: "mock0000commit", agrees_with: "article"} | .skeptic = {result: "CONFIRMED", reason: "test asserts 10"} | .actions = {bug_report: "triage/0001-x.md"}'
DOC_MUT='.verdict = "DOC_OUTDATED" | .claims[0].status = "CONTRADICTED" | .claims[0].intent = {kind: "none", file: "", line: 0, commit: "", agrees_with: "code"} | .skeptic = {result: "CONFIRMED", reason: "ok"} | .actions = {doc_diff: "articles/billing/cancelar-assinatura.kb-verify.diff"}'
verdict_base > "$DATA/runs/$RUN/inbox/verdict-ok.json"
ok_cmd "append a valid CORRECT verdict" append-verdict --run "$RUN" verdict-ok
eq "line_no 1" 1 "$(f .data.line_no)"
eq "verdicts.jsonl has one line" 1 "$(lines_of "$VFILE")"
eq "snippet redacted in the stored record" 'header Bearer [REDACTED] and password=[REDACTED]' "$(tail -n 1 "$VFILE" | "$JQ" -r '.claims[0].evidence[0].snippet')"
eq "redacted_snippets counted" 1 "$(f .data.redacted_snippets)"
eq "record stamped with the run" "$RUN" "$(tail -n 1 "$VFILE" | "$JQ" -r .run)"
eq "recorded_at from the clock" 2023-11-14T22:13:20Z "$(tail -n 1 "$VFILE" | "$JQ" -r .recorded_at)"
verdict_base | "$JQ" -c "$CODE_BUG_MUT" > "$DATA/runs/$RUN/inbox/verdict-bug.json"
ok_cmd "append a valid CODE_BUG verdict" append-verdict --run "$RUN" verdict-bug
verdict_base | "$JQ" -c "$DOC_MUT" > "$DATA/runs/$RUN/inbox/verdict-doc.json"
ok_cmd "append a valid DOC_OUTDATED verdict" append-verdict --run "$RUN" verdict-doc
verdict_base | "$JQ" -c '.verdict = "INCONCLUSIVE" | .inconclusive_reason = "NOT_LOCATED" | .claims[0].status = "NOT_FOUND"' > "$DATA/runs/$RUN/inbox/verdict-inc.json"
ok_cmd "append a valid INCONCLUSIVE verdict" append-verdict --run "$RUN" verdict-inc
verdict_base | "$JQ" -c 'del(.run) | del(.kac) | del(.notes)' > "$DATA/runs/$RUN/inbox/verdict-min.json"
ok_cmd "run, kac and notes are optional" append-verdict --run "$RUN" verdict-min
eq "five valid lines stored" 5 "$(lines_of "$VFILE")"
# reject <desc> <jq-mutation>: the record must be rejected and nothing appended
reject() {
  local before
  verdict_base | "$JQ" -c "$2" > "$DATA/runs/$RUN/inbox/verdict-bad.json"
  before=$(lines_of "$VFILE")
  code_cmd "reject: $1" INVALID_INPUT append-verdict --run "$RUN" verdict-bad
  eq "reject: $1 appends nothing" "$before" "$(lines_of "$VFILE")"
}
reject "verdict outside the enum" '.verdict = "MAYBE"'
reject "SUPPORTED claim without evidence" '.claims[0].evidence = []'
reject "CONTRADICTED claim without evidence" '.claims[0].status = "CONTRADICTED" | del(.claims[0].evidence)'
reject "evidence line as a string" '.claims[0].evidence[0].line = "12"'
reject "evidence line zero" '.claims[0].evidence[0].line = 0'
reject "evidence without commit" 'del(.claims[0].evidence[0].commit)'
reject "evidence without file" '.claims[0].evidence[0].file = ""'
reject "claim material not boolean" '.claims[0].material = "yes"'
reject "claims not an array" '.claims = {}'
reject "investigator{} missing" 'del(.investigator)'
reject "investigator.layer outside a-e" '.investigator.layer = "z"'
reject "investigator.search_calls as string" '.investigator.search_calls = "3"'
reject "investigator.seconds negative" '.investigator.seconds = -1'
reject "investigator.fetch_calls missing" 'del(.investigator.fetch_calls)'
reject "CODE_BUG without skeptic CONFIRMED" "$CODE_BUG_MUT"' | .skeptic.result = "UNSURE"'
reject "CODE_BUG without skeptic" "$CODE_BUG_MUT"' | del(.skeptic)'
reject "CODE_BUG without actions.bug_report" "$CODE_BUG_MUT"' | .actions = {}'
reject "CODE_BUG with intent.agrees_with code" "$CODE_BUG_MUT"' | .claims[0].intent.agrees_with = "code"'
reject "CODE_BUG without intent" "$CODE_BUG_MUT"' | del(.claims[0].intent)'
reject "CODE_BUG whose contradicted claim is not material" "$CODE_BUG_MUT"' | .claims[0].material = false'
reject "intent.agrees_with outside article|code" '.claims[0].intent = {agrees_with: "maybe"}'
reject "DOC_OUTDATED without actions.doc_diff" "$DOC_MUT"' | .actions = {}'
reject "DOC_OUTDATED without skeptic CONFIRMED" "$DOC_MUT"' | .skeptic.result = "REFUTED"'
reject "INCONCLUSIVE without inconclusive_reason" '.verdict = "INCONCLUSIVE"'
reject "INCONCLUSIVE with a reason outside the enum" '.verdict = "INCONCLUSIVE" | .inconclusive_reason = "LAZY"'
reject "CORRECT with an inconclusive_reason" '.inconclusive_reason = "RATE_LIMITED"'
reject "article.sha256 not 64 hex" '.article.sha256 = "abc"'
reject "article without id" '.article.id = ""'
reject "commit missing" 'del(.commit)'
reject "run mismatch" '.run = "other-run"'
reject "notes not an array" '.notes = "x"'
printf '{"verdict": ' > "$DATA/runs/$RUN/inbox/verdict-bad.json"
code_cmd "reject: malformed JSON" INVALID_INPUT append-verdict --run "$RUN" verdict-bad
eq "still five lines" 5 "$(lines_of "$VFILE")"
code_cmd "append-verdict without --run" INVALID_INPUT append-verdict verdict-ok
is_true "every stored line is valid JSON" "$JQ" -c . "$VFILE"
verdict_base | "$JQ" -c "$DOC_MUT"' | .claims[0].intent = {kind: "none"}' > "$DATA/runs/$RUN/inbox/verdict-none.json"
ok_cmd "DOC_OUTDATED with intent {kind: none} and no agrees_with" append-verdict --run "$RUN" verdict-none
reject "intent kind none with a bogus agrees_with" "$DOC_MUT"' | .claims[0].intent = {kind: "none", agrees_with: "maybe"}'
verdict_base | "$JQ" -c '.mapping_delta = {topic: "cancel-subscription", article: "articles/x.md"}' > "$DATA/runs/$RUN/inbox/verdict-delta.json"
ok_cmd "append a verdict carrying the inbox-only mapping_delta" append-verdict --run "$RUN" verdict-delta
eq "mapping_delta is not persisted in verdicts.jsonl" null "$(tail -n 1 "$VFILE" | "$JQ" -r '.mapping_delta // "null"')"

# ======================================================== mapping-update ==
echo "# mapping-update"
MAP="$KB/.kb-verify/mapping.json"
inbox "$RUN" map-1 '{"topic":"cancel-subscription","article":"articles/billing/cancelar-assinatura.md","aliases":["cancelar assinatura","cancel subscription"],"hits":[{"path":"apps/billing/src/cancel.ts","symbols":["cancelSubscription"]}]}'
ok_cmd "mapping-update applies a hit" mapping-update --run "$RUN" map-1
eq "hits = 1" 1 "$("$JQ" -r '.topics["cancel-subscription"].paths[0].hits' "$MAP")"
eq "last_verified = today" 2023-11-14 "$("$JQ" -r '.topics["cancel-subscription"].paths[0].last_verified' "$MAP")"
eq "commit = run commit" mock0000commit "$("$JQ" -r '.topics["cancel-subscription"].paths[0].commit' "$MAP")"
eq "stale false" false "$("$JQ" -r '.topics["cancel-subscription"].paths[0].stale' "$MAP")"
eq "article recorded" "$ART_ID" "$("$JQ" -r '.topics["cancel-subscription"].articles[0]' "$MAP")"
ok_cmd "mapping-update applies the same hit again" mapping-update --run "$RUN" map-1
eq "hits = 2" 2 "$("$JQ" -r '.topics["cancel-subscription"].paths[0].hits' "$MAP")"
eq "aliases unioned without duplicates" 2 "$("$JQ" -r '.topics["cancel-subscription"].aliases | length' "$MAP")"
eq "articles unioned without duplicates" 1 "$("$JQ" -r '.topics["cancel-subscription"].articles | length' "$MAP")"
inbox "$RUN" map-2 '{"topic":"cancel-subscription","aliases":["cancelar assinatura","cancelamento"],"hits":[{"path":"apps/billing/src/constants.ts"}],"stale":["apps/billing/src/cancel.ts","apps/unknown.ts"]}'
ok_cmd "mapping-update with stale and a new path" mapping-update --run "$RUN" map-2
eq "stale true on the 404 path" true "$("$JQ" -r '.topics["cancel-subscription"].paths[] | select(.path == "apps/billing/src/cancel.ts") | .stale' "$MAP")"
eq "stale path keeps its hits (never deleted)" 2 "$("$JQ" -r '.topics["cancel-subscription"].paths[] | select(.path == "apps/billing/src/cancel.ts") | .hits' "$MAP")"
eq "new path created with hits 1" 1 "$("$JQ" -r '.topics["cancel-subscription"].paths[] | select(.path == "apps/billing/src/constants.ts") | .hits' "$MAP")"
eq "unknown stale path is not created" 2 "$("$JQ" -r '.topics["cancel-subscription"].paths | length' "$MAP")"
eq "aliases now 3" 3 "$("$JQ" -r '.topics["cancel-subscription"].aliases | length' "$MAP")"
inbox "$RUN" map-3 '{"topic":"change-plan","hits":[{"path":"apps/billing/src/plans.ts","symbols":["changePlan"]}]}'
ok_cmd "mapping-update creates a new topic" mapping-update --run "$RUN" map-3
eq "new topic present" 1 "$("$JQ" -r '.topics["change-plan"].paths | length' "$MAP")"
inbox "$RUN" map-4 '{"repo":{"search_available":true,"bogus":"x"}}'
ok_cmd "mapping-update repo{} only" mapping-update --run "$RUN" map-4
eq "repo.search_available applied" true "$("$JQ" -r .repo.search_available "$MAP")"
eq "unknown repo key ignored" null "$("$JQ" -r '.repo.bogus' "$MAP")"
eq "repo.index_commit preserved" mock0000commit "$("$JQ" -r .repo.index_commit "$MAP")"
eq "mapping.json is written with sorted keys (jq -S)" "$("$JQ" -c 'keys' "$MAP")" "$("$JQ" -c 'keys_unsorted' "$MAP")"
eq "version 1" 1 "$("$JQ" -r .version "$MAP")"
inbox "$RUN" map-5 '{"topic":"x","hits":"apps/a.ts"}'
code_cmd "hits not an array -> INVALID_INPUT" INVALID_INPUT mapping-update --run "$RUN" map-5
inbox "$RUN" map-6 '{"hits":[{"path":"apps/a.ts"}]}'
code_cmd "hits without topic -> INVALID_INPUT" INVALID_INPUT mapping-update --run "$RUN" map-6
inbox "$RUN" map-7 '{}'
code_cmd "empty delta -> INVALID_INPUT" INVALID_INPUT mapping-update --run "$RUN" map-7
inbox "$LEARN_RUN" map-8 '{"topic":"x","hits":[{"path":"apps/a.ts"}]}'
code_cmd "hits in a learn run (no commit) -> INVALID_INPUT" INVALID_INPUT mapping-update --run "$LEARN_RUN" map-8
cp "$MAP" "$T/map.bak"; printf '[]' > "$MAP"
code_cmd "corrupt mapping.json is not clobbered" INVALID_INPUT mapping-update --run "$RUN" map-3
eq "corrupt mapping.json left as is" '[]' "$(cat "$MAP")"
cp "$T/map.bak" "$MAP"
inbox "$RUN" map-9 '{"verdict":"CORRECT","article":{"id":"articles/billing/cancelar-assinatura.md"},"mapping_delta":{"topic":"faturas","aliases":["faturas"],"hits":[{"path":"apps/billing/src/invoices.ts"}]}}'
ok_cmd "mapping-update reads mapping_delta from the S8 verdict file" mapping-update --run "$RUN" map-9
eq "delta topic applied" faturas "$(f .data.topic)"
eq "delta hit recorded" 1 "$("$JQ" -r '.topics["faturas"].paths[0].hits' "$MAP")"

# =============================================================== pending ==
echo "# pending"
OTHER="$KB/articles/other.md"; OTHER_SHA=$(sha_of "$OTHER")
ok_cmd "run-begin a fresh run for pending" run-begin
RUN3=$(f .data.run)
ok_cmd "pending on articles dir" pending --run "$RUN3" "$KB/articles"
eq "two articles pending" 2 "$(f '.data.pending | length')"
eq "pending ids are relative to kb_root, notes.txt excluded" '["articles/billing/cancelar-assinatura.md","articles/other.md"]' "$(fj '.data.pending | map(.id)')"
eq "reason new" '["new","new"]' "$(fj '.data.pending | map(.reason)')"
ok_cmd "pending on kb root" pending --run "$RUN3" "$KB"
eq "drafts/ outside the glob base is excluded" 2 "$(f '.data.total')"
"$JQ" -n -c --arg run "$RUN3" --arg sha "$OTHER_SHA" '{run: $run, commit: "mock0000commit", article: {id: "articles/other.md", sha256: $sha, title: "Outro artigo"}, verdict: "CORRECT", claims: [], investigator: {layer: "a", anchor_type: "path", search_calls: 0, fetch_calls: 0, seconds: 1}}' > "$DATA/runs/$RUN3/inbox/verdict-other.json"
ok_cmd "append CORRECT for other.md" append-verdict --run "$RUN3" verdict-other
ok_cmd "pending after a CORRECT verdict" pending --run "$RUN3" "$KB/articles"
eq "other.md concluded" '["articles/billing/cancelar-assinatura.md"]' "$(fj '.data.pending | map(.id)')"
eq "done lists other.md with its verdict" '[{"id":"articles/other.md","verdict":"CORRECT"}]' "$(fj '.data.done | map({id, verdict})')"
printf '\nRegenerated by the rewriter.\n' >> "$OTHER"
ok_cmd "pending after the article changed" pending --run "$RUN3" "$KB/articles"
eq "changed sha re-queues the article" sha_changed "$(f '.data.pending[] | select(.id == "articles/other.md") | .reason')"
"$JQ" -n -c --arg run "$RUN3" --arg sha "$ART_SHA" --arg id "$ART_ID" '{run: $run, commit: "mock0000commit", article: {id: $id, sha256: $sha, title: "t"}, verdict: "INCONCLUSIVE", inconclusive_reason: "RATE_LIMITED", claims: [], investigator: {layer: "c", anchor_type: "symbol", search_calls: 1, fetch_calls: 0, seconds: 2}}' > "$DATA/runs/$RUN3/inbox/verdict-rl.json"
ok_cmd "append INCONCLUSIVE RATE_LIMITED" append-verdict --run "$RUN3" verdict-rl
ok_cmd "pending after a transient verdict" pending --run "$RUN3" "$KB/articles"
eq "transient RATE_LIMITED re-queues" transient:RATE_LIMITED "$(f '.data.pending[] | select(.id == "articles/billing/cancelar-assinatura.md") | .reason')"
"$JQ" -n -c --arg run "$RUN3" --arg sha "$ART_SHA" --arg id "$ART_ID" '{run: $run, commit: "mock0000commit", article: {id: $id, sha256: $sha, title: "t"}, verdict: "INCONCLUSIVE", inconclusive_reason: "GH_AUTH", claims: [], investigator: {layer: "c", anchor_type: "symbol", search_calls: 1, fetch_calls: 0, seconds: 2}}' > "$DATA/runs/$RUN3/inbox/verdict-ga.json"
ok_cmd "append INCONCLUSIVE GH_AUTH" append-verdict --run "$RUN3" verdict-ga
ok_cmd "pending after GH_AUTH" pending --run "$RUN3" "$KB/articles"
eq "transient GH_AUTH re-queues" transient:GH_AUTH "$(f '.data.pending[] | select(.id == "articles/billing/cancelar-assinatura.md") | .reason')"
"$JQ" -n -c --arg run "$RUN3" --arg sha "$ART_SHA" --arg id "$ART_ID" '{run: $run, commit: "mock0000commit", article: {id: $id, sha256: $sha, title: "t"}, verdict: "INCONCLUSIVE", inconclusive_reason: "NOT_LOCATED", claims: [], investigator: {layer: "d", anchor_type: "path", search_calls: 1, fetch_calls: 0, seconds: 2}}' > "$DATA/runs/$RUN3/inbox/verdict-nl.json"
ok_cmd "append INCONCLUSIVE NOT_LOCATED" append-verdict --run "$RUN3" verdict-nl
ok_cmd "pending after a non-transient INCONCLUSIVE" pending --run "$RUN3" "$KB/articles"
eq "NOT_LOCATED concludes the article (latest verdict wins)" '["articles/other.md"]' "$(fj '.data.pending | map(.id)')"
ok_cmd "pending in another run ignores these verdicts" pending --run "$RUN" "$KB/articles"
eq "other run: cancelar-assinatura concluded there (CORRECT earlier), other.md pending" '["articles/other.md"]' "$(fj '.data.pending | map(.id)')"
code_cmd "pending on a missing dir -> INVALID_INPUT" INVALID_INPUT pending --run "$RUN3" "$KB/nope"
code_cmd "pending without dir -> INVALID_INPUT" INVALID_INPUT pending --run "$RUN3"

# ========================================================= memory-append ==
echo "# memory-append"
MEM="$KB/.kb-verify/memory.md"
rm -f "$MEM"
inbox "$LEARN_RUN" lesson-1 '{"section":"Search heuristics","statement":"Prefer error codes and i18n keys over prose anchors.","article":"articles/billing/cancelar-assinatura.md","run":"20260901-120000-abcd"}'
ok_cmd "memory-append creates memory.md from the template" memory-append --run "$LEARN_RUN" lesson-1
eq "first lesson is L-01" L-01 "$(f .data.id)"
eq "line format" 'L-01 Prefer error codes and i18n keys over prose anchors. — from: 20260901-120000-abcd articles/billing/cancelar-assinatura.md' "$(f .data.line)"
is_true "memory.md has the three sections" test "$(grep -c '^## ' "$MEM")" -eq 3
eq "lesson sits right under its section header" 'L-01' "$(awk '/^## Search heuristics/ {getline; print substr($0, 1, 4); exit}' "$MEM")"
inbox "$LEARN_RUN" lesson-2 '{"section":"False-positive patterns","statement":"Multi-line\nstatement   with   spaces","article":"articles/other.md"}'
ok_cmd "memory-append a second lesson in another section" memory-append --run "$LEARN_RUN" lesson-2
eq "second lesson is L-02 and whitespace is normalized" "L-02 Multi-line statement with spaces — from: $LEARN_RUN articles/other.md" "$(f .data.line)"
eq "L-02 is the last line of the file" 'L-02' "$(tail -n 1 "$MEM" | cut -c1-4)"
inbox "$LEARN_RUN" lesson-3 '{"section":"Fragile assumptions","statement":"Tenant overrides change limits: token Bearer abc.def"}'
ok_cmd "memory-append redacts statements" memory-append --run "$LEARN_RUN" lesson-3
eq "statement redacted" 'L-03 Tenant overrides change limits: token Bearer [REDACTED] — from: '"$LEARN_RUN"' -' "$(f .data.line)"
eq "L-03 sits between the fragile header and the false-positive header" 'L-03' "$(awk '/^## Fragile assumptions/ {getline; print substr($0, 1, 4); exit}' "$MEM")"
inbox "$LEARN_RUN" lesson-4 '{"section":"Random","statement":"x"}'
code_cmd "unknown section -> INVALID_INPUT" INVALID_INPUT memory-append --run "$LEARN_RUN" lesson-4
inbox "$LEARN_RUN" lesson-5 '{"section":"Search heuristics","statement":"   "}'
code_cmd "empty statement -> INVALID_INPUT" INVALID_INPUT memory-append --run "$LEARN_RUN" lesson-5
cur=$(lines_of "$MEM"); while [ "$cur" -lt 59 ]; do printf 'filler line %d\n' "$cur" >> "$MEM"; cur=$((cur + 1)); done
inbox "$LEARN_RUN" lesson-6 '{"section":"Search heuristics","statement":"Sixtieth line fits."}'
ok_cmd "memory-append up to exactly 60 lines" memory-append --run "$LEARN_RUN" lesson-6
eq "60 lines now" 60 "$(lines_of "$MEM")"
eq "numbering continues from the highest L-nn" L-04 "$(f .data.id)"
cp "$MEM" "$T/mem.bak"
inbox "$LEARN_RUN" lesson-7 '{"section":"Search heuristics","statement":"Sixty-first line does not fit."}'
code_cmd "61st line -> INVALID_INPUT" INVALID_INPUT memory-append --run "$LEARN_RUN" lesson-7
is_true "refused append leaves memory.md unchanged" cmp -s "$MEM" "$T/mem.bak"
rm -f "$MEM"
inbox "$LEARN_RUN" lesson-8 '{"section":"Search heuristics","statement":"Nested provenance.","from":{"run":"20260901-120000-abcd","article":"articles/other.md","claims":["c1"]},"signal":"triage"}'
ok_cmd "memory-append reads provenance nested under from{}" memory-append --run "$LEARN_RUN" lesson-8
eq "from{} run and article are recorded, not the current run" 'L-01 Nested provenance. — from: 20260901-120000-abcd articles/other.md' "$(f .data.line)"

# =========================================================== config-init ==
echo "# config-init"
KB2="$T/kb2"; mkdir -p "$KB2/artigos/cobranca" "$KB2/artigos/conta"
printf -- '---\ntitulo: Cancelar assinatura\netiquetas: [cobrança]\npolitica: cancelamento\nestado: draft\n---\nAção: cancele a assinatura em Configurações. Não há cobrança após o cancelamento.\n' > "$KB2/artigos/cobranca/cancelar.md"
printf -- '---\ntitulo: Solicitar reembolso\netiquetas: [cobrança, reembolso]\npolitica: reembolso\nestado: review\n---\nSolicitação de reembolso em até 7 dias. Atenção à condição do plano anual.\n' > "$KB2/artigos/cobranca/reembolso.md"
printf -- '---\ntitulo: Alterar senha\netiquetas: [conta]\npolitica: seguranca\nestado: draft\n---\nAlteração de senha: informação, autenticação e sessão são encerradas.\n' > "$KB2/artigos/conta/senha.md"
printf '# Repo readme\n\nEnglish text without frontmatter.\n' > "$KB2/README.md"
KBV_ENV='-u KB_VERIFY_CONFIG' ok_cmd "config-init on a small pt-BR KB (no config needed)" config-init "$KB2"
eq "sampled 4 files" 4 "$(f .data.sampled)"
eq "frontmatter keys counted" 3 "$(f '.data.frontmatter_keys.titulo')"
eq "frontmatter_map guessed" '{"title":"titulo","tags":"etiquetas","topic":"politica","status":"estado"}' "$(fj .data.config.integration.frontmatter_map)"
eq "locales guessed from accents" '["en","pt-BR"]' "$(fj .data.config.integration.locales)"
eq "articles_dir is the folder holding most articles" artigos "$(f .data.config.articles_dir)"
eq "article_glob derived" 'artigos/**/*.md' "$(f .data.config.integration.article_glob)"
eq "verify_when from the status values seen" '["draft","review"]' "$(fj .data.config.integration.verify_when.status_in)"
eq "kb_root is absolute" "$KB2" "$(f .data.config.kb_root)"
eq "three questions" 3 "$(f '.data.questions | length')"
is_true "question 1 is about frontmatter fields" jqcheck "$OUT" '.data.questions[0] | test("title, tags, topic and status")'
is_true "question 2 is about the rewriter folder" jqcheck "$OUT" '.data.questions[1] | test("rewriter")'
is_true "question 3 is about the ready status" jqcheck "$OUT" '.data.questions[2] | test("ready to verify")'
fj .data.config > "$T/proposed.json"
KBV_CONFIG_ERROR=''
is_true "proposed config passes kbv_load_config" kbv_load_config "$T/proposed.json"
KB3="$T/kb3"; mkdir -p "$KB3/docs"
printf -- '---\ntitle: Change password\ntags: [account]\nstatus: published\n---\nPlain English article about passwords and sessions.\n' > "$KB3/docs/password.md"
ok_cmd "config-init on an English KB" config-init "$KB3"
eq "English KB keeps canonical keys" '{"title":"title","tags":"tags","topic":"topic","status":"status"}' "$(fj .data.config.integration.frontmatter_map)"
eq "English KB -> locales [en]" '["en"]' "$(fj .data.config.integration.locales)"
eq "single status value proposed" '["published"]' "$(fj .data.config.integration.verify_when.status_in)"
code_cmd "config-init on a missing dir -> INVALID_INPUT" INVALID_INPUT config-init "$T/nowhere"
code_cmd "config-init without argument -> INVALID_INPUT" INVALID_INPUT config-init

# --------------------------------------------------------------- summary --
echo "1..$N"
if [ "$FAILS" -ne 0 ]; then
  echo "# FAILED $FAILS of $N"
  exit 1
fi
echo "# all $N passed (bash $BASH_VERSION)"
exit 0
