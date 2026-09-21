# kb-verify -- lib/common.sh
#
# Shared helpers sourced by hooks/*.sh and scripts/kbv.sh.
#
# Conventions
#   - bash 3.2 clean: no associative arrays, no mapfile, no ${var,,},
#     no [[ =~ ]]. Character-set checks use `case` with spelled-out ASCII
#     classes so they are locale-proof and newline-proof.
#   - Sourcing this file has no side effects beyond defining constants and
#     functions. It never sets -e/-u/pipefail; every function is written to
#     run correctly under `set -eEuo pipefail` in the caller.
#   - Text tools (sed, tr, cut) run with LC_ALL=C so that BSD sed never
#     aborts on bytes that are not valid UTF-8.
#   - Only kbv_deny and kbv_allow exit; everything else returns.
#   - Return code 70 (EX_SOFTWARE) marks misuse by the caller, i.e. a
#     script bug, never a handled failure.
#
# External commands used: jq (resolved via kbv_resolve_jq), realpath,
# shasum, sed, tr, cut, dirname, basename.

KBV_CONFIG_NAME='kb-verify.config.json'
KBV_JQ_CANDIDATES='/opt/homebrew/bin/jq /usr/local/bin/jq /opt/anaconda3/bin/jq'
KBV_ASCII_LOWER='abcdefghijklmnopqrstuvwxyz'
KBV_ASCII_UPPER='ABCDEFGHIJKLMNOPQRSTUVWXYZ'
KBV_DIGITS='0123456789'
KBV_ASCII_ALNUM="${KBV_ASCII_LOWER}${KBV_ASCII_UPPER}${KBV_DIGITS}"
# Envelope codes accepted by kbv_err (OK is reserved for kbv_ok).
KBV_ERR_CODES='GH_AUTH RATE_LIMITED SEARCH_UNAVAILABLE NOT_FOUND BUDGET_EXHAUSTED DIFF_APPLY_FAILED INVALID_INPUT'
# Set by kbv_load_config on failure: names the offending piece.
KBV_CONFIG_ERROR=''

# ---------------------------------------------------------------------------
# kbv_lib_diag <message>
#   Internal. Writes a diagnostic to stderr with the kb-verify prefix.
#   stdout: nothing. Returns 0.
# ---------------------------------------------------------------------------
kbv_lib_diag() {
  printf 'kb-verify: %s\n' "${1:-}" >&2
  return 0
}

# ---------------------------------------------------------------------------
# kbv_data_dir
#   Inputs: env KB_VERIFY_DATA_DIR, CLAUDE_PLUGIN_DATA, HOME (in that order).
#   stdout: the data directory, without trailing slash. Nothing is created.
#   Returns 0; 1 when no variable is set and HOME is empty.
# ---------------------------------------------------------------------------
kbv_data_dir() {
  local d="${KB_VERIFY_DATA_DIR:-${CLAUDE_PLUGIN_DATA:-}}"
  if [ -z "$d" ]; then
    [ -n "${HOME:-}" ] || return 1
    d="$HOME/.kb-verify"
  fi
  [ "$d" = "/" ] || d="${d%/}"
  printf '%s\n' "$d"
}

# ---------------------------------------------------------------------------
# kbv_resolve_jq
#   Inputs: env KB_VERIFY_JQ (test-only override: when set, it is the only
#   candidate). Otherwise tries /opt/homebrew/bin/jq, /usr/local/bin/jq,
#   /opt/anaconda3/bin/jq, then `command -v jq` (hooks do not inherit the
#   user's PATH).
#   stdout: absolute path of an executable jq. Returns 0; 1 when none found.
# ---------------------------------------------------------------------------
kbv_resolve_jq() {
  local c
  if [ -n "${KB_VERIFY_JQ:-}" ]; then
    if [ -x "$KB_VERIFY_JQ" ] && [ ! -d "$KB_VERIFY_JQ" ]; then
      printf '%s\n' "$KB_VERIFY_JQ"
      return 0
    fi
    return 1
  fi
  for c in $KBV_JQ_CANDIDATES; do
    if [ -x "$c" ] && [ ! -d "$c" ]; then
      printf '%s\n' "$c"
      return 0
    fi
  done
  c=$(command -v jq 2>/dev/null) || return 1
  if [ -n "$c" ] && [ -x "$c" ]; then
    printf '%s\n' "$c"
    return 0
  fi
  return 1
}

# ---------------------------------------------------------------------------
# kbv_find_config <start_dir>
#   Inputs: env KB_VERIFY_CONFIG (tests and CI) takes precedence: when set and
#   non-empty it is echoed as-is, even if the file is missing, so that
#   kbv_load_config can fail closed. Otherwise walks up from <start_dir>
#   (physical path) looking for kb-verify.config.json.
#   stdout: path of the config file. Returns 0; 1 when not found or
#   <start_dir> is empty / not a directory.
# ---------------------------------------------------------------------------
kbv_find_config() {
  local start="${1:-}" dir
  if [ -n "${KB_VERIFY_CONFIG:-}" ]; then
    printf '%s\n' "$KB_VERIFY_CONFIG"
    return 0
  fi
  [ -n "$start" ] || return 1
  dir=$(unset CDPATH; cd -- "$start" 2>/dev/null && pwd -P) || return 1
  while :; do
    if [ -f "$dir/$KBV_CONFIG_NAME" ]; then
      printf '%s\n' "$dir/$KBV_CONFIG_NAME"
      return 0
    fi
    [ "$dir" != "/" ] || return 1
    dir=$(dirname -- "$dir")
  done
}

# ---------------------------------------------------------------------------
# kbv_is_armed <start_dir>
#   Thin wrapper: returns 0 when kbv_find_config finds a config (the guard is
#   armed), 1 otherwise. stdout: nothing.
# ---------------------------------------------------------------------------
kbv_is_armed() {
  kbv_find_config "${1:-}" >/dev/null 2>&1
}

# ---------------------------------------------------------------------------
# kbv_config_string <jq> <file> <jq_path>
#   Internal. stdout: the value at <jq_path> when it is a non-empty,
#   single-line string. Returns 0; 1 otherwise.
# ---------------------------------------------------------------------------
kbv_config_string() {
  local jq="$1" file="$2" expr="$3" out
  out=$("$jq" -e -r "$expr | if type == \"string\" and length > 0 then . else empty end" "$file" 2>/dev/null) || return 1
  [ -n "$out" ] || return 1
  case "$out" in *$'\n'*) return 1 ;; esac
  printf '%s\n' "$out"
}

# ---------------------------------------------------------------------------
# kbv_valid_gh_repo <s>
#   Internal. Returns 0 when <s> looks like org/repo with both halves in
#   [A-Za-z0-9_.-], non-empty and not "." or "..". stdout: nothing.
# ---------------------------------------------------------------------------
kbv_valid_gh_repo() {
  local s="${1:-}" org name
  case "$s" in */*) ;; *) return 1 ;; esac
  org="${s%%/*}"
  name="${s#*/}"
  [ -n "$org" ] && [ -n "$name" ] || return 1
  case "$name" in */*) return 1 ;; esac
  case "$org" in .|..) return 1 ;; esac
  case "$name" in .|..) return 1 ;; esac
  case "$org" in *[!${KBV_ASCII_ALNUM}_.-]*) return 1 ;; esac
  case "$name" in *[!${KBV_ASCII_ALNUM}_.-]*) return 1 ;; esac
  return 0
}

# ---------------------------------------------------------------------------
# kbv_load_config <path>
#   Inputs: path of kb-verify.config.json.
#   Exports on success:
#     KBV_KB_ROOT      absolute physical path; must be an existing directory
#                      (relative or ~ values resolve against the config dir)
#     KBV_ARTICLES_DIR absolute path: <kb_root>/<articles_dir> unless absolute
#     KBV_TRIAGE_DIR   absolute path: <kb_root>/<triage_dir> unless absolute
#     KBV_GH_REPO      "org/repo" as written
#     KBV_CONFIG_JSON  the whole config as compact JSON (budgets, integration)
#     KBV_CONFIG_PATH  absolute path of the config file itself
#   stdout: nothing. Returns 0; 1 when the file is missing/unreadable, jq is
#   unavailable, the JSON is not an object, a required key (kb_root,
#   articles_dir, triage_dir, gh.repo) is missing or not a non-empty string,
#   kb_root is not an existing directory, or gh.repo is malformed. On failure
#   KBV_CONFIG_ERROR names the piece: file|jq|json|kb_root|articles_dir|
#   triage_dir|gh.repo.
# ---------------------------------------------------------------------------
kbv_load_config() {
  local path="${1:-}" jq cfgdir root articles triage repo json
  KBV_CONFIG_ERROR=''
  if [ -z "$path" ] || [ ! -f "$path" ] || [ ! -r "$path" ]; then
    KBV_CONFIG_ERROR='file'
    return 1
  fi
  jq=$(kbv_resolve_jq) || { KBV_CONFIG_ERROR='jq'; return 1; }
  if ! "$jq" -e 'type == "object"' "$path" >/dev/null 2>&1; then
    KBV_CONFIG_ERROR='json'
    return 1
  fi
  root=$(kbv_config_string "$jq" "$path" '.kb_root') || { KBV_CONFIG_ERROR='kb_root'; return 1; }
  articles=$(kbv_config_string "$jq" "$path" '.articles_dir') || { KBV_CONFIG_ERROR='articles_dir'; return 1; }
  triage=$(kbv_config_string "$jq" "$path" '.triage_dir') || { KBV_CONFIG_ERROR='triage_dir'; return 1; }
  repo=$(kbv_config_string "$jq" "$path" '.gh.repo') || { KBV_CONFIG_ERROR='gh.repo'; return 1; }
  kbv_valid_gh_repo "$repo" || { KBV_CONFIG_ERROR='gh.repo'; return 1; }

  cfgdir=$(unset CDPATH; cd -- "$(dirname -- "$path")" 2>/dev/null && pwd -P) || { KBV_CONFIG_ERROR='file'; return 1; }
  root=$(kbv_normalize_path "$root" "$cfgdir") || { KBV_CONFIG_ERROR='kb_root'; return 1; }
  [ -d "$root" ] || { KBV_CONFIG_ERROR='kb_root'; return 1; }
  articles=$(kbv_normalize_path "$articles" "$root") || { KBV_CONFIG_ERROR='articles_dir'; return 1; }
  triage=$(kbv_normalize_path "$triage" "$root") || { KBV_CONFIG_ERROR='triage_dir'; return 1; }
  json=$("$jq" -c . "$path" 2>/dev/null) || { KBV_CONFIG_ERROR='json'; return 1; }

  KBV_KB_ROOT="$root"
  KBV_ARTICLES_DIR="$articles"
  KBV_TRIAGE_DIR="$triage"
  KBV_GH_REPO="$repo"
  KBV_CONFIG_JSON="$json"
  KBV_CONFIG_PATH="$cfgdir/$(basename -- "$path")"
  export KBV_KB_ROOT KBV_ARTICLES_DIR KBV_TRIAGE_DIR KBV_GH_REPO KBV_CONFIG_JSON KBV_CONFIG_PATH
  return 0
}

# ---------------------------------------------------------------------------
# kbv_field_for_tool <tool_name>
#   stdout: the tool_input field(s) the guard inspects, one per line:
#     Write|Edit|MultiEdit -> file_path      NotebookEdit -> notebook_path
#     Bash -> command                        Read -> file_path, then path
#     Grep -> path                           Glob -> pattern, then path
#   Read is the one tool that sends file_path in practice while the design
#   doc names path, so the guard checks both and so does this helper.
#   Returns 0; 1 for any other tool (nothing printed).
# ---------------------------------------------------------------------------
kbv_field_for_tool() {
  case "${1:-}" in
    Write|Edit|MultiEdit) printf 'file_path\n' ;;
    NotebookEdit) printf 'notebook_path\n' ;;
    Bash) printf 'command\n' ;;
    Read) printf 'file_path\npath\n' ;;
    Grep) printf 'path\n' ;;
    Glob) printf 'pattern\npath\n' ;;
    *) return 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# kbv_name_exists <dir> <name>
#   Returns 0 when <dir> holds an entry named exactly <name>, comparing bytes,
#   so a case-insensitive volume cannot satisfy the check with a differently
#   cased file. Symlinks count as entries (their own name is what matters).
#   stdout: nothing. Returns 1 when <dir> is not a directory, either argument
#   is empty, or no entry carries that name.
# ---------------------------------------------------------------------------
kbv_name_exists() {
  local dir="${1:-}" name="${2:-}" entry
  [ -n "$dir" ] && [ -n "$name" ] || return 1
  [ -d "$dir" ] || return 1
  for entry in "$dir"/* "$dir"/.*; do
    [ -e "$entry" ] || [ -L "$entry" ] || continue
    [ "${entry##*/}" = "$name" ] || continue
    return 0
  done
  return 1
}

# ---------------------------------------------------------------------------
# kbv_normalize_path <path> <cwd>
#   Inputs: <path> may be absolute, relative (joined with <cwd>), "~" or
#   "~/..." (expanded with HOME). <cwd> must be absolute; empty falls back to
#   $PWD. Other "~user" forms are not expanded.
#   Algorithm: walk the segments; "." and empty segments are dropped; the
#   longest existing prefix is resolved with `realpath` (symlinks followed,
#   ".." resolved physically); the non-existing rest is re-appended verbatim.
#   stdout: the absolute normalized path. Returns 0;
#     1 when <path> is empty, <cwd> is not absolute, HOME is needed but empty,
#       or a ".." segment remains in the non-existing rest;
#     2 when realpath is unavailable or fails on the existing prefix;
#     3 when a segment is a dangling symlink (fail closed: writing through it
#       would create the link target).
# ---------------------------------------------------------------------------
kbv_normalize_path() {
  local path="${1:-}" cwd="${2:-}" abs remaining seg candidate prefix rest resolved
  local finished=0 in_rest=0
  [ -n "$path" ] || return 1
  [ -n "$cwd" ] || cwd="$PWD"
  case "$cwd" in /*) ;; *) return 1 ;; esac
  case "$path" in
    '~')
      [ -n "${HOME:-}" ] || return 1
      path="$HOME"
      ;;
    '~/'*)
      [ -n "${HOME:-}" ] || return 1
      path="$HOME/${path#\~/}"
      ;;
  esac
  case "$path" in
    /*) abs="$path" ;;
    *) abs="$cwd/$path" ;;
  esac
  command -v realpath >/dev/null 2>&1 || return 2

  prefix='/'
  rest=''
  remaining="${abs#/}"
  while [ "$finished" -eq 0 ]; do
    case "$remaining" in
      */*)
        seg="${remaining%%/*}"
        remaining="${remaining#*/}"
        ;;
      *)
        seg="$remaining"
        remaining=''
        finished=1
        ;;
    esac
    case "$seg" in ''|'.') continue ;; esac
    if [ "$in_rest" -eq 1 ]; then
      [ "$seg" != '..' ] || return 1
      rest="${rest:+$rest/}$seg"
      continue
    fi
    if [ "$prefix" = '/' ]; then candidate="/$seg"; else candidate="$prefix/$seg"; fi
    if [ -L "$candidate" ] && [ ! -e "$candidate" ]; then
      return 3
    fi
    if [ -e "$candidate" ]; then
      prefix="$candidate"
    else
      in_rest=1
      [ "$seg" != '..' ] || return 1
      rest="$seg"
    fi
  done

  resolved=$(realpath "$prefix" 2>/dev/null) || return 2
  [ -n "$resolved" ] || return 2
  if [ -z "$rest" ]; then
    printf '%s\n' "$resolved"
  elif [ "$resolved" = '/' ]; then
    printf '/%s\n' "$rest"
  else
    printf '%s/%s\n' "$resolved" "$rest"
  fi
}

# ---------------------------------------------------------------------------
# kbv_under <path> <root>
#   Inputs: two absolute paths (normalize both first). Trailing slashes on
#   <root> are ignored; root "/" contains every absolute path.
#   stdout: nothing. Returns 0 when <path> equals <root> or lies below it
#   (segment-wise, so /kb/articles2 is not under /kb/articles); 1 otherwise
#   or when either argument is empty.
# ---------------------------------------------------------------------------
kbv_under() {
  local path="${1:-}" root="${2:-}"
  [ -n "$path" ] && [ -n "$root" ] || return 1
  while [ "${#root}" -gt 1 ]; do
    case "$root" in
      */) root="${root%/}" ;;
      *) break ;;
    esac
  done
  if [ "$root" = '/' ]; then
    case "$path" in /*) return 0 ;; *) return 1 ;; esac
  fi
  if [ "$path" = "$root" ]; then
    return 0
  fi
  case "$path" in
    "$root"/*) return 0 ;;
  esac
  return 1
}

# ---------------------------------------------------------------------------
# kbv_valid_arg <s>
#   Script-argument charset: ^[A-Za-z0-9_./:@=-]+$ and no "..".
#   stdout: nothing. Returns 0 when valid; 1 otherwise (empty included).
# ---------------------------------------------------------------------------
kbv_valid_arg() {
  local s="${1:-}"
  [ -n "$s" ] || return 1
  case "$s" in *..*) return 1 ;; esac
  case "$s" in *[!${KBV_ASCII_ALNUM}_./:@=-]*) return 1 ;; esac
  return 0
}

# ---------------------------------------------------------------------------
# kbv_valid_inbox_name <s>
#   Inbox file STEM (no extension): ^[a-z0-9][a-z0-9-]{0,63}$.
#   stdout: nothing. Returns 0 when valid; 1 otherwise.
# ---------------------------------------------------------------------------
kbv_valid_inbox_name() {
  local s="${1:-}"
  [ -n "$s" ] || return 1
  case "$s" in [!${KBV_ASCII_LOWER}${KBV_DIGITS}]*) return 1 ;; esac
  case "$s" in *[!${KBV_ASCII_LOWER}${KBV_DIGITS}-]*) return 1 ;; esac
  [ "${#s}" -le 64 ] || return 1
  return 0
}

# ---------------------------------------------------------------------------
# kbv_valid_inbox_file <s>
#   Inbox file NAME: <stem>.json where <stem> passes kbv_valid_inbox_name.
#   The extension must be exactly ".json" (lowercase).
#   stdout: nothing. Returns 0 when valid; 1 otherwise.
# ---------------------------------------------------------------------------
kbv_valid_inbox_file() {
  local s="${1:-}"
  case "$s" in
    *.json) kbv_valid_inbox_name "${s%.json}" ;;
    *) return 1 ;;
  esac
}

# ---------------------------------------------------------------------------
# kbv_valid_triage_name <s>
#   Triage file NAME: ^[0-9]{4}-[a-z0-9]+(-[a-z0-9]+)*\.md$.
#   stdout: nothing. Returns 0 when valid; 1 otherwise.
# ---------------------------------------------------------------------------
kbv_valid_triage_name() {
  local s="${1:-}" stem body
  case "$s" in
    *.md) stem="${s%.md}" ;;
    *) return 1 ;;
  esac
  case "$stem" in
    [${KBV_DIGITS}][${KBV_DIGITS}][${KBV_DIGITS}][${KBV_DIGITS}]-*) body="${stem#?????}" ;;
    *) return 1 ;;
  esac
  [ -n "$body" ] || return 1
  case "$body" in *[!${KBV_ASCII_LOWER}${KBV_DIGITS}-]*) return 1 ;; esac
  case "$body" in -*|*-|*--*) return 1 ;; esac
  return 0
}

# ---------------------------------------------------------------------------
# kbv_sha256 <file>
#   stdout: lowercase hex sha256 of <file> via `shasum -a 256` (macOS has no
#   sha256sum). Returns 0; 1 when the file is missing/unreadable or shasum
#   fails.
# ---------------------------------------------------------------------------
kbv_sha256() {
  local f="${1:-}" out
  if [ -z "$f" ] || [ ! -f "$f" ] || [ ! -r "$f" ]; then
    return 1
  fi
  out=$(shasum -a 256 < "$f") || return 1
  out="${out%% *}"
  [ -n "$out" ] || return 1
  printf '%s\n' "$out"
}

# ---------------------------------------------------------------------------
# kbv_translit_script
#   Internal. stdout: the sed script used by kbv_slugify. One `s` command per
#   precomposed character (bracket expressions would match single bytes under
#   LC_ALL=C). Covers Latin-1 Supplement and Latin Extended-A plus Romanian
#   s/t-comma. The two trailing byte-range commands remove combining
#   diacritical marks (NFD input, U+0300..U+036F). Kept in a function because
#   bash 3.2 cannot parse a heredoc with unbalanced quotes inside $(...).
#   Returns 0.
# ---------------------------------------------------------------------------
kbv_translit_script() {
  cat <<'EOF'
s/À/a/g;s/Á/a/g;s/Â/a/g;s/Ã/a/g;s/Ä/a/g;s/Å/a/g;s/Ā/a/g;s/Ă/a/g;s/Ą/a/g
s/à/a/g;s/á/a/g;s/â/a/g;s/ã/a/g;s/ä/a/g;s/å/a/g;s/ā/a/g;s/ă/a/g;s/ą/a/g
s/Æ/ae/g;s/æ/ae/g
s/Ç/c/g;s/Ć/c/g;s/Ĉ/c/g;s/Ċ/c/g;s/Č/c/g
s/ç/c/g;s/ć/c/g;s/ĉ/c/g;s/ċ/c/g;s/č/c/g
s/Ð/d/g;s/Ď/d/g;s/Đ/d/g;s/ð/d/g;s/ď/d/g;s/đ/d/g
s/È/e/g;s/É/e/g;s/Ê/e/g;s/Ë/e/g;s/Ē/e/g;s/Ĕ/e/g;s/Ė/e/g;s/Ę/e/g;s/Ě/e/g
s/è/e/g;s/é/e/g;s/ê/e/g;s/ë/e/g;s/ē/e/g;s/ĕ/e/g;s/ė/e/g;s/ę/e/g;s/ě/e/g
s/Ĝ/g/g;s/Ğ/g/g;s/Ġ/g/g;s/Ģ/g/g;s/ĝ/g/g;s/ğ/g/g;s/ġ/g/g;s/ģ/g/g
s/Ĥ/h/g;s/Ħ/h/g;s/ĥ/h/g;s/ħ/h/g
s/Ì/i/g;s/Í/i/g;s/Î/i/g;s/Ï/i/g;s/Ĩ/i/g;s/Ī/i/g;s/Ĭ/i/g;s/Į/i/g;s/İ/i/g
s/ì/i/g;s/í/i/g;s/î/i/g;s/ï/i/g;s/ĩ/i/g;s/ī/i/g;s/ĭ/i/g;s/į/i/g;s/ı/i/g
s/Ĳ/ij/g;s/ĳ/ij/g;s/Ĵ/j/g;s/ĵ/j/g;s/Ķ/k/g;s/ķ/k/g
s/Ĺ/l/g;s/Ļ/l/g;s/Ľ/l/g;s/Ŀ/l/g;s/Ł/l/g;s/ĺ/l/g;s/ļ/l/g;s/ľ/l/g;s/ŀ/l/g;s/ł/l/g
s/Ñ/n/g;s/Ń/n/g;s/Ņ/n/g;s/Ň/n/g;s/ñ/n/g;s/ń/n/g;s/ņ/n/g;s/ň/n/g
s/Ò/o/g;s/Ó/o/g;s/Ô/o/g;s/Õ/o/g;s/Ö/o/g;s/Ø/o/g;s/Ō/o/g;s/Ŏ/o/g;s/Ő/o/g
s/ò/o/g;s/ó/o/g;s/ô/o/g;s/õ/o/g;s/ö/o/g;s/ø/o/g;s/ō/o/g;s/ŏ/o/g;s/ő/o/g
s/Œ/oe/g;s/œ/oe/g
s/Ŕ/r/g;s/Ŗ/r/g;s/Ř/r/g;s/ŕ/r/g;s/ŗ/r/g;s/ř/r/g
s/Ś/s/g;s/Ŝ/s/g;s/Ş/s/g;s/Š/s/g;s/Ș/s/g;s/ś/s/g;s/ŝ/s/g;s/ş/s/g;s/š/s/g;s/ș/s/g;s/ß/ss/g
s/Ţ/t/g;s/Ť/t/g;s/Ŧ/t/g;s/Ț/t/g;s/ţ/t/g;s/ť/t/g;s/ŧ/t/g;s/ț/t/g;s/Þ/th/g;s/þ/th/g
s/Ù/u/g;s/Ú/u/g;s/Û/u/g;s/Ü/u/g;s/Ũ/u/g;s/Ū/u/g;s/Ŭ/u/g;s/Ů/u/g;s/Ű/u/g;s/Ų/u/g
s/ù/u/g;s/ú/u/g;s/û/u/g;s/ü/u/g;s/ũ/u/g;s/ū/u/g;s/ŭ/u/g;s/ů/u/g;s/ű/u/g;s/ų/u/g
s/Ŵ/w/g;s/ŵ/w/g
s/Ý/y/g;s/Ÿ/y/g;s/Ŷ/y/g;s/ý/y/g;s/ÿ/y/g;s/ŷ/y/g
s/Ź/z/g;s/Ż/z/g;s/Ž/z/g;s/ź/z/g;s/ż/z/g;s/ž/z/g
EOF
  # U+0300..U+033F = CC 80..CC BF ; U+0340..U+036F = CD 80..CD AF (raw bytes
  # via printf octal escapes because BSD sed has no \xHH escapes).
  printf 's/\314[\200-\277]//g\n'
  printf 's/\315[\200-\257]//g\n'
}

# ---------------------------------------------------------------------------
# kbv_slugify <string>
#   Steps: newlines/tabs to spaces; strip accents (table above, NFD marks
#   dropped); ASCII lowercase; every other byte (including leftover
#   non-Latin characters) becomes "-"; runs of "-" collapse; leading and
#   trailing "-" trimmed; cut to 60 characters; trailing "-" trimmed again so
#   the result always matches [a-z0-9]+(-[a-z0-9]+)*; empty -> "untitled".
#   stdout: the slug. Returns 0.
# ---------------------------------------------------------------------------
kbv_slugify() {
  local s="${1:-}" out
  out=$(printf '%s' "$s" \
    | LC_ALL=C tr '\n\r\t' '   ' \
    | LC_ALL=C sed "$(kbv_translit_script)" \
    | LC_ALL=C tr '[:upper:]' '[:lower:]' \
    | LC_ALL=C sed -e 's/[^a-z0-9]/-/g' -e 's/-\{2,\}/-/g' -e 's/^-//' -e 's/-$//' \
    | LC_ALL=C cut -c1-60 \
    | LC_ALL=C sed -e 's/-\{1,\}$//')
  [ -n "$out" ] || out='untitled'
  printf '%s\n' "$out"
}

# ---------------------------------------------------------------------------
# kbv_redact_script
#   Internal. stdout: the sed script used by kbv_redact. Order matters: a
#   one-line private key is replaced first so the multi-line range below
#   cannot start on it and swallow the rest of the input; the range then
#   replaces the BEGIN line and deletes everything through the END line (or
#   to EOF when the block is truncated). Kept in a function for the same
#   bash 3.2 reason as kbv_translit_script. Returns 0.
# ---------------------------------------------------------------------------
kbv_redact_script() {
  cat <<'EOF'
s/-----BEGIN [A-Z ]*PRIVATE KEY-----.*-----END [A-Z ]*PRIVATE KEY-----/[REDACTED PRIVATE KEY]/g
/-----BEGIN [A-Z ]*PRIVATE KEY-----/,/-----END [A-Z ]*PRIVATE KEY-----/{
/-----BEGIN [A-Z ]*PRIVATE KEY-----/!d
s/-----BEGIN [A-Z ]*PRIVATE KEY-----.*/[REDACTED PRIVATE KEY]/
}
s|[Bb][Ee][Aa][Rr][Ee][Rr][ ][ ]*[A-Za-z0-9._~+/=-][A-Za-z0-9._~+/=-]*|Bearer [REDACTED]|g
s/\([Pp][Aa][Ss][Ss][Ww][Oo][Rr][Dd]\)=[^[:space:]&"';,]*/\1=[REDACTED]/g
s/AKIA[0-9A-Z]\{16\}/AKIA[REDACTED]/g
s/\(gh[opsur]_\)[A-Za-z0-9][A-Za-z0-9]*/\1[REDACTED]/g
s/\(github_pat_\)[A-Za-z0-9_][A-Za-z0-9_]*/\1[REDACTED]/g
EOF
}

# ---------------------------------------------------------------------------
# kbv_redact
#   stdin -> stdout. Masks: "Bearer <token>", "password=<value>" (any case,
#   value ends at whitespace or & " ' ; ,), AWS access keys AKIA + 16
#   [0-9A-Z], GitHub tokens gh[opsur]_... and github_pat_..., and
#   "-----BEGIN ... PRIVATE KEY-----" blocks (single- or multi-line, replaced
#   by [REDACTED PRIVATE KEY]). Returns sed's status (0 normally).
# ---------------------------------------------------------------------------
kbv_redact() {
  LC_ALL=C sed "$(kbv_redact_script)"
}

# ---------------------------------------------------------------------------
# kbv_json_escape <string>
#   Internal, jq-free (the guard must be able to deny when jq is missing).
#   stdout: <string> escaped for use inside a JSON string literal: newline,
#   CR and tab become spaces, other control bytes are dropped, backslash and
#   double quote are escaped. Returns 0.
# ---------------------------------------------------------------------------
kbv_json_escape() {
  printf '%s' "${1:-}" \
    | LC_ALL=C tr '\n\r\t' '   ' \
    | LC_ALL=C tr -d '\000-\037\177' \
    | LC_ALL=C sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

# ---------------------------------------------------------------------------
# kbv_ok <json-data> <msg>
#   Inputs: <json-data> is a JSON object (empty -> {}); <msg> free text.
#   stdout: exactly one line
#     {"ok":true,"code":"OK","data":{...},"msg":"..."}
#   Returns 0; 70 (nothing on stdout, diagnostic on stderr) when jq is
#   unavailable or <json-data> is not a JSON object -- a script bug.
# ---------------------------------------------------------------------------
kbv_ok() {
  local data="${1:-}" msg="${2:-}" jq
  [ -n "$data" ] || data='{}'
  jq=$(kbv_resolve_jq) || { kbv_lib_diag 'kbv_ok: jq not found'; return 70; }
  if "$jq" -c -n --argjson data "$data" --arg msg "$msg" \
      'if ($data | type) != "object" then error("data must be an object") else {ok: true, code: "OK", data: $data, msg: $msg} end' 2>/dev/null; then
    return 0
  fi
  kbv_lib_diag 'kbv_ok: data is not a JSON object'
  return 70
}

# ---------------------------------------------------------------------------
# kbv_err <CODE> <msg> [retry_after]
#   Inputs: <CODE> in GH_AUTH RATE_LIMITED SEARCH_UNAVAILABLE NOT_FOUND
#   BUDGET_EXHAUSTED DIFF_APPLY_FAILED INVALID_INPUT; <msg> free text;
#   optional <retry_after> non-negative integer (seconds).
#   stdout: exactly one line
#     {"ok":false,"code":"<CODE>","data":{},"msg":"...","retry_after":n?}
#   Returns 0; 70 (nothing on stdout, diagnostic on stderr) when jq is
#   unavailable, <CODE> is not in the list or <retry_after> is not an
#   integer -- a script bug.
# ---------------------------------------------------------------------------
kbv_err() {
  local code="${1:-}" msg="${2:-}" retry="${3:-}" jq
  case " $KBV_ERR_CODES " in
    *" $code "*) ;;
    *) kbv_lib_diag "kbv_err: unknown code '$code'"; return 70 ;;
  esac
  jq=$(kbv_resolve_jq) || { kbv_lib_diag 'kbv_err: jq not found'; return 70; }
  if [ -z "$retry" ]; then
    "$jq" -c -n --arg code "$code" --arg msg "$msg" \
      '{ok: false, code: $code, data: {}, msg: $msg}'
    return $?
  fi
  case "$retry" in
    *[!${KBV_DIGITS}]*) kbv_lib_diag "kbv_err: retry_after must be an integer, got '$retry'"; return 70 ;;
  esac
  "$jq" -c -n --arg code "$code" --arg msg "$msg" --argjson ra "$retry" \
    '{ok: false, code: $code, data: {}, msg: $msg, retry_after: $ra}'
}

# ---------------------------------------------------------------------------
# kbv_deny <reason>
#   stdout: one line of PreToolUse deny JSON, reason prefixed "kb-verify: ".
#   Does not need jq. EXITS 0 (call inside $(...) to capture in tests).
# ---------------------------------------------------------------------------
kbv_deny() {
  local esc
  esc=$(kbv_json_escape "kb-verify: ${1:-}")
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$esc"
  exit 0
}

# ---------------------------------------------------------------------------
# kbv_allow
#   stdout: nothing (an allow is silent). EXITS 0.
# ---------------------------------------------------------------------------
kbv_allow() {
  exit 0
}
