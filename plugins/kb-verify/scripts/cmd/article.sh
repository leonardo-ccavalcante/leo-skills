# kb-verify -- scripts/cmd/article.sh
# Subcommands: frontmatter, next-bug-id, diff-check. Sourced by
# scripts/kbv.sh; defines functions only. kbv_fm_parse is also used by
# config-init (setup.sh).

# ---------------------------------------------------------------------------
# Frontmatter subset parser
#   Supported: a leading "---" block closed by "---" or "..."; `key: scalar`
#   (plain, "double" or 'single' quoted; a trailing " # comment" is dropped
#   from plain scalars); `key:` followed by `- item` lines; the inline list
#   form `key: [a, b]`; blank lines and `# comments`. Anything else (nested
#   mappings, block scalars | and >, anchors/aliases/tags, inline mappings,
#   tab indentation, list items without a key, unterminated quotes, an
#   unclosed block) is reported as a note and skipped: the article is then
#   verified by its body ("frontmatter partially parsed").
#
# kbv_fm_awk <mode:fm|body>  -- prints the awk program (kept in a function
#   because bash 3.2 cannot parse heredocs with unbalanced quotes inside $(...))
# ---------------------------------------------------------------------------
kbv_fm_awk() {
  cat <<'EOF'
function trim(s) { sub(/^[ \t]+/, "", s); sub(/[ \t]+$/, "", s); return s }
function note(msg) { print "N\t" msg }
function unquote(v,   inner) {
  if (length(v) >= 2 && v ~ /^".*"$/) { inner = substr(v, 2, length(v) - 2); gsub(/\\"/, "\"", inner); gsub(/\\\\/, "\\", inner); return inner }
  if (length(v) >= 2 && v ~ /^'.*'$/) { inner = substr(v, 2, length(v) - 2); gsub(/''/, "'", inner); return inner }
  return v
}
function plain(v,   i) {
  if (v ~ /^["']/) return v
  i = index(v, " #"); if (i > 0) v = substr(v, 1, i - 1)
  return trim(v)
}
function emit_items(key, inner,   n, parts, i, it) {
  n = split(inner, parts, ",")
  for (i = 1; i <= n; i++) { it = trim(parts[i]); if (it == "") continue; print "L\t" key "\t" unquote(it) }
}
BEGIN { state = (mode == "fm") ? 1 : 2; cur = ""; curkind = ""; body = 0; steps = 0; conds = 0; nums = 0; h1 = 0 }
{
  line = $0
  sub(/\r$/, "", line)
  if (state == 1) {
    if (NR == 1) next
    if (line ~ /^---[ \t]*$/ || line ~ /^\.\.\.[ \t]*$/) { state = 2; next }
    if (line ~ /^[ \t]*$/) next
    if (line ~ /^[ \t]*#/) next
    if (line ~ /^\t/) { note("tab indentation at line " NR); cur = ""; curkind = ""; next }
    gsub(/\t/, " ", line)
    if (line ~ /^[ ]*-([ ]|$)/) {
      if (curkind != "list") { note("list item without a key at line " NR); next }
      item = line; sub(/^[ ]*-[ ]*/, "", item); item = trim(item)
      if (item ~ /^[A-Za-z0-9_.-]+:([ ]|$)/) { note("mapping inside a list at line " NR); next }
      if (item ~ /^[&*!]/) { note("anchor, alias or tag at line " NR); next }
      print "L\t" cur "\t" unquote(plain(item))
      next
    }
    if (line ~ /^[ ]+/) { note("nested mapping or continued value at line " NR); cur = ""; curkind = ""; next }
    if (line ~ /^[A-Za-z0-9_.-]+:([ ]|$)/) {
      key = line; sub(/:.*$/, "", key)
      val = line; sub(/^[A-Za-z0-9_.-]+:[ ]*/, "", val); val = trim(val)
      if (key in seen) note("duplicate key '" key "' at line " NR)
      seen[key] = 1
      cur = ""; curkind = ""
      if (val == "") { cur = key; curkind = "list"; print "K\t" key; next }
      if (val ~ /^[|>]/) { note("block scalar for key '" key "' at line " NR); next }
      if (val ~ /^[&*!]/) { note("anchor, alias or tag for key '" key "' at line " NR); next }
      if (val ~ /^\{/) { note("inline mapping for key '" key "' at line " NR); next }
      if (val ~ /^\[.*\]$/) { print "K\t" key; emit_items(key, substr(val, 2, length(val) - 2)); next }
      if (val ~ /^["']/ && val !~ /^".*"$/ && val !~ /^'.*'$/) { note("unterminated quote or trailing content for key '" key "' at line " NR); next }
      print "S\t" key "\t" unquote(plain(val))
      next
    }
    note("unsupported line " NR)
    cur = ""; curkind = ""
    next
  }
  body++
  gsub(/\t/, " ", line)
  if (!h1 && line ~ /^#[ ]+/) { t = line; sub(/^#[ ]+/, "", t); print "T\t" trim(t); h1 = 1 }
  if (line ~ /^[ ]*[0-9]+[.)][ ]/ || line ~ /^[ ]*[-*+][ ]/) steps++
  low = tolower(line)
  if (low ~ /(^|[^a-z])(if|when|unless|se|quando|caso|si|cuando)([^a-z]|$)/) conds++
  if (line ~ /[0-9]/) nums++
}
END { print "B\t" body "\t" steps "\t" conds "\t" nums }
EOF
}

# kbv_fm_block_state <file> -> none | closed | unclosed
kbv_fm_block_state() {
  LC_ALL=C awk '
    NR == 1 { if ($0 ~ /^---[ \t]*\r?$/) { o = 1; next } ; print "none"; done = 1; exit }
    o && ($0 ~ /^---[ \t]*\r?$/ || $0 ~ /^\.\.\.[ \t]*\r?$/) { print "closed"; done = 1; exit }
    END { if (!done) print (o ? "unclosed" : "none") }' "$1"
}

# kbv_fm_parse <file> -> one JSON object:
#   {has_frontmatter, raw:{key: scalar|[items]|null}, notes:[...], h1, body:{lines,steps,conditions,numbers}}
#   notes[0] is "frontmatter partially parsed" whenever a construct was skipped.
kbv_fm_parse() {
  local file="$1" state mode tsv
  state=$(kbv_fm_block_state "$file")
  mode=body
  [ "$state" != closed ] || mode=fm
  tsv=$(kbv_tmpfile)
  LC_ALL=C awk -v mode="$mode" "$(kbv_fm_awk)" "$file" > "$tsv"
  if [ "$state" = unclosed ]; then
    printf 'N\tfrontmatter block opened at line 1 but never closed\n' >> "$tsv"
  fi
  "$KBV_JQ" -c -R -s --argjson has "$([ "$state" = closed ] && printf true || printf false)" '
    [split("\n")[] | select(length > 0) | split("\t")] as $rows
    | ([$rows[] | select(.[0] == "N") | .[1]]) as $issues
    | {has_frontmatter: $has,
       raw: (reduce ($rows[] | select(.[0] == "S" or .[0] == "K" or .[0] == "L")) as $r ({};
               if $r[0] == "S" then .[$r[1]] = ($r[2] // "")
               elif $r[0] == "K" then (if has($r[1]) and .[$r[1]] != null then . else .[$r[1]] = null end)
               else .[$r[1]] = (if (.[$r[1]] | type) == "array" then .[$r[1]] + [$r[2] // ""]
                                elif .[$r[1]] == null then [$r[2] // ""]
                                else [.[$r[1]], ($r[2] // "")] end) end)),
       notes: (if ($issues | length) > 0 then ["frontmatter partially parsed"] + ($issues | map("unsupported: " + .)) else [] end),
       h1: ([$rows[] | select(.[0] == "T") | .[1]] | first // null),
       body: ([$rows[] | select(.[0] == "B")] | first
              | {lines: (.[1] | tonumber), steps: (.[2] | tonumber), conditions: (.[3] | tonumber), numbers: (.[4] | tonumber)})}' "$tsv"
}

# ---------------------------------------------------------------------------
# frontmatter <file>
#   Parses the article, applies integration.frontmatter_map (canonical ->
#   environment key; the canonical name itself is the fallback), computes the
#   sha256 and decides the title (mapped field, else first "# " heading, else
#   the file name). `kb_verify.topic` (dotted key) is exposed as topic_override.
#   verify = no verify_when.status_in configured, or status missing, or
#   status in the list.
#   data: {path, article_id, sha256, sha12, has_frontmatter, title, title_source,
#          tags, topic, status, topic_override, raw, notes, verify, body}
# ---------------------------------------------------------------------------
kbv_cmd_frontmatter() {
  local file='' parsed sha rel stem data
  if [ $# -ne 1 ]; then
    kbv_err INVALID_INPUT "usage: frontmatter <file>"
    return 0
  fi
  if ! file=$(kbv_normalize_path "$1" "$PWD"); then
    kbv_err INVALID_INPUT "frontmatter: cannot normalize path '$1'"
    return 0
  fi
  if [ ! -f "$file" ] || [ ! -r "$file" ]; then
    kbv_err INVALID_INPUT "frontmatter: not a readable file: $file"
    return 0
  fi
  sha=$(kbv_sha256 "$file")
  rel=$(kbv_relpath "$file" "$KBV_KB_ROOT")
  stem=$(basename -- "$file")
  stem="${stem%.*}"
  parsed=$(kbv_fm_parse "$file")
  data=$(printf '%s' "$parsed" | "$KBV_JQ" -c --arg path "$file" --arg id "$rel" --arg sha "$sha" --arg stem "$stem" \
    --argjson cfg "$KBV_CONFIG_JSON" '
    def str: if . == null then null elif type == "string" then . elif type == "array" then (map(tostring) | join(", ")) else tostring end;
    def trimmed: sub("^[ \t]+"; "") | sub("[ \t]+$"; "");
    (($cfg.integration // {}) | if type == "object" then . else {} end) as $integ
    | (($integ.frontmatter_map // {}) | if type == "object" then . else {} end) as $map
    | .raw as $raw
    | def pick($canon): (($map[$canon] // $canon) | tostring) as $k | ($raw[$k] // $raw[$canon] // null);
      (pick("title") | str) as $ft
    | (pick("tags")) as $rt
    | (if ($rt | type) == "array" then ($rt | map(tostring | trimmed) | map(select(length > 0)))
       elif ($rt | type) == "string" then ($rt | split(",") | map(trimmed) | map(select(length > 0)))
       elif $rt == null then [] else [($rt | tostring)] end) as $tags
    | (($integ.verify_when.status_in? // null) | if type == "array" then map(tostring) else null end) as $status_in
    | (pick("status") | str) as $status
    | {path: $path, article_id: $id, sha256: $sha, sha12: $sha[0:12],
       has_frontmatter: .has_frontmatter,
       title: (if ($ft // "" | trimmed) != "" then ($ft | trimmed) elif (.h1 // "") != "" then .h1 else $stem end),
       title_source: (if ($ft // "" | trimmed) != "" then "frontmatter" elif (.h1 // "") != "" then "h1" else "filename" end),
       tags: $tags,
       topic: (pick("topic") | str),
       status: $status,
       topic_override: ($raw["kb_verify.topic"] | str),
       raw: $raw, notes: .notes,
       verify: (if $status_in == null or ($status_in | length) == 0 or $status == null then true else ($status_in | index($status)) != null end),
       body: .body}')
  kbv_ok "$data" "$(printf '%s' "$data" | "$KBV_JQ" -r '"title from \(.title_source); \(.notes | length) notes"')"
}

# ---------------------------------------------------------------------------
# next-bug-id --run <id> <inbox-name>
#   Inbox JSON: {title: "...", evidence: [{file, line, commit, snippet?} | "..."], topic?: "..."}
#   Returns the next free NNNN in triage_dir, the slug of the title, the
#   destination path, and the evidence with snippets redacted and capped at
#   200 characters. Writes nothing: the main agent writes the MD via Write.
#   data: {id, slug, filename, path, triage_dir, title, topic, evidence}
# ---------------------------------------------------------------------------
kbv_cmd_next_bug_id() {
  local run='' name='' title slug max=0 n id filename evidence data f base num
  while [ $# -gt 0 ]; do
    case "$1" in
      --run) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--run needs a value"; return 0; }; run="$2"; shift 2 ;;
      -*) kbv_err INVALID_INPUT "next-bug-id: unexpected option '$1' (usage: next-bug-id --run <id> <inbox-name>)"; return 0 ;;
      *)
        if [ -n "$name" ]; then kbv_err INVALID_INPUT "next-bug-id: exactly one <inbox-name> is expected"; return 0; fi
        name="$1"; shift ;;
    esac
  done
  kbv_require_run "$run" || return 0
  kbv_read_inbox "$name" || return 0
  if ! title=$(kbv_inbox_get 'if has("title") and (.title | type) != "string" then error("title") else (.title // "") end' 2>/dev/null); then
    kbv_err INVALID_INPUT "next-bug-id: title must be a string"
    return 0
  fi
  if ! evidence=$(kbv_inbox_get 'if has("evidence") and (.evidence | type) != "array" then error("evidence") else (.evidence // []) end | tojson' 2>/dev/null); then
    kbv_err INVALID_INPUT "next-bug-id: evidence must be an array"
    return 0
  fi
  title=$(printf '%s' "$title" | tr '\n\r' '  ' | kbv_redact)
  slug=$(kbv_slugify "$title")
  evidence=$(printf '%s' "$evidence" | "$KBV_JQ" -c 'map(if type == "string" then {snippet: .} else . end)')
  evidence=$(kbv_redact_json_snippets "$evidence")

  if [ -d "$KBV_TRIAGE_DIR" ]; then
    for f in "$KBV_TRIAGE_DIR"/[0-9][0-9][0-9][0-9]-*; do
      [ -e "$f" ] || continue
      base=$(basename -- "$f")
      num="${base%%-*}"
      num=$(printf '%s' "$num" | sed 's/^0*//')
      [ -n "$num" ] || num=0
      [ "$num" -le "$max" ] || max="$num"
    done
  fi
  n=$((max + 1))
  if [ "$n" -gt 9999 ]; then
    kbv_err INVALID_INPUT "triage id space exhausted in $KBV_TRIAGE_DIR (NNNN would exceed 9999)"
    return 0
  fi
  id=$(printf '%04d' "$n")
  filename="$id-$slug.md"
  if ! kbv_valid_triage_name "$filename"; then
    kbv_err INVALID_INPUT "internal: computed triage name '$filename' is invalid"
    return 0
  fi
  data=$("$KBV_JQ" -c -n --arg id "$id" --arg slug "$slug" --arg fn "$filename" --arg dir "$KBV_TRIAGE_DIR" \
    --arg title "$title" --argjson evidence "$evidence" --argjson topic "$(kbv_inbox_get '(.topic // null) | tojson')" \
    '{id: $id, slug: $slug, filename: $fn, path: ($dir + "/" + $fn), triage_dir: $dir, title: $title, topic: $topic, evidence: $evidence}')
  kbv_ok "$data" "next bug id $id"
}

# ---------------------------------------------------------------------------
# diff-check --run <id> <inbox-name>
#   Inbox JSON: {article: "<path relative to kb_root or absolute>", diff: "<unified diff>", claims?: ["c1", ...]}
#   Applies /usr/bin/patch --dry-run to a temporary copy of the article. OK
#   returns the diff text prefixed by the header line
#   "# kb-verify <run> base_sha256:<sha> claims:<ids>" and the sibling
#   <article>.kb-verify.diff path the main agent may Write. DIFF_APPLY_FAILED
#   writes nothing.
#   data: {article, article_path, diff_path, base_sha256, header, diff, claims, hunks}
# ---------------------------------------------------------------------------
kbv_cmd_diff_check() {
  local run='' name='' article diff claims_csv claims_json sha tmpd copy difff out header hunks body data
  while [ $# -gt 0 ]; do
    case "$1" in
      --run) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--run needs a value"; return 0; }; run="$2"; shift 2 ;;
      -*) kbv_err INVALID_INPUT "diff-check: unexpected option '$1' (usage: diff-check --run <id> <inbox-name>)"; return 0 ;;
      *)
        if [ -n "$name" ]; then kbv_err INVALID_INPUT "diff-check: exactly one <inbox-name> is expected"; return 0; fi
        name="$1"; shift ;;
    esac
  done
  kbv_require_run "$run" || return 0
  kbv_read_inbox "$name" || return 0
  article=$(kbv_inbox_get 'if (.article | type) == "string" then .article else "" end')
  if [ -z "$article" ]; then
    kbv_err INVALID_INPUT "diff-check: inbox .article must be a non-empty string"
    return 0
  fi
  if ! diff=$(kbv_inbox_get 'if (.diff | type) == "string" and (.diff | length) > 0 then .diff else error("diff") end' 2>/dev/null); then
    kbv_err INVALID_INPUT "diff-check: inbox .diff must be a non-empty string (unified diff)"
    return 0
  fi
  if ! claims_json=$(kbv_inbox_get 'if has("claims") and (.claims | type) != "array" then error("claims") else ((.claims // []) | map(tostring)) end | tojson' 2>/dev/null); then
    kbv_err INVALID_INPUT "diff-check: inbox .claims must be an array of ids"
    return 0
  fi
  if ! article=$(kbv_normalize_path "$article" "$KBV_KB_ROOT"); then
    kbv_err INVALID_INPUT "diff-check: cannot normalize article path"
    return 0
  fi
  if ! kbv_under "$article" "$KBV_ARTICLES_DIR"; then
    kbv_err INVALID_INPUT "diff-check: article must live under articles_dir ($KBV_ARTICLES_DIR)"
    return 0
  fi
  case "$article" in *.md) ;; *) kbv_err INVALID_INPUT "diff-check: article must be a .md file"; return 0 ;; esac
  if [ ! -f "$article" ]; then
    kbv_err INVALID_INPUT "diff-check: article not found: $article"
    return 0
  fi
  if [ ! -x /usr/bin/patch ]; then
    kbv_lib_diag 'diff-check: /usr/bin/patch is missing'
    return 70
  fi
  sha=$(kbv_sha256 "$article")
  claims_csv=$(printf '%s' "$claims_json" | "$KBV_JQ" -r 'join(",")')
  header="# kb-verify $KBV_RUN_ID base_sha256:$sha claims:$claims_csv"

  tmpd=$(kbv_tmpdir)
  copy="$tmpd/$(basename -- "$article")"
  cp "$article" "$copy"
  difff="$tmpd/proposed.diff"
  # Drop a header line the caller may already have prepended; keep the rest byte for byte.
  printf '%s\n' "$diff" | LC_ALL=C sed -e '1{/^# kb-verify /d;}' > "$difff"
  out="$tmpd/patch.out"
  if ! /usr/bin/patch --dry-run -u -s "$copy" < "$difff" > "$out" 2>&1; then
    body=$(LC_ALL=C head -c 300 "$out" | tr '\n' ' ' | kbv_redact)
    body="${body//"$copy"/<temporary copy>}"
    kbv_err DIFF_APPLY_FAILED "patch --dry-run failed on a copy of $article: $body"
    return 0
  fi
  hunks=$(LC_ALL=C grep -c '^@@' "$difff" || true)
  body=$(cat "$difff")
  data=$("$KBV_JQ" -c -n --arg article "$(kbv_relpath "$article" "$KBV_KB_ROOT")" --arg ap "$article" \
    --arg dp "${article%.md}.kb-verify.diff" --arg sha "$sha" --arg header "$header" --arg body "$body" \
    --argjson claims "$claims_json" --argjson hunks "$hunks" \
    '{article: $article, article_path: $ap, diff_path: $dp, base_sha256: $sha, header: $header,
      diff: ($header + "\n" + $body + "\n"), claims: $claims, hunks: $hunks}')
  kbv_ok "$data" "diff applies cleanly ($hunks hunks); write it to ${article%.md}.kb-verify.diff"
}
