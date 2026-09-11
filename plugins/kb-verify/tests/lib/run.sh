#!/bin/bash
# tests/lib/run.sh -- self-contained test of lib/common.sh.
#
# Run:  /bin/bash tests/lib/run.sh        (bash 3.2 on macOS, bash 5 on CI)
# Output is TAP-style ("ok N - ..." / "not ok N - ..."); exit 1 on failure.
# Needs: jq (resolved by the library), realpath, shasum, sed, tr, cut.

set -u

HERE=$(cd "$(dirname "$0")" && pwd -P)
PLUGIN_ROOT=$(cd "$HERE/../.." && pwd -P)
LIB="$PLUGIN_ROOT/lib/common.sh"

# Isolate from the caller's environment.
unset KB_VERIFY_CONFIG KB_VERIFY_JQ KB_VERIFY_DATA_DIR CLAUDE_PLUGIN_DATA CDPATH
T=$(mktemp -d "${TMPDIR:-/tmp}/kbv-lib-test.XXXXXX") || { echo "mktemp failed"; exit 1; }
trap 'rm -rf "$T"' EXIT
TR=$(realpath "$T")             # physical path (/tmp is a symlink on macOS)
HOME="$T/home"; export HOME; mkdir -p "$HOME"

# shellcheck source=../../lib/common.sh
. "$LIB" || { echo "cannot source $LIB"; exit 1; }

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
# eq <desc> <expected> <actual>
eq() { if [ "$2" = "$3" ]; then pass "$1"; else fail "$1" "expected [$2] got [$3]"; fi; }
# is_true <desc> <cmd...>   /  is_false <desc> <cmd...>
is_true() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then pass "$d"; else fail "$d" "expected success, got failure"; fi; }
is_false() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then fail "$d" "expected failure, got success"; else pass "$d"; fi; }
# rc_is <desc> <expected_rc> <cmd...>
rc_is() { local d="$1" want="$2" got; shift 2; "$@" >/dev/null 2>&1; got=$?; eq "$d" "$want" "$got"; }
# repeat <string> <count>
repeat() { local out='' i=0; while [ "$i" -lt "$2" ]; do out="$out$1"; i=$((i + 1)); done; printf '%s' "$out"; }
# lines <string> -> number of lines
lines() { printf '%s\n' "$1" | wc -l | tr -d ' '; }

JQ=$(kbv_resolve_jq) || { echo "Bail out! jq not found; cannot validate envelopes"; exit 1; }
# jqcheck <json> <filter>  -> success when the filter is truthy
jqcheck() { printf '%s' "$1" | "$JQ" -e "$2" >/dev/null 2>&1; }

# ---------------------------------------------------------- normalize_path --
echo "# kbv_normalize_path"
mkdir -p "$T/kb/articles/sub" "$T/outside"
: > "$T/kb/articles/x.md"
ln -s "$T/outside" "$T/kb/articles/link"
ln -s "$T/nowhere" "$T/kb/articles/dangling"
ln -s loop "$T/kb/articles/loop"

eq "absolute existing file resolves to physical path" "$TR/kb/articles/x.md" "$(kbv_normalize_path "$T/kb/articles/x.md" /)"
eq "relative path joins the given cwd" "$TR/kb/articles/x.md" "$(kbv_normalize_path articles/x.md "$T/kb")"
eq "relative path uses the given cwd, not PWD" "$TR/kb/articles/x.md" "$(cd / && kbv_normalize_path articles/x.md "$T/kb")"
eq "empty cwd falls back to PWD" "$TR/kb/articles/x.md" "$(cd "$T/kb" && kbv_normalize_path articles/x.md '')"
eq "non-existing rest is re-appended" "$TR/kb/articles/new/y.md" "$(kbv_normalize_path articles/new/y.md "$T/kb")"
eq "dot and empty segments are dropped" "$TR/kb/articles/new/sub/y.md" "$(kbv_normalize_path 'articles/./new//sub/./y.md' "$T/kb")"
eq "trailing slash is dropped" "$TR/kb/articles" "$(kbv_normalize_path "$T/kb/articles/" /)"
eq "root path" "/" "$(kbv_normalize_path / /)"
eq "tilde-slash expands to HOME" "$TR/home/.ssh/id_rsa" "$(kbv_normalize_path '~/.ssh/id_rsa' /)"
eq "bare tilde expands to HOME" "$TR/home" "$(kbv_normalize_path '~' /)"
eq "symlink to outside resolves to the target" "$TR/outside/new.md" "$(kbv_normalize_path articles/link/new.md "$T/kb")"
is_false "symlink target is not under kb root" kbv_under "$(kbv_normalize_path articles/link/new.md "$T/kb")" "$TR/kb"
eq ".. inside the existing prefix is resolved" "$TR/kb/articles/x.md" "$(kbv_normalize_path articles/sub/../x.md "$T/kb")"
eq ".. after an existing dir before a new file is resolved" "$TR/kb/articles/new.md" "$(kbv_normalize_path "$T/kb/articles/sub/../new.md" /)"
rc_is ".. in the non-existing rest is rejected" 1 kbv_normalize_path articles/nope/../x.md "$T/kb"
rc_is ".. escaping through a non-existing dir is rejected" 1 kbv_normalize_path "$T/kb/articles/nope/../../../etc/passwd" /
rc_is "dangling symlink is rejected" 3 kbv_normalize_path articles/dangling "$T/kb"
rc_is "dangling symlink deeper in the path is rejected" 3 kbv_normalize_path articles/dangling/new.md "$T/kb"
rc_is "symlink loop is rejected" 3 kbv_normalize_path articles/loop "$T/kb"
rc_is "empty path is rejected" 1 kbv_normalize_path '' "$T/kb"
rc_is "relative cwd is rejected" 1 kbv_normalize_path x.md relative/dir
empty_home_tilde() { ( HOME=''; kbv_normalize_path '~/x' / ); }
rc_is "tilde with empty HOME is rejected" 1 empty_home_tilde

# ------------------------------------------------------------------- under --
echo "# kbv_under"
is_true "path equal to root" kbv_under /kb/articles /kb/articles
is_true "child of root" kbv_under /kb/articles/a/b.md /kb/articles
is_false "sibling sharing a prefix" kbv_under /kb/articles2/x /kb/articles
is_false "parent of root" kbv_under /kb /kb/articles
is_true "root with trailing slash" kbv_under /kb/articles/x /kb/articles/
is_true "slash contains everything" kbv_under /etc/passwd /
is_false "relative path never under slash" kbv_under etc/passwd /
is_false "empty path" kbv_under '' /kb
is_false "empty root" kbv_under /kb ''

# ----------------------------------------------------------------- slugify --
echo "# kbv_slugify"
eq "plain title" "refund-window-is-7-days-in-code-article-says-10" "$(kbv_slugify 'Refund window is 7 days in code; article says 10')"
eq "accents stripped (pt-BR)" "acao-de-cafe-a-sao-paulo-urgent" "$(kbv_slugify 'Ação de café à São Paulo — Ürgent!')"
eq "accents stripped (mixed Latin)" "aeiou-cn-ss-ore-aesir-oeuvre-thor" "$(kbv_slugify 'ÀÉÎÕÜ Çñ ß Øre Æsir Œuvre Þor')"
eq "Latin Extended-A" "lodz-zazolc-gesla-jazn-strasse" "$(kbv_slugify 'Łódź zażółć gęślą jaźń straße')"
eq "NFD combining marks removed" "cafe-nfd" "$(kbv_slugify "$(printf 'cafe\314\201 nfd')")"
eq "spaces collapse and trim" "multiple-spaces-here" "$(kbv_slugify '  multiple   spaces  here  ')"
eq "uppercase lowered" "hello-world" "$(kbv_slugify 'HELLO World')"
eq "newline and tab become separators" "a-b-c" "$(kbv_slugify "$(printf 'a\nb\tc')")"
eq "punctuation collapses to one hyphen" "a-b" "$(kbv_slugify 'a -- / . b')"
eq "capped at 60 characters" "$(repeat a 60)" "$(kbv_slugify "$(repeat a 80)")"
eq "no trailing hyphen after the cap" "$(repeat a 59)" "$(kbv_slugify "$(repeat a 59) bbbbb")"
eq "empty becomes untitled" untitled "$(kbv_slugify '')"
eq "punctuation only becomes untitled" untitled "$(kbv_slugify '!!! ???')"
eq "non-Latin script only becomes untitled" untitled "$(kbv_slugify '日本語')"
eq "non-Latin script is dropped around Latin" guide "$(kbv_slugify '日本語 guide')"
is_true "slug forms a valid triage name" kbv_valid_triage_name "0001-$(kbv_slugify 'Ação: café!').md"
is_true "capped slug forms a valid triage name" kbv_valid_triage_name "0001-$(kbv_slugify "$(repeat a 59) bbbbb").md"

# ------------------------------------------------------------------ redact --
echo "# kbv_redact"
eq "Bearer token" "Authorization: Bearer [REDACTED] ok" "$(printf 'Authorization: Bearer abc.DEF-123_x/y+z= ok' | kbv_redact)"
eq "bearer lowercase" "Bearer [REDACTED]" "$(printf 'bearer eyJhbGciOiJIUzI1NiJ9.e30.abc' | kbv_redact)"
eq "password=" "password=[REDACTED]&next=1" "$(printf 'password=hunter2&next=1' | kbv_redact)"
eq "PASSWORD= uppercase" "PASSWORD=[REDACTED] tail" "$(printf 'PASSWORD=Sup3r!x tail' | kbv_redact)"
eq "password= inside quotes" 'x="password=[REDACTED]"' "$(printf 'x="password=s3cr3t"' | kbv_redact)"
eq "password= ends at semicolon" "password=[REDACTED]; y" "$(printf 'password=abc; y' | kbv_redact)"
eq "AWS access key" "key AKIA[REDACTED] end" "$(printf 'key AKIAABCDEFGHIJKLMNOP end' | kbv_redact)"
eq "AKIA followed by too few chars untouched" "AKIA1234 x" "$(printf 'AKIA1234 x' | kbv_redact)"
eq "ghp token" "ghp_[REDACTED]" "$(printf 'ghp_abcdefghijklmnopqrstuvwxyz0123456789' | kbv_redact)"
eq "gho token" "t=gho_[REDACTED];" "$(printf 't=gho_16C7e42F292c6912E7710c838347Ae178B4a;' | kbv_redact)"
eq "ghs token" "ghs_[REDACTED]" "$(printf 'ghs_abc123' | kbv_redact)"
eq "github_pat token" "github_pat_[REDACTED] x" "$(printf 'github_pat_11ABCDEF_abc123XYZ x' | kbv_redact)"
eq "multi-line private key block" "$(printf 'before\n[REDACTED PRIVATE KEY]\nafter')" \
  "$(printf 'before\n-----BEGIN RSA PRIVATE KEY-----\nMIIEow\nAAAA\n-----END RSA PRIVATE KEY-----\nafter' | kbv_redact)"
eq "single-line private key" "k=[REDACTED PRIVATE KEY] tail" \
  "$(printf 'k=-----BEGIN PRIVATE KEY-----MIIE-----END PRIVATE KEY----- tail' | kbv_redact)"
eq "OPENSSH private key block" "$(printf 'a\n[REDACTED PRIVATE KEY]\nz')" \
  "$(printf 'a\n-----BEGIN OPENSSH PRIVATE KEY-----\nb3Bl\n-----END OPENSSH PRIVATE KEY-----\nz' | kbv_redact)"
eq "truncated private key block drops to EOF" "$(printf 'a\n[REDACTED PRIVATE KEY]')" \
  "$(printf 'a\n-----BEGIN EC PRIVATE KEY-----\nMIIE\nMORE' | kbv_redact)"
eq "several patterns on one line" "Bearer [REDACTED] password=[REDACTED] AKIA[REDACTED] ghp_[REDACTED]" \
  "$(printf 'Bearer tok password=pw AKIAABCDEFGHIJKLMNOP ghp_abc' | kbv_redact)"
eq "clean text unchanged" "const REFUND_WINDOW_DAYS = 7; // password policy" "$(printf 'const REFUND_WINDOW_DAYS = 7; // password policy' | kbv_redact)"
eq "empty input" "" "$(printf '' | kbv_redact)"

# --------------------------------------------------------------- valid_arg --
echo "# kbv_valid_arg"
for good in --run r1 apps/a.ts org/repo@abc123 a=b k:v _x 0001-slug.md --article=1a2b3c4d5e6f; do
  is_true "valid_arg accepts [$good]" kbv_valid_arg "$good"
done
for bad in '' 'a b' 'a..b' '..' ';' 'x;y' '$x' 'é' '*' '~' 'a|b' "a'b" 'a"b' '`x`' '\' '(x)' '{x}' '&' '<' '>' '?' 'a,b' 'a#b' 'a%b' 'a!b'; do
  is_false "valid_arg rejects [$bad]" kbv_valid_arg "$bad"
done
is_false "valid_arg rejects an embedded newline" kbv_valid_arg "$(printf 'ok\n;rm')"
is_false "valid_arg rejects a trailing newline" kbv_valid_arg $'ok\n'

# ------------------------------------------------------------- inbox names --
echo "# kbv_valid_inbox_name / kbv_valid_inbox_file"
is_true "inbox stem simple" kbv_valid_inbox_name claims-abc123
is_true "inbox stem single char" kbv_valid_inbox_name a
is_true "inbox stem digit first" kbv_valid_inbox_name 1a
is_true "inbox stem 64 chars" kbv_valid_inbox_name "$(repeat a 64)"
is_false "inbox stem 65 chars" kbv_valid_inbox_name "$(repeat a 65)"
is_false "inbox stem leading hyphen" kbv_valid_inbox_name -abc
is_false "inbox stem uppercase" kbv_valid_inbox_name V1
is_false "inbox stem dot" kbv_valid_inbox_name a.b
is_false "inbox stem underscore" kbv_valid_inbox_name a_b
is_false "inbox stem slash" kbv_valid_inbox_name a/b
is_false "inbox stem empty" kbv_valid_inbox_name ''
is_true "inbox file" kbv_valid_inbox_file claims-abc.json
is_true "inbox file trailing hyphen stem" kbv_valid_inbox_file abc-.json
is_false "inbox file uppercase extension" kbv_valid_inbox_file V1.JSON
is_false "inbox file traversal" kbv_valid_inbox_file ../x.json
is_false "inbox file bare extension" kbv_valid_inbox_file .json
is_false "inbox file double extension" kbv_valid_inbox_file x.json.json
is_false "inbox file no extension" kbv_valid_inbox_file claims-abc
is_false "inbox file empty" kbv_valid_inbox_file ''

# ------------------------------------------------------------ triage names --
echo "# kbv_valid_triage_name"
is_true "triage ok" kbv_valid_triage_name 0001-refund-window-is-7-days.md
is_true "triage single word" kbv_valid_triage_name 0042-a.md
is_true "triage digits in slug" kbv_valid_triage_name 0001-7-days.md
is_true "triage 9999" kbv_valid_triage_name 9999-z9.md
is_false "triage short number" kbv_valid_triage_name 7-slug.md
is_false "triage five digits" kbv_valid_triage_name 00001-slug.md
is_false "triage trailing hyphen" kbv_valid_triage_name 0001-slug-.md
is_false "triage double hyphen" kbv_valid_triage_name 0001--slug.md
is_false "triage uppercase" kbv_valid_triage_name 0001-Slug.md
is_false "triage empty slug" kbv_valid_triage_name 0001-.md
is_false "triage wrong extension" kbv_valid_triage_name notas.txt
is_false "triage extension suffix" kbv_valid_triage_name 0001-slug.md.txt
is_false "triage no extension" kbv_valid_triage_name 0001-slug
is_false "triage underscore" kbv_valid_triage_name 0001-slug_x.md
is_false "triage accent" kbv_valid_triage_name 0001-ação.md
is_false "triage empty" kbv_valid_triage_name ''

# ------------------------------------------------------------------ sha256 --
echo "# kbv_sha256"
printf 'hello kb-verify\n' > "$T/f.txt"
: > "$T/empty"
eq "sha256 matches shasum -a 256" "$(shasum -a 256 "$T/f.txt" | awk '{print $1}')" "$(kbv_sha256 "$T/f.txt")"
eq "sha256 of empty file" e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 "$(kbv_sha256 "$T/empty")"
sha=$(kbv_sha256 "$T/f.txt"); eq "sha256 is 64 hex chars" 64 "${#sha}"
is_false "sha256 missing file" kbv_sha256 "$T/nope"
is_false "sha256 directory" kbv_sha256 "$T"
is_false "sha256 empty arg" kbv_sha256 ''

# -------------------------------------------------------------- resolve_jq --
echo "# kbv_resolve_jq"
is_true "resolve_jq returns an executable" test -x "$JQ"
eq "resolve_jq returns an absolute path" "/" "$(printf '%s' "$JQ" | cut -c1)"
jq_missing() { ( KB_VERIFY_JQ=/nonexistent/jq; kbv_resolve_jq ); }
jq_override() { ( KB_VERIFY_JQ="$JQ"; kbv_resolve_jq ); }
is_false "KB_VERIFY_JQ pointing nowhere -> not found" jq_missing
eq "KB_VERIFY_JQ override is echoed" "$JQ" "$(jq_override)"

# ---------------------------------------------------------------- envelope --
echo "# kbv_ok / kbv_err"
out=$(kbv_ok '{"a":1,"b":[1,2]}' 'hello "world"'); rc=$?
eq "kbv_ok returns 0" 0 "$rc"
eq "kbv_ok prints one line" 1 "$(lines "$out")"
is_true "kbv_ok shape and key order" jqcheck "$out" \
  '.ok == true and .code == "OK" and .data.a == 1 and .data.b == [1,2] and .msg == "hello \"world\"" and (has("retry_after") | not) and (keys_unsorted == ["ok","code","data","msg"])'
out=$(kbv_ok '' 'no data'); is_true "kbv_ok empty data becomes {}" jqcheck "$out" '.data == {} and .msg == "no data"'
out=$(kbv_ok '{}' "$(printf 'line1\nline2\ttab')")
eq "kbv_ok msg with newline stays one line" 1 "$(lines "$out")"
is_true "kbv_ok msg escapes preserved" jqcheck "$out" '.msg == "line1\nline2\ttab"'
rc_is "kbv_ok rejects invalid JSON data" 70 kbv_ok 'not json' x
rc_is "kbv_ok rejects non-object data" 70 kbv_ok '[1]' x
eq "kbv_ok invalid data prints nothing on stdout" '' "$(kbv_ok 'not json' x 2>/dev/null)"

out=$(kbv_err RATE_LIMITED 'slow down' 42); rc=$?
eq "kbv_err returns 0" 0 "$rc"
eq "kbv_err prints one line" 1 "$(lines "$out")"
is_true "kbv_err with retry_after shape and key order" jqcheck "$out" \
  '.ok == false and .code == "RATE_LIMITED" and .data == {} and .msg == "slow down" and .retry_after == 42 and (keys_unsorted == ["ok","code","data","msg","retry_after"])'
out=$(kbv_err NOT_FOUND 'nope')
is_true "kbv_err without retry_after omits the key" jqcheck "$out" '.ok == false and .code == "NOT_FOUND" and .data == {} and (has("retry_after") | not)'
for c in GH_AUTH RATE_LIMITED SEARCH_UNAVAILABLE NOT_FOUND BUDGET_EXHAUSTED DIFF_APPLY_FAILED INVALID_INPUT; do
  is_true "kbv_err accepts code $c" kbv_err "$c" m
done
rc_is "kbv_err rejects unknown code" 70 kbv_err BOGUS m
rc_is "kbv_err rejects OK" 70 kbv_err OK m
rc_is "kbv_err rejects empty code" 70 kbv_err '' m
rc_is "kbv_err rejects non-integer retry_after" 70 kbv_err RATE_LIMITED m soon
rc_is "kbv_err rejects negative retry_after" 70 kbv_err RATE_LIMITED m -5
eq "kbv_err unknown code prints nothing on stdout" '' "$(kbv_err BOGUS m 2>/dev/null)"
out=$(kbv_err INVALID_INPUT "bad arg: $(printf 'x;y\n"q"')")
eq "kbv_err msg with control chars stays one line" 1 "$(lines "$out")"
is_true "kbv_err msg with quotes valid" jqcheck "$out" '.msg == "bad arg: x;y\n\"q\""'

# ------------------------------------------------------------- deny/allow --
echo "# kbv_deny / kbv_allow"
out=$(kbv_deny 'token "x" \ y'); rc=$?
eq "kbv_deny exits 0" 0 "$rc"
eq "kbv_deny prints one line" 1 "$(lines "$out")"
is_true "kbv_deny shape" jqcheck "$out" \
  '.hookSpecificOutput.hookEventName == "PreToolUse" and .hookSpecificOutput.permissionDecision == "deny" and .hookSpecificOutput.permissionDecisionReason == "kb-verify: token \"x\" \\ y"'
out=$(kbv_deny "$(printf 'multi\nline\ttab\001ctl')")
is_true "kbv_deny flattens whitespace and drops other control characters" jqcheck "$out" '.hookSpecificOutput.permissionDecisionReason == "kb-verify: multi line tabctl"'
out=$(kbv_deny ''); is_true "kbv_deny with empty reason still prefixed" jqcheck "$out" '.hookSpecificOutput.permissionDecisionReason == "kb-verify: "'
deny_without_jq() { ( KB_VERIFY_JQ=/nonexistent/jq; kbv_deny 'no jq' ); }
is_true "kbv_deny works without jq" jqcheck "$(deny_without_jq)" '.hookSpecificOutput.permissionDecisionReason == "kb-verify: no jq"'
out=$(kbv_allow); rc=$?
eq "kbv_allow exits 0" 0 "$rc"
eq "kbv_allow prints nothing" '' "$out"

# ---------------------------------------------------------------- data_dir --
echo "# kbv_data_dir"
eq "data_dir defaults to HOME/.kb-verify" "$HOME/.kb-verify" "$(kbv_data_dir)"
eq "data_dir uses CLAUDE_PLUGIN_DATA (trailing slash stripped)" "$T/pd" "$( CLAUDE_PLUGIN_DATA="$T/pd/"; kbv_data_dir )"
eq "data_dir prefers KB_VERIFY_DATA_DIR" "$T/dd" "$( KB_VERIFY_DATA_DIR="$T/dd"; CLAUDE_PLUGIN_DATA="$T/pd"; kbv_data_dir )"
no_home_data_dir() { ( HOME=''; kbv_data_dir ); }
is_false "data_dir fails with empty HOME and no override" no_home_data_dir

# ---------------------------------------------------------- field_for_tool --
echo "# kbv_field_for_tool"
eq "Write -> file_path" file_path "$(kbv_field_for_tool Write)"
eq "Edit -> file_path" file_path "$(kbv_field_for_tool Edit)"
eq "MultiEdit -> file_path" file_path "$(kbv_field_for_tool MultiEdit)"
eq "NotebookEdit -> notebook_path" notebook_path "$(kbv_field_for_tool NotebookEdit)"
eq "Bash -> command" command "$(kbv_field_for_tool Bash)"
eq "Read -> file_path then path" "$(printf 'file_path\npath')" "$(kbv_field_for_tool Read)"
eq "Grep -> path" path "$(kbv_field_for_tool Grep)"
eq "Glob -> pattern then path" "$(printf 'pattern\npath')" "$(kbv_field_for_tool Glob)"
is_false "unknown tool" kbv_field_for_tool WebFetch
is_false "empty tool" kbv_field_for_tool ''

# ------------------------------------------------------------ name_exists --
echo "# kbv_name_exists"
mkdir -p "$T/names"
: > "$T/names/cancelar-assinatura.md"
: > "$T/names/.hidden.md"
ln -s /nonexistent/target "$T/names/dangling.md" 2>/dev/null
is_true "exact name found" kbv_name_exists "$T/names" cancelar-assinatura.md
is_true "hidden entry found" kbv_name_exists "$T/names" .hidden.md
is_true "dangling symlink counts as an entry" kbv_name_exists "$T/names" dangling.md
is_false "differently cased name not found" kbv_name_exists "$T/names" CANCELAR-ASSINATURA.md
is_false "missing name" kbv_name_exists "$T/names" nope.md
is_false "not a directory" kbv_name_exists "$T/names/cancelar-assinatura.md" x
is_false "empty arguments" kbv_name_exists '' ''

# ------------------------------------------------------------------ config --
echo "# kbv_find_config / kbv_is_armed / kbv_load_config"
mkdir -p "$T/kb2/articles/deep/er" "$T/elsewhere"
cat > "$T/kb2/kb-verify.config.json" <<'EOF'
{"version": 1,
 "kb_root": ".", "articles_dir": "articles", "triage_dir": "kb-verify/triage/bugs",
 "gh": {"repo": "org/monorepo"},
 "budgets": {"search_calls_per_article": 15, "fetch_calls_per_article": 40, "index_i18n_files": 20},
 "integration": {"article_glob": "articles/**/*.md", "locales": ["en", "pt-BR"]}}
EOF
eq "find_config walks up from a nested dir" "$TR/kb2/kb-verify.config.json" "$(kbv_find_config "$T/kb2/articles/deep/er")"
eq "find_config finds it in the start dir" "$TR/kb2/kb-verify.config.json" "$(kbv_find_config "$T/kb2")"
eq "find_config from a relative start dir" "$TR/kb2/kb-verify.config.json" "$(cd "$T/kb2/articles" && kbv_find_config deep)"
is_false "find_config outside the kb" kbv_find_config "$T/elsewhere"
is_false "find_config nonexistent start dir" kbv_find_config "$T/nope"
is_false "find_config empty start dir" kbv_find_config ''
is_true "is_armed inside the kb" kbv_is_armed "$T/kb2/articles"
is_false "is_armed outside the kb" kbv_is_armed "$T/elsewhere"
eq "KB_VERIFY_CONFIG overrides the walk" "/x/y.json" "$( KB_VERIFY_CONFIG=/x/y.json; kbv_find_config "$T/elsewhere" )"
armed_by_env() { ( KB_VERIFY_CONFIG=/x/y.json; kbv_is_armed "$T/elsewhere" ); }
is_true "KB_VERIFY_CONFIG arms even when the file is missing" armed_by_env

is_true "load_config accepts a valid config" kbv_load_config "$T/kb2/kb-verify.config.json"
eq "KBV_KB_ROOT is absolute physical" "$TR/kb2" "$KBV_KB_ROOT"
eq "KBV_ARTICLES_DIR is under kb_root" "$TR/kb2/articles" "$KBV_ARTICLES_DIR"
eq "KBV_TRIAGE_DIR is under kb_root (may not exist yet)" "$TR/kb2/kb-verify/triage/bugs" "$KBV_TRIAGE_DIR"
eq "KBV_GH_REPO as written" org/monorepo "$KBV_GH_REPO"
eq "KBV_CONFIG_PATH is absolute" "$TR/kb2/kb-verify.config.json" "$KBV_CONFIG_PATH"
eq "KBV_CONFIG_JSON is one line" 1 "$(lines "$KBV_CONFIG_JSON")"
is_true "KBV_CONFIG_JSON keeps budgets and integration" jqcheck "$KBV_CONFIG_JSON" '.budgets.fetch_calls_per_article == 40 and .integration.locales == ["en","pt-BR"]'
eq "KBV_CONFIG_ERROR is empty after success" '' "$KBV_CONFIG_ERROR"
is_true "exports reach child processes" sh -c '[ -n "$KBV_KB_ROOT" ] && [ -n "$KBV_ARTICLES_DIR" ] && [ -n "$KBV_TRIAGE_DIR" ] && [ -n "$KBV_GH_REPO" ] && [ -n "$KBV_CONFIG_JSON" ] && [ -n "$KBV_CONFIG_PATH" ]'

# Config fixtures are written with printf formats on purpose: bash 3.2
# mis-parses backslash-escaped quotes inside "$( ... )" and brace-expands the
# JSON literal into several arguments.
# cfg <kb_root> <articles_dir> <triage_dir> <repo> -> writes $T/cfg.json with the four required keys
cfg() { printf '{"kb_root":"%s","articles_dir":"%s","triage_dir":"%s","gh":{"repo":"%s"}}' "$1" "$2" "$3" "$4" > "$T/cfg.json"; }
# cfg_fmt <printf-format> [args...] -> writes $T/cfg.json
cfg_fmt() { local f="$1"; shift; printf "$f" "$@" > "$T/cfg.json"; }
# load_err -> prints KBV_CONFIG_ERROR after a failed load of $T/cfg.json, LOADED on success
load_err() { if kbv_load_config "$T/cfg.json"; then printf 'LOADED'; else printf '%s' "$KBV_CONFIG_ERROR"; fi; }
mkdir -p "$T/home/kb3/docs" "$T/abs-kb/content"
KB2="$T/kb2"

cfg "$T/abs-kb" "$T/abs-kb/content" "$T/abs-kb/triage" o/r
eq "absolute kb_root and absolute dirs" LOADED "$(load_err)"
eq "absolute articles_dir kept absolute" "$TR/abs-kb/content" "$( load_err >/dev/null; printf '%s' "$KBV_ARTICLES_DIR" )"
eq "absolute triage_dir kept absolute" "$TR/abs-kb/triage" "$( load_err >/dev/null; printf '%s' "$KBV_TRIAGE_DIR" )"
cfg '~/kb3' docs t o/r
eq "tilde kb_root resolves against HOME" "$TR/home/kb3" "$( load_err >/dev/null; printf '%s' "$KBV_KB_ROOT" )"
cfg kb2 a t o/r
eq "relative kb_root resolves against the config dir" "$TR/kb2" "$( load_err >/dev/null; printf '%s' "$KBV_KB_ROOT" )"
cfg_fmt '{"kb_root":"../kb2","articles_dir":"a","triage_dir":"t","gh":{"repo":"o/r"}}'
mkdir -p "$T/sub" && cp "$T/cfg.json" "$T/sub/kb-verify.config.json"
eq "dot-dot kb_root resolves against the config dir" "$TR/kb2" "$( kbv_load_config "$T/sub/kb-verify.config.json" >/dev/null; printf '%s' "$KBV_KB_ROOT" )"
eq "missing file -> file" file "$( kbv_load_config "$T/nope.json"; printf '%s' "$KBV_CONFIG_ERROR" )"
eq "empty path -> file" file "$( kbv_load_config ''; printf '%s' "$KBV_CONFIG_ERROR" )"
cfg_fmt 'not json';                                                       eq "invalid JSON -> json" json "$(load_err)"
cfg_fmt '[1,2]';                                                          eq "JSON array -> json" json "$(load_err)"
cfg_fmt '{"articles_dir":"a","triage_dir":"t","gh":{"repo":"o/r"}}';      eq "missing kb_root -> kb_root" kb_root "$(load_err)"
cfg_fmt '{"kb_root":5,"articles_dir":"a","triage_dir":"t","gh":{"repo":"o/r"}}'; eq "numeric kb_root -> kb_root" kb_root "$(load_err)"
cfg '' a t o/r;                                                           eq "empty kb_root -> kb_root" kb_root "$(load_err)"
cfg /nonexistent/kbv-root a t o/r;                                        eq "nonexistent kb_root -> kb_root" kb_root "$(load_err)"
cfg "$T/f.txt" a t o/r;                                                   eq "kb_root that is a file -> kb_root" kb_root "$(load_err)"
cfg_fmt '{"kb_root":"%s","triage_dir":"t","gh":{"repo":"o/r"}}' "$KB2";   eq "missing articles_dir -> articles_dir" articles_dir "$(load_err)"
cfg_fmt '{"kb_root":"%s","articles_dir":"a","gh":{"repo":"o/r"}}' "$KB2"; eq "missing triage_dir -> triage_dir" triage_dir "$(load_err)"
cfg_fmt '{"kb_root":"%s","articles_dir":"a","triage_dir":"t"}' "$KB2";    eq "missing gh -> gh.repo" gh.repo "$(load_err)"
cfg_fmt '{"kb_root":"%s","articles_dir":"a","triage_dir":"t","gh":{"repo":7}}' "$KB2"; eq "numeric gh.repo -> gh.repo" gh.repo "$(load_err)"
cfg "$KB2" a t monorepo;                                                  eq "gh.repo without slash -> gh.repo" gh.repo "$(load_err)"
cfg "$KB2" a t a/b/c;                                                     eq "gh.repo with extra slash -> gh.repo" gh.repo "$(load_err)"
cfg "$KB2" a t ../r;                                                      eq "gh.repo with dot-dot -> gh.repo" gh.repo "$(load_err)"
cfg "$KB2" a t 'o/r x';                                                   eq "gh.repo with space -> gh.repo" gh.repo "$(load_err)"
cfg "$KB2" nope/../a t o/r;                                               eq "articles_dir escaping through a non-existing dir -> articles_dir" articles_dir "$(load_err)"
cfg "$KB2" a nope/../t o/r;                                               eq "triage_dir escaping through a non-existing dir -> triage_dir" triage_dir "$(load_err)"
cfg "$KB2" a t o/r;                                                       eq "jq unavailable -> jq" jq "$( KB_VERIFY_JQ=/nonexistent/jq; load_err )"
eq "valid config after failures still loads" LOADED "$(load_err)"

# ----------------------------------------------------------------- summary --
printf '1..%d\n' "$N"
if [ "$FAILS" -eq 0 ]; then
  printf '# all %d tests passed (bash %s)\n' "$N" "$BASH_VERSION"
  exit 0
fi
printf '# %d of %d tests FAILED (bash %s)\n' "$FAILS" "$N" "$BASH_VERSION"
exit 1
