# kb-verify -- scripts/cmd/transport.sh
# Subcommands: gh-search, gh-fetch, repo-index, plus the transport layer they
# share with run-begin (kbv_tx_*). Sourced by scripts/kbv.sh; defines
# functions and a few globals only.
#
# Transport layer contract
#   kbv_tx_resolve_commit            -> KBV_TX_OUT = pinned commit SHA
#   kbv_tx_tree <ref> <out.json>     -> {truncated:bool, tree:[{type,path,sha}]}
#   kbv_tx_fetch <path> <out-file>   -> raw file content written to <out-file>
#   kbv_tx_search <terms> <prefix> <out.json> -> {items:[{path,fragment}]}
#   Each returns 0 on success; on a handled failure it returns 1 after setting
#   KBV_TX_CODE (GH_AUTH|RATE_LIMITED|SEARCH_UNAVAILABLE|NOT_FOUND),
#   KBV_TX_MSG and KBV_TX_RETRY (seconds or ''). kbv_tx_fail prints the
#   matching envelope. Never call these inside $(...): the globals would be
#   lost in the subshell.
#
# Mock (KB_VERIFY_GH_MOCK=<dir>): commit is "mock0000commit"; the tree is
# built with find (a directory containing a ".kbv-truncated" marker file
# reports truncated:true and lists only its direct children); fetch copies the
# file; search is `grep -il` with the query terms ANDed. KB_VERIFY_MOCK_CODE=
# RATE_LIMITED|SEARCH_UNAVAILABLE|NOT_FOUND|GH_AUTH forces that code on the
# first transport call of the process.

KBV_TX_CODE='OK'
KBV_TX_MSG=''
KBV_TX_RETRY=''
KBV_TX_OUT=''
KBV_TX_STATUS=''
KBV_TX_HDR_RETRY=''
KBV_TX_HDR_REMAINING=''
KBV_TX_HDR_RESET=''
KBV_TX_ERRTXT=''
KBV_MOCK_FORCED_USED=0
KBV_MOCK_COMMIT='mock0000commit'
KBV_TREE_CALL_CAP=300
KBV_TREE_SKIP_DIRS='node_modules vendor dist build'
KBV_SEARCH_PACE_SECONDS=6
KBV_SEARCH_MAX_HITS=30
KBV_SEARCH_MAX_TERMS=8

kbv_tx_set() { KBV_TX_CODE="$1"; KBV_TX_MSG="$2"; KBV_TX_RETRY="${3:-}"; }

kbv_tx_fail() {
  if [ -n "$KBV_TX_RETRY" ]; then
    kbv_err "$KBV_TX_CODE" "$KBV_TX_MSG" "$KBV_TX_RETRY"
  else
    kbv_err "$KBV_TX_CODE" "$KBV_TX_MSG"
  fi
}

kbv_tx_is_mock() { [ -n "${KB_VERIFY_GH_MOCK:-}" ]; }

# kbv_tx_mock_dir -> the fake repo dir (rc 1 + KBV_TX_* set when it is not a directory)
kbv_tx_mock_dir() {
  local d="${KB_VERIFY_GH_MOCK:-}"
  if [ ! -d "$d" ]; then
    kbv_tx_set GH_AUTH "mock: KB_VERIFY_GH_MOCK is not a directory: $d"
    return 1
  fi
  printf '%s\n' "${d%/}"
}

# kbv_tx_mock_forced -> 0 (and KBV_TX_* set) when KB_VERIFY_MOCK_CODE applies to this call
kbv_tx_mock_forced() {
  local code="${KB_VERIFY_MOCK_CODE:-}"
  [ -n "$code" ] || return 1
  [ "$KBV_MOCK_FORCED_USED" -eq 0 ] || return 1
  case "$code" in
    RATE_LIMITED) kbv_tx_set RATE_LIMITED "mock: rate limited (forced by KB_VERIFY_MOCK_CODE)" 60 ;;
    SEARCH_UNAVAILABLE) kbv_tx_set SEARCH_UNAVAILABLE "mock: code search unavailable (forced by KB_VERIFY_MOCK_CODE)" ;;
    NOT_FOUND) kbv_tx_set NOT_FOUND "mock: not found (forced by KB_VERIFY_MOCK_CODE)" ;;
    GH_AUTH) kbv_tx_set GH_AUTH "mock: not authenticated (forced by KB_VERIFY_MOCK_CODE)" ;;
    *) return 1 ;;
  esac
  KBV_MOCK_FORCED_USED=1
  return 0
}

# ---------------------------------------------------------------------------
# Real transport: gh api with headers, status classification, rate-limit wait
# ---------------------------------------------------------------------------

# kbv_tx_http <endpoint> <accept> <body-out> [gh api args...]
#   Runs `gh api -i` and splits status/headers/body. Sets KBV_TX_STATUS (3
#   digits) and the rate-limit headers. rc 1 when gh produced no HTTP status
#   (not logged in, network down): KBV_TX_ERRTXT carries gh's stderr.
kbv_tx_http() {
  local ep="$1" accept="$2" body="$3" raw errf hdr
  shift 3
  raw=$(kbv_tmpfile); errf=$(kbv_tmpfile); hdr=$(kbv_tmpfile)
  KBV_TX_STATUS=''; KBV_TX_HDR_RETRY=''; KBV_TX_HDR_REMAINING=''; KBV_TX_HDR_RESET=''; KBV_TX_ERRTXT=''
  gh api -i --method GET -H "Accept: $accept" "$@" "$ep" > "$raw" 2> "$errf" || true
  KBV_TX_STATUS=$(head -n 1 "$raw" | awk '{print $2}')
  case "$KBV_TX_STATUS" in
    [0-9][0-9][0-9]) ;;
    *)
      KBV_TX_STATUS=''
      KBV_TX_ERRTXT=$(LC_ALL=C head -c 300 "$errf" | tr '\n' ' ')
      return 1
      ;;
  esac
  LC_ALL=C sed -n '1,/^[[:space:]]*$/p' "$raw" > "$hdr"
  LC_ALL=C sed '1,/^[[:space:]]*$/d' "$raw" > "$body"
  KBV_TX_HDR_RETRY=$(kbv_tx_header "$hdr" 'retry-after')
  KBV_TX_HDR_REMAINING=$(kbv_tx_header "$hdr" 'x-ratelimit-remaining')
  KBV_TX_HDR_RESET=$(kbv_tx_header "$hdr" 'x-ratelimit-reset')
  return 0
}

# kbv_tx_header <headers-file> <lowercase-name> -> value (digits only) or ''
kbv_tx_header() {
  LC_ALL=C awk -v name="$2" 'BEGIN{IGNORECASE=1} {
    n = tolower($1); sub(/:$/, "", n)
    if (n == name) { v = $2; gsub(/[^0-9]/, "", v); print v; exit }
  }' "$1"
}

# kbv_tx_body_message <body-file> -> .message of a JSON error body, or ''
kbv_tx_body_message() {
  "$KBV_JQ" -r 'if type == "object" then (.message // "") else "" end' "$1" 2>/dev/null | LC_ALL=C head -c 200 || true
}

# kbv_tx_request <kind:commit|tree|fetch|search> <endpoint> <accept> <body-out> [gh api args...]
#   Classifies the status into the envelope codes; waits once (up to 90 s)
#   on a rate limit before giving up with RATE_LIMITED + retry_after.
kbv_tx_request() {
  local kind="$1" ep="$2" accept="$3" body="$4" attempt=0 wait now msg
  shift 4
  while :; do
    if ! kbv_tx_http "$ep" "$accept" "$body" "$@"; then
      kbv_tx_set GH_AUTH "gh api produced no HTTP response (not logged in or network down): $KBV_TX_ERRTXT"
      return 1
    fi
    case "$KBV_TX_STATUS" in
      2*) return 0 ;;
      401)
        kbv_tx_set GH_AUTH "GitHub returned 401 (token missing or expired): $(kbv_tx_body_message "$body")"
        return 1 ;;
      403|429)
        msg=$(kbv_tx_body_message "$body")
        if [ "$KBV_TX_STATUS" = 429 ] || [ -n "$KBV_TX_HDR_RETRY" ] || [ "$KBV_TX_HDR_REMAINING" = 0 ]; then
          wait="$KBV_TX_HDR_RETRY"
          if [ -z "$wait" ] && [ -n "$KBV_TX_HDR_RESET" ]; then
            now=$(date +%s)
            wait=$((KBV_TX_HDR_RESET - now))
            [ "$wait" -ge 0 ] || wait=0
          fi
          [ -n "$wait" ] || wait=60
          if [ "$attempt" -eq 0 ] && [ "$wait" -le 90 ]; then
            attempt=1
            sleep "$wait"
            continue
          fi
          kbv_tx_set RATE_LIMITED "GitHub rate limit (HTTP $KBV_TX_STATUS): $msg" "$wait"
          return 1
        fi
        kbv_tx_set GH_AUTH "GitHub returned 403 without rate-limit headers (token lacks permission?): $msg"
        return 1 ;;
      404)
        if [ "$kind" = search ]; then
          kbv_tx_set SEARCH_UNAVAILABLE "code search returned 404 for this repo: $(kbv_tx_body_message "$body")"
        else
          kbv_tx_set NOT_FOUND "GitHub returned 404: $ep"
        fi
        return 1 ;;
      422)
        if [ "$kind" = search ]; then
          kbv_tx_set SEARCH_UNAVAILABLE "code search returned 422 (repo not indexed or not searchable): $(kbv_tx_body_message "$body")"
        else
          kbv_tx_set NOT_FOUND "GitHub returned 422 for $ep: $(kbv_tx_body_message "$body")"
        fi
        return 1 ;;
      5*)
        kbv_tx_set RATE_LIMITED "GitHub returned HTTP $KBV_TX_STATUS (transient server error)" 60
        return 1 ;;
      *)
        kbv_tx_set GH_AUTH "unexpected HTTP $KBV_TX_STATUS from GitHub for $ep: $(kbv_tx_body_message "$body")"
        return 1 ;;
    esac
  done
}

# ---------------------------------------------------------------------------
# kbv_tx_resolve_commit -> KBV_TX_OUT = SHA of the default branch head
# ---------------------------------------------------------------------------
kbv_tx_resolve_commit() {
  local body branch sha
  KBV_TX_OUT=''
  if kbv_tx_is_mock; then
    kbv_tx_mock_dir >/dev/null || return 1
    kbv_tx_mock_forced && return 1
    KBV_TX_OUT="$KBV_MOCK_COMMIT"
    return 0
  fi
  body=$(kbv_tmpfile)
  kbv_tx_request commit "repos/$KBV_GH_REPO" 'application/vnd.github+json' "$body" || return 1
  branch=$("$KBV_JQ" -r '.default_branch // empty' "$body" 2>/dev/null || true)
  if [ -z "$branch" ]; then
    kbv_tx_set GH_AUTH "repos/$KBV_GH_REPO returned no default_branch"
    return 1
  fi
  kbv_tx_request commit "repos/$KBV_GH_REPO/git/ref/heads/$branch" 'application/vnd.github+json' "$body" || return 1
  sha=$("$KBV_JQ" -r '.object.sha // empty' "$body" 2>/dev/null || true)
  if [ -z "$sha" ]; then
    kbv_tx_set GH_AUTH "git/ref/heads/$branch returned no object.sha"
    return 1
  fi
  KBV_TX_OUT="$sha"
  return 0
}

# ---------------------------------------------------------------------------
# kbv_tx_tree <ref> <out.json>
#   <ref> is the commit SHA for the root or a tree SHA from a parent listing
#   (mock: "dir:<relative-path>"). Output paths are relative to that tree.
# ---------------------------------------------------------------------------
kbv_tx_tree() {
  local ref="$1" out="$2" mock base rel tsv body
  if kbv_tx_is_mock; then
    mock=$(kbv_tx_mock_dir) || return 1
    kbv_tx_mock_forced && return 1
    case "$ref" in
      "$KBV_MOCK_COMMIT") base="$mock"; rel='' ;;
      dir:*) rel="${ref#dir:}"; base="$mock/$rel" ;;
      *) kbv_tx_set NOT_FOUND "mock: unknown tree ref '$ref'"; return 1 ;;
    esac
    if [ ! -d "$base" ]; then
      kbv_tx_set NOT_FOUND "mock: tree not found: $ref"
      return 1
    fi
    tsv=$(kbv_tmpfile)
    if [ -f "$base/.kbv-truncated" ]; then
      kbv_tx_mock_list "$base" "$rel" 1 > "$tsv"
      "$KBV_JQ" -c -R -s '{truncated: true, tree: [split("\n")[] | select(length > 0) | split("\t") | {type: .[0], path: .[1], sha: .[2]}]}' "$tsv" > "$out"
    else
      kbv_tx_mock_list "$base" "$rel" 0 > "$tsv"
      "$KBV_JQ" -c -R -s '{truncated: false, tree: [split("\n")[] | select(length > 0) | split("\t") | {type: .[0], path: .[1], sha: .[2]}]}' "$tsv" > "$out"
    fi
    return 0
  fi
  body=$(kbv_tmpfile)
  kbv_tx_request tree "repos/$KBV_GH_REPO/git/trees/$ref?recursive=1" 'application/vnd.github+json' "$body" || return 1
  if ! "$KBV_JQ" -c '{truncated: (.truncated == true), tree: [(.tree // [])[] | {type, path, sha}]}' "$body" > "$out" 2>/dev/null; then
    kbv_tx_set NOT_FOUND "git/trees/$ref returned an unreadable body"
    return 1
  fi
  return 0
}

# kbv_tx_mock_list <base-dir> <rel-prefix> <shallow:0|1> -> TSV type\tpath\tsha
kbv_tx_mock_list() {
  local base="$1" rel="$2" shallow="$3" depth_args=''
  [ "$shallow" -eq 0 ] || depth_args='-maxdepth 1'
  # shellcheck disable=SC2086
  (cd "$base" && find . -mindepth 1 $depth_args \( -name .git -prune \) -o \( -type d -print \) -o \( -type f ! -name .kbv-truncated -print \) 2>/dev/null) \
    | LC_ALL=C sort \
    | while IFS= read -r p; do
        p="${p#./}"
        if [ -d "$base/$p" ]; then
          if [ -n "$rel" ]; then printf 'tree\t%s\tdir:%s/%s\n' "$p" "$rel" "$p"; else printf 'tree\t%s\tdir:%s\n' "$p" "$p"; fi
        else
          printf 'blob\t%s\tblob:%s\n' "$p" "$p"
        fi
      done
}

# ---------------------------------------------------------------------------
# kbv_tx_fetch <repo-path> <out-file>  (raw content at the pinned commit)
# ---------------------------------------------------------------------------
kbv_tx_fetch() {
  local path="$1" out="$2" commit="$3" mock
  if kbv_tx_is_mock; then
    mock=$(kbv_tx_mock_dir) || return 1
    kbv_tx_mock_forced && return 1
    if [ ! -f "$mock/$path" ]; then
      kbv_tx_set NOT_FOUND "mock: no such file at $KBV_MOCK_COMMIT: $path"
      return 1
    fi
    cp "$mock/$path" "$out"
    return 0
  fi
  kbv_tx_request fetch "repos/$KBV_GH_REPO/contents/$path?ref=$commit" 'application/vnd.github.raw+json' "$out" || return 1
  return 0
}

# ---------------------------------------------------------------------------
# kbv_tx_search <terms (space separated)> <path-prefix|''> <out.json>
# ---------------------------------------------------------------------------
kbv_tx_search() {
  local terms="$1" prefix="$2" out="$3" mock base t first tsv body q list f frag rel n=0
  if kbv_tx_is_mock; then
    mock=$(kbv_tx_mock_dir) || return 1
    kbv_tx_mock_forced && return 1
    base="$mock"
    [ -z "$prefix" ] || base="$mock/$prefix"
    tsv=$(kbv_tmpfile)
    : > "$tsv"
    if [ -d "$base" ]; then
      list=$(cd "$mock" && find "${prefix:-.}" -type f ! -name .kbv-truncated ! -path '*/.git/*' 2>/dev/null | LC_ALL=C sort)
      first=''
      for t in $terms; do
        [ -n "$first" ] || first="$t"
        list=$(printf '%s\n' "$list" | while IFS= read -r f; do
          [ -n "$f" ] || continue
          if LC_ALL=C grep -qiF -e "$t" -- "$mock/$f" 2>/dev/null; then printf '%s\n' "$f"; fi
        done)
        [ -n "$list" ] || break
      done
      if [ -n "$list" ]; then
        printf '%s\n' "$list" | while IFS= read -r f; do
          [ -n "$f" ] || continue
          n=$((n + 1))
          [ "$n" -le "$KBV_SEARCH_MAX_HITS" ] || continue
          rel="${f#./}"
          frag=$(LC_ALL=C grep -iF -m 1 -e "$first" -- "$mock/$f" 2>/dev/null | LC_ALL=C head -c 200 | tr '\t\r' '  ' || true)
          printf '%s\t%s\n' "$rel" "$frag"
        done > "$tsv"
      fi
    fi
    "$KBV_JQ" -c -R -s '{items: [split("\n")[] | select(length > 0) | split("\t") | {path: .[0], fragment: (.[1] // "")}]}' "$tsv" > "$out"
    return 0
  fi
  body=$(kbv_tmpfile)
  q="$terms repo:$KBV_GH_REPO"
  [ -z "$prefix" ] || q="$q path:$prefix"
  kbv_tx_request search 'search/code' 'application/vnd.github.text-match+json' "$body" -f "q=$q" -F "per_page=$KBV_SEARCH_MAX_HITS" || return 1
  if ! "$KBV_JQ" -c '{items: [(.items // [])[] | {path: .path, fragment: (((.text_matches // []) | map(.fragment // "") | join(" ")) | .[0:200])}]}' "$body" > "$out" 2>/dev/null; then
    kbv_tx_set SEARCH_UNAVAILABLE "search/code returned an unreadable body"
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Per-article budget counters: runs/<id>/budget/<sha12>.json
# ---------------------------------------------------------------------------
kbv_budget_file() { printf '%s/budget/%s.json\n' "$KBV_RUN_DIR" "$1"; }

# kbv_budget_get <sha12> <search_calls|fetch_calls> -> current count
kbv_budget_get() {
  local f
  f=$(kbv_budget_file "$1")
  if [ -f "$f" ]; then
    "$KBV_JQ" -r --arg k "$2" '.[$k] // 0' "$f" 2>/dev/null || printf '0\n'
  else
    printf '0\n'
  fi
}

# kbv_budget_inc <sha12> <key> -> new count
kbv_budget_inc() {
  local f cur
  f=$(kbv_budget_file "$1")
  cur='{}'
  [ ! -f "$f" ] || cur=$("$KBV_JQ" -c . "$f" 2>/dev/null || printf '{}')
  printf '%s' "$cur" | "$KBV_JQ" -c --arg k "$2" '.[$k] = ((.[$k] // 0) + 1)' | kbv_atomic_write "$f"
  "$KBV_JQ" -r --arg k "$2" '.[$k]' "$f"
}

# kbv_dot_path <repo-path> -> same path with every segment starting with "." renamed to "_dot_<rest>"
kbv_dot_path() {
  printf '%s\n' "$1" | LC_ALL=C awk -F/ 'BEGIN{OFS="/"} {for (i = 1; i <= NF; i++) if (substr($i, 1, 1) == ".") $i = "_dot_" substr($i, 2); print}'
}

# kbv_search_terms <anchor> -> up to 8 distinct [A-Za-z0-9_]+ terms of length >= 2, space separated
kbv_search_terms() {
  printf '%s\n' "$1" \
    | LC_ALL=C tr -c 'A-Za-z0-9_' '\n' \
    | LC_ALL=C awk -v max="$KBV_SEARCH_MAX_TERMS" '
        length($0) >= 2 && !seen[$0]++ && n < max { out = (n ? out " " : "") $0; n++ }
        END { print out }'
}

# kbv_mark_search_unavailable  -- persist search_available:false in run.json and mapping.json
kbv_mark_search_unavailable() {
  local today
  "$KBV_JQ" -c '.search_available = false' "$KBV_RUN_DIR/run.json" | kbv_atomic_write "$KBV_RUN_DIR/run.json"
  today=$(kbv_date_utc "$(kbv_now)")
  kbv_mapping_apply '{"repo":{"search_available":false}}' "$KBV_RUN_COMMIT" "$today" || true
}

# ---------------------------------------------------------------------------
# gh-search --run <id> --article <sha12> --claim <id> [--path <prefix>]
#   Term = the anchor of claims[].id == <id> in inbox/claims-<sha12>.json,
#   reduced to alphanumeric terms ANDed together. Cache by sha1(commit +
#   query) in cache/search/; a cache hit costs no pacing and no budget.
#   Pacing: 6 s between real searches (timestamp file search.last in the run
#   dir; KB_VERIFY_FAKE_NOW replaces the clock and skips the actual sleep).
#   data: {hits:[{path,fragment}], query, cached, waited, search_calls, search_budget, commit, claim}
# ---------------------------------------------------------------------------
kbv_cmd_gh_search() {
  local run='' article='' claim='' prefix='' claims_file anchor terms query key cache_dir cache_file
  local used last now delta waited=0 effective out data sa
  while [ $# -gt 0 ]; do
    case "$1" in
      --run) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--run needs a value"; return 0; }; run="$2"; shift 2 ;;
      --article) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--article needs a value"; return 0; }; article="$2"; shift 2 ;;
      --claim) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--claim needs a value"; return 0; }; claim="$2"; shift 2 ;;
      --path) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--path needs a value"; return 0; }; prefix="$2"; shift 2 ;;
      *) kbv_err INVALID_INPUT "gh-search: unexpected argument '$1' (usage: gh-search --run <id> --article <sha12> --claim <id> [--path <prefix>])"; return 0 ;;
    esac
  done
  kbv_require_run "$run" || return 0
  kbv_require_commit || return 0
  if ! kbv_is_hex12 "$article"; then
    kbv_err INVALID_INPUT "--article must be the first 12 hex characters of the article sha256"
    return 0
  fi
  if [ -z "$claim" ]; then
    kbv_err INVALID_INPUT "--claim <id> is required"
    return 0
  fi
  case "$prefix" in /*) kbv_err INVALID_INPUT "--path must be repo-relative (no leading slash)"; return 0 ;; esac
  prefix="${prefix%/}"

  claims_file="$KBV_RUN_DIR/inbox/claims-$article.json"
  if [ ! -f "$claims_file" ]; then
    kbv_err INVALID_INPUT "claims file not found: $claims_file (Write inbox/claims-$article.json first)"
    return 0
  fi
  if ! anchor=$("$KBV_JQ" -r --arg id "$claim" '
        if type != "object" or (.claims | type) != "array" then error("claims[] missing")
        else ([.claims[] | select(type == "object" and (.id | tostring) == $id)] | first
              | if . == null then error("claim not found") else (.anchor // .text // "") end) end' "$claims_file" 2>/dev/null); then
    kbv_err INVALID_INPUT "claim '$claim' not found in claims-$article.json (or the file is malformed)"
    return 0
  fi
  terms=$(kbv_search_terms "$anchor")
  if [ -z "$terms" ]; then
    kbv_err INVALID_INPUT "claim '$claim' has no searchable term (anchor/text needs at least one [A-Za-z0-9_]{2,} token)"
    return 0
  fi
  query="$terms"
  [ -z "$prefix" ] || query="$terms path:$prefix"

  sa=$("$KBV_JQ" -r '.search_available' "$KBV_RUN_DIR/run.json")
  if [ "$sa" = false ]; then
    kbv_err SEARCH_UNAVAILABLE "code search was marked unavailable earlier in run $KBV_RUN_ID; skip layer (c)"
    return 0
  fi

  key=$(printf '%s\n%s' "$KBV_RUN_COMMIT" "$query" | shasum -a 1 | cut -c1-40)
  cache_dir="$KBV_RUN_DIR/cache/search"
  cache_file="$cache_dir/$key.json"
  if [ -f "$cache_file" ]; then
    data=$("$KBV_JQ" -c --arg q "$query" --arg commit "$KBV_RUN_COMMIT" --arg claim "$claim" \
      --argjson used "$(kbv_budget_get "$article" search_calls)" --argjson budget "$KBV_BUDGET_SEARCH" \
      '{hits: .items, query: $q, cached: true, waited: 0, search_calls: $used, search_budget: $budget, commit: $commit, claim: $claim}' "$cache_file")
    kbv_ok "$data" "cache hit: $(printf '%s' "$data" | "$KBV_JQ" -r '.hits | length') hits"
    return 0
  fi

  used=$(kbv_budget_get "$article" search_calls)
  if [ "$used" -ge "$KBV_BUDGET_SEARCH" ]; then
    kbv_err BUDGET_EXHAUSTED "search budget exhausted for article $article ($used/$KBV_BUDGET_SEARCH calls)"
    return 0
  fi

  now=$(kbv_now)
  last=0
  if [ -f "$KBV_RUN_DIR/search.last" ]; then
    last=$(cat "$KBV_RUN_DIR/search.last" 2>/dev/null || printf '0')
    kbv_is_int "$last" || last=0
  fi
  delta=$((now - last))
  if [ "$delta" -lt "$KBV_SEARCH_PACE_SECONDS" ] && [ "$delta" -ge 0 ]; then
    waited=$((KBV_SEARCH_PACE_SECONDS - delta))
    [ -n "${KB_VERIFY_FAKE_NOW:-}" ] || sleep "$waited"
  fi
  effective=$((now + waited))

  used=$(kbv_budget_inc "$article" search_calls)
  printf '%s\n' "$effective" | kbv_atomic_write "$KBV_RUN_DIR/search.last"
  out=$(kbv_tmpfile)
  if ! kbv_tx_search "$terms" "$prefix" "$out"; then
    if [ "$KBV_TX_CODE" = SEARCH_UNAVAILABLE ]; then
      kbv_mark_search_unavailable
    fi
    kbv_tx_fail
    return 0
  fi
  mkdir -p "$cache_dir"
  "$KBV_JQ" -c --arg q "$query" '. + {query: $q}' "$out" | kbv_atomic_write "$cache_file"
  data=$("$KBV_JQ" -c --arg q "$query" --arg commit "$KBV_RUN_COMMIT" --arg claim "$claim" \
    --argjson used "$used" --argjson budget "$KBV_BUDGET_SEARCH" --argjson waited "$waited" \
    '{hits: .items, query: $q, cached: false, waited: $waited, search_calls: $used, search_budget: $budget, commit: $commit, claim: $claim}' "$cache_file")
  kbv_ok "$data" "$(printf '%s' "$data" | "$KBV_JQ" -r '"\(.hits | length) hits (\(.search_calls)/\(.search_budget) searches)"')"
}

# ---------------------------------------------------------------------------
# gh-fetch --run <id> --article <sha12> <path>
#   contents/<path>?ref=<commit> raw -> runs/<id>/cache/<commit>/<path> with
#   every leading-dot segment renamed _dot_ (Grep skips hidden files). A file
#   already in the cache is returned without a call and without budget.
#   data: {path, local_path, commit, cached, bytes, fetch_calls, fetch_budget}
# ---------------------------------------------------------------------------
kbv_cmd_gh_fetch() {
  local run='' article='' path='' rel dest used tmp bytes data
  while [ $# -gt 0 ]; do
    case "$1" in
      --run) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--run needs a value"; return 0; }; run="$2"; shift 2 ;;
      --article) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--article needs a value"; return 0; }; article="$2"; shift 2 ;;
      -*) kbv_err INVALID_INPUT "gh-fetch: unexpected option '$1' (usage: gh-fetch --run <id> --article <sha12> <path>)"; return 0 ;;
      *)
        if [ -n "$path" ]; then kbv_err INVALID_INPUT "gh-fetch: exactly one <path> is expected"; return 0; fi
        path="$1"; shift ;;
    esac
  done
  kbv_require_run "$run" || return 0
  kbv_require_commit || return 0
  if ! kbv_is_hex12 "$article"; then
    kbv_err INVALID_INPUT "--article must be the first 12 hex characters of the article sha256"
    return 0
  fi
  if [ -z "$path" ]; then
    kbv_err INVALID_INPUT "gh-fetch: <path> is required"
    return 0
  fi
  case "$path" in
    /*) kbv_err INVALID_INPUT "gh-fetch: <path> must be repo-relative (no leading slash)"; return 0 ;;
    */) kbv_err INVALID_INPUT "gh-fetch: <path> must name a file, not a directory"; return 0 ;;
  esac
  rel=$(kbv_dot_path "$path")
  dest="$KBV_RUN_DIR/cache/$KBV_RUN_COMMIT/$rel"

  if [ -f "$dest" ]; then
    bytes=$(wc -c < "$dest" | tr -d ' ')
    data=$("$KBV_JQ" -c -n --arg path "$path" --arg lp "$dest" --arg commit "$KBV_RUN_COMMIT" --argjson bytes "$bytes" \
      --argjson used "$(kbv_budget_get "$article" fetch_calls)" --argjson budget "$KBV_BUDGET_FETCH" \
      '{path: $path, local_path: $lp, commit: $commit, cached: true, bytes: $bytes, fetch_calls: $used, fetch_budget: $budget}')
    kbv_ok "$data" "cache hit: $dest"
    return 0
  fi

  used=$(kbv_budget_get "$article" fetch_calls)
  if [ "$used" -ge "$KBV_BUDGET_FETCH" ]; then
    kbv_err BUDGET_EXHAUSTED "fetch budget exhausted for article $article ($used/$KBV_BUDGET_FETCH calls)"
    return 0
  fi
  used=$(kbv_budget_inc "$article" fetch_calls)
  tmp=$(kbv_tmpfile)
  if ! kbv_tx_fetch "$path" "$tmp" "$KBV_RUN_COMMIT"; then
    kbv_tx_fail
    return 0
  fi
  mkdir -p "$(dirname -- "$dest")"
  mv -f "$tmp" "$dest"
  bytes=$(wc -c < "$dest" | tr -d ' ')
  data=$("$KBV_JQ" -c -n --arg path "$path" --arg lp "$dest" --arg commit "$KBV_RUN_COMMIT" --argjson bytes "$bytes" \
    --argjson used "$used" --argjson budget "$KBV_BUDGET_FETCH" \
    '{path: $path, local_path: $lp, commit: $commit, cached: false, bytes: $bytes, fetch_calls: $used, fetch_budget: $budget}')
  kbv_ok "$data" "fetched $path ($used/$KBV_BUDGET_FETCH fetches)"
}

# ---------------------------------------------------------------------------
# repo-index [--refresh]
#   Builds $KBV_DATA/repo/<org-repo>/{tree.txt, i18n/, index.json}. Skipped
#   (data.refreshed=false) when tree.txt is younger than 7 days unless
#   --refresh. Tree: git/trees/<commit>?recursive=1; a truncated listing is
#   expanded one directory level at a time (skipping node_modules, vendor,
#   dist, build) under a cap of 300 tree calls -> tree_partial:true. Then the
#   files under a locales|i18n|messages directory whose basename is a
#   configured locale (or starts with "<locale>.") are fetched into i18n/, up
#   to budgets.index_i18n_files -> i18n_partial:true. mapping.json repo{}
#   fields are updated through the mapping-update logic.
#   data: {repo, index_commit, index_dir, tree_path, tree_entries, tree_calls,
#          tree_partial, i18n_dir, i18n_files, i18n_candidates, i18n_partial, refreshed}
# ---------------------------------------------------------------------------
kbv_cmd_repo_index() {
  local refresh=0 index_dir tree_file index_file commit tmp_tree tree_json calls=0 partial=false
  local qi=0 prefix ref truncated entries locales cand_file cand_count fetched=0 missing=0 i18n_partial=false
  local p dest tmp today now data qp qr
  while [ $# -gt 0 ]; do
    case "$1" in
      --refresh) refresh=1; shift ;;
      *) kbv_err INVALID_INPUT "repo-index: unexpected argument '$1' (usage: repo-index [--refresh])"; return 0 ;;
    esac
  done
  index_dir="$KBV_REPO_DIR"
  tree_file="$index_dir/tree.txt"
  index_file="$index_dir/index.json"

  if [ "$refresh" -eq 0 ] && [ -f "$tree_file" ] && [ -f "$index_file" ] && [ -z "$(find "$tree_file" -mtime +7 2>/dev/null)" ]; then
    data=$("$KBV_JQ" -c '. + {refreshed: false}' "$index_file" 2>/dev/null) || data=''
    if [ -n "$data" ]; then
      kbv_ok "$data" "index is fresh (younger than 7 days); use --refresh to rebuild"
      return 0
    fi
  fi

  if ! kbv_tx_resolve_commit; then
    kbv_tx_fail
    return 0
  fi
  commit="$KBV_TX_OUT"
  tmp_tree=$(kbv_tmpfile)
  tree_json=$(kbv_tmpfile)
  : > "$tmp_tree"

  # Breadth-first expansion of truncated trees (indexed arrays: bash 3.2 has them).
  qp[0]=''
  qr[0]="$commit"
  while [ "$qi" -lt "${#qp[@]}" ]; do
    prefix="${qp[$qi]}"
    ref="${qr[$qi]}"
    qi=$((qi + 1))
    if [ "$calls" -ge "$KBV_TREE_CALL_CAP" ]; then
      partial=true
      break
    fi
    calls=$((calls + 1))
    if ! kbv_tx_tree "$ref" "$tree_json"; then
      if [ "$KBV_TX_CODE" = NOT_FOUND ]; then
        partial=true
        continue
      fi
      kbv_tx_fail
      return 0
    fi
    "$KBV_JQ" -r --arg p "$prefix" '.tree[] | select(.type == "blob") | $p + .path' "$tree_json" >> "$tmp_tree"
    truncated=$("$KBV_JQ" -r '.truncated' "$tree_json")
    if [ "$truncated" = true ]; then
      entries=$(kbv_tmpfile)
      "$KBV_JQ" -r '.tree[] | select(.type == "tree") | .path + "\t" + .sha' "$tree_json" > "$entries"
      while IFS="$(printf '\t')" read -r p ref; do
        [ -n "$p" ] || continue
        case " $KBV_TREE_SKIP_DIRS " in *" $(basename -- "$p") "*) continue ;; esac
        qp[${#qp[@]}]="$prefix$p/"
        qr[${#qr[@]}]="$ref"
      done < "$entries"
    fi
  done
  if [ "$qi" -lt "${#qp[@]}" ]; then partial=true; fi

  mkdir -p "$index_dir"
  LC_ALL=C sort -u "$tmp_tree" | kbv_atomic_write "$tree_file"
  entries=$(wc -l < "$tree_file" | tr -d ' ')

  # i18n candidates: a locales|i18n|messages directory segment and a basename
  # equal to a configured locale or starting with "<locale>.".
  locales=$(kbv_config_get '(.integration.locales // ["en"]) | if type == "array" then map(tostring) | join(" ") else "en" end')
  [ -n "$locales" ] || locales='en'
  cand_file=$(kbv_tmpfile)
  LC_ALL=C awk -F/ -v locs="$locales" '
    BEGIN { n = split(locs, L, " ") }
    {
      hit = 0
      for (i = 1; i < NF; i++) if ($i == "locales" || $i == "i18n" || $i == "messages") hit = 1
      if (!hit) next
      b = $NF
      for (j = 1; j <= n; j++) if (b == L[j] || index(b, L[j] ".") == 1) { print $0; break }
    }' "$tree_file" > "$cand_file"
  cand_count=$(wc -l < "$cand_file" | tr -d ' ')
  [ "$cand_count" -le "$KBV_BUDGET_I18N" ] || i18n_partial=true
  rm -rf "$index_dir/i18n"
  mkdir -p "$index_dir/i18n"
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    [ "$((fetched + missing))" -lt "$KBV_BUDGET_I18N" ] || break
    tmp=$(kbv_tmpfile)
    if kbv_tx_fetch "$p" "$tmp" "$commit"; then
      dest="$index_dir/i18n/$(kbv_dot_path "$p")"
      mkdir -p "$(dirname -- "$dest")"
      mv -f "$tmp" "$dest"
      fetched=$((fetched + 1))
    else
      if [ "$KBV_TX_CODE" = NOT_FOUND ]; then
        missing=$((missing + 1))
        continue
      fi
      kbv_tx_fail
      return 0
    fi
  done < "$cand_file"

  now=$(kbv_now)
  today=$(kbv_date_utc "$now")
  "$KBV_JQ" -c -n --arg repo "$KBV_GH_REPO" --arg commit "$commit" --arg today "$today" --argjson epoch "$now" \
    --arg dir "$index_dir" --arg tree "$tree_file" --argjson entries "$entries" --argjson calls "$calls" \
    --argjson partial "$partial" --argjson fetched "$fetched" --argjson missing "$missing" \
    --argjson cands "$cand_count" --argjson ipartial "$i18n_partial" --arg locales "$locales" \
    '{repo: $repo, index_commit: $commit, indexed_at: $today, indexed_at_epoch: $epoch, index_dir: $dir,
      tree_path: $tree, tree_entries: $entries, tree_calls: $calls, tree_partial: $partial,
      i18n_dir: ($dir + "/i18n"), i18n_files: $fetched, i18n_missing: $missing, i18n_candidates: $cands,
      i18n_partial: $ipartial, locales: ($locales | split(" "))}' | kbv_atomic_write "$index_file"

  kbv_mapping_apply "$("$KBV_JQ" -c -n --arg repo "$KBV_GH_REPO" --arg commit "$commit" --arg today "$today" \
      --argjson partial "$partial" --argjson ipartial "$i18n_partial" \
      '{repo: {name: $repo, index_commit: $commit, indexed_at: $today, tree_partial: $partial, i18n_partial: $ipartial}}')" \
    "$commit" "$today" || {
      kbv_err INVALID_INPUT "index written, but mapping.json could not be updated: $KBV_MAPPING_ERR"
      return 0
    }
  data=$("$KBV_JQ" -c '. + {refreshed: true}' "$index_file")
  kbv_ok "$data" "indexed $entries paths in $calls tree calls; $fetched i18n files"
}
