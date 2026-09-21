# kb-verify -- scripts/cmd/mapping.sh
# Subcommand: mapping-update, plus kbv_mapping_apply shared with repo-index
# and gh-search (search_available:false). Sourced by scripts/kbv.sh.

KBV_MAPPING_ERR=''
KBV_MAPPING_REPO_KEYS='["name","index_commit","indexed_at","tree_partial","i18n_partial","search_available"]'

# kbv_mapping_delta_program -> jq program applying $delta/$commit/$date/$repo/$keys to a mapping document
kbv_mapping_delta_program() {
  cat <<'EOF'
.version = (.version // 1)
| .repo = ((.repo // {}) + (($delta.repo // {}) | with_entries(select(.key as $k | $keys | index($k) != null))))
| .repo.name = (.repo.name // $repo)
| .repo.search_available = (if .repo | has("search_available") then .repo.search_available else true end)
| .topics = (.topics // {})
| if ($delta.topic // "") == "" then . else
    .topics[$delta.topic] = (
      (.topics[$delta.topic] // {aliases: [], articles: [], paths: []})
      | .aliases = (((.aliases // []) + ($delta.aliases // [])) | map(tostring) | unique)
      | .articles = (((.articles // []) + (if ($delta.article // "") != "" then [$delta.article] else [] end)) | map(tostring) | unique)
      | .paths = (.paths // [])
      | reduce ($delta.hits // [])[] as $h (.;
          if any(.paths[]; .path == $h.path) then
            .paths |= map(if .path == $h.path then
                            .hits = ((.hits // 0) + 1) | .last_verified = $date | .commit = $commit | .stale = false
                            | .symbols = (((.symbols // []) + ($h.symbols // [])) | map(tostring) | unique)
                          else . end)
          else
            .paths += [{path: $h.path, symbols: (($h.symbols // []) | map(tostring) | unique), hits: 1, last_verified: $date, commit: $commit, stale: false}]
          end)
      | reduce ($delta.stale // [])[] as $p (.; .paths |= map(if .path == $p then .stale = true else . end)))
  end
EOF
}

# kbv_mapping_apply <delta-json> <commit|''> <date>
#   Reads <kb_root>/.kb-verify/mapping.json (created when absent), applies the
#   delta and rewrites it sorted (jq -S) through a temp file + mv. rc 1 with
#   KBV_MAPPING_ERR when the existing file is not a JSON object.
kbv_mapping_apply() {
  local delta="$1" commit="$2" date="$3" f="$KBV_STATE_DIR/mapping.json" cur
  KBV_MAPPING_ERR=''
  if [ -f "$f" ]; then
    if ! cur=$("$KBV_JQ" -c 'if type == "object" then . else error("not an object") end' "$f" 2>/dev/null); then
      KBV_MAPPING_ERR="mapping.json is not a JSON object: $f"
      return 1
    fi
  else
    cur='{}'
  fi
  mkdir -p "$KBV_STATE_DIR"
  printf '%s' "$cur" | "$KBV_JQ" -S --argjson delta "$delta" --arg commit "$commit" --arg date "$date" \
    --arg repo "$KBV_GH_REPO" --argjson keys "$KBV_MAPPING_REPO_KEYS" "$(kbv_mapping_delta_program)" \
    | kbv_atomic_write "$f"
}

# kbv_mapping_delta_validator -> jq program: input = inbox delta, output = array of error strings
kbv_mapping_delta_validator() {
  cat <<'EOF'
def nonempty_str: type == "string" and length > 0;
[ (if has("topic") and .topic != null and (.topic | nonempty_str | not) then "topic must be a non-empty string" else empty end),
  (if has("article") and .article != null and (.article | type) != "string" then "article must be a string" else empty end),
  (if has("aliases") and .aliases != null and ((.aliases | type) != "array" or any(.aliases[]; type != "string")) then "aliases must be an array of strings" else empty end),
  (if has("hits") and .hits != null and ((.hits | type) != "array" or any(.hits[]; type != "object" or (.path | nonempty_str | not) or (has("symbols") and .symbols != null and (.symbols | type) != "array"))) then "hits must be an array of {path, symbols?}" else empty end),
  (if has("stale") and .stale != null and ((.stale | type) != "array" or any(.stale[]; type != "string")) then "stale must be an array of paths" else empty end),
  (if has("repo") and .repo != null and (.repo | type) != "object" then "repo must be an object" else empty end),
  (if ((.topic // "") == "") and ((.hits // []) | length) + ((.stale // []) | length) + ((.aliases // []) | length) > 0 then "topic is required when hits, stale or aliases are given" else empty end),
  (if ((.topic // "") == "") and ((.repo // null) == null) then "delta is empty: give topic{hits,stale,aliases,article} and/or repo{}" else empty end)
]
EOF
}

# ---------------------------------------------------------------------------
# mapping-update --run <id> <inbox-name>
#   Inbox delta: {topic?, article?, aliases?: [..], hits?: [{path, symbols?}],
#   stale?: [path], repo?: {search_available?, ...}} -- either the whole inbox
#   document or nested under `mapping_delta`, because S8 passes the same
#   verdict-<sha12>.json it gave to append-verdict. Hits: hits += 1,
#   last_verified = today, commit = run commit, stale = false (new paths are
#   created). Stale: stale = true on existing paths (never deleted). Aliases
#   and articles are unioned. repo{} fields are merged (known keys only).
#   data: {path, topic, hits_applied, stale_applied, aliases, repo}
# ---------------------------------------------------------------------------
kbv_cmd_mapping_update() {
  local run='' name='' errors today data topic
  while [ $# -gt 0 ]; do
    case "$1" in
      --run) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--run needs a value"; return 0; }; run="$2"; shift 2 ;;
      -*) kbv_err INVALID_INPUT "mapping-update: unexpected option '$1' (usage: mapping-update --run <id> <inbox-name>)"; return 0 ;;
      *)
        if [ -n "$name" ]; then kbv_err INVALID_INPUT "mapping-update: exactly one <inbox-name> is expected"; return 0; fi
        name="$1"; shift ;;
    esac
  done
  kbv_require_run "$run" || return 0
  kbv_read_inbox "$name" || return 0
  # The S8 file carries the delta under mapping_delta; a file that IS the delta
  # (repo-index, gh-search) is used as it stands.
  KBV_INBOX_JSON=$(printf '%s' "$KBV_INBOX_JSON" | "$KBV_JQ" -c 'if (.mapping_delta | type) == "object" then .mapping_delta else . end')
  errors=$(printf '%s' "$KBV_INBOX_JSON" | "$KBV_JQ" -c "$(kbv_mapping_delta_validator)")
  if [ "$(printf '%s' "$errors" | "$KBV_JQ" 'length')" -ne 0 ]; then
    kbv_err INVALID_INPUT "mapping delta rejected: $(printf '%s' "$errors" | "$KBV_JQ" -r 'join("; ")')"
    return 0
  fi
  if [ -z "$KBV_RUN_COMMIT" ] && [ "$(kbv_inbox_get '(.hits // []) | length')" -ne 0 ]; then
    kbv_err INVALID_INPUT "run '$KBV_RUN_ID' has no pinned commit (created with --learn); hits cannot be recorded"
    return 0
  fi
  today=$(kbv_date_utc "$(kbv_now)")
  if ! kbv_mapping_apply "$KBV_INBOX_JSON" "$KBV_RUN_COMMIT" "$today"; then
    kbv_err INVALID_INPUT "$KBV_MAPPING_ERR"
    return 0
  fi
  topic=$(kbv_inbox_get '.topic // ""')
  data=$("$KBV_JQ" -c --arg topic "$topic" --arg path "$KBV_STATE_DIR/mapping.json" --argjson delta "$KBV_INBOX_JSON" \
    '{path: $path, topic: (if $topic == "" then null else $topic end),
      hits_applied: (($delta.hits // []) | length), stale_applied: (($delta.stale // []) | length),
      aliases: (if $topic == "" then [] else (.topics[$topic].aliases // []) end),
      paths: (if $topic == "" then [] else (.topics[$topic].paths // []) end),
      repo: .repo}' "$KBV_STATE_DIR/mapping.json")
  kbv_ok "$data" "mapping updated"
}
