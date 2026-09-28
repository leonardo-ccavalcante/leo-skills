# kb-verify -- scripts/cmd/setup.sh
# Subcommand: config-init. Sourced by scripts/kbv.sh; defines functions only.
# Runs before a config exists, so it must not rely on kbv_require_config.

KBV_CONFIG_INIT_SAMPLE=50

# Candidate environment keys per canonical field (first match by frequency wins).
kbv_config_init_candidates() {
  case "$1" in
    title) printf 'title titulo título titre titel name nome heading\n' ;;
    tags) printf 'tags etiquetas tag keywords palavras-chave palabras-clave labels categorias\n' ;;
    topic) printf 'topic topico tópico politica política policy category categoria categoría area área feature\n' ;;
    status) printf 'status estado state estagio stage workflow\n' ;;
  esac
}

# ---------------------------------------------------------------------------
# config-init <kb_root>
#   Samples the frontmatter keys of up to 50 .md files under <kb_root>,
#   guesses frontmatter_map, articles_dir/article_glob, verify_when and
#   locales (from accented-character frequency), and prints the proposed
#   config plus the three questions the human must answer. Writes nothing.
#   data: {kb_root, sampled, frontmatter_keys:{key:count}, status_values:{v:count},
#          locale_scores:{...}, config:{...}, questions:[3]}
# ---------------------------------------------------------------------------
kbv_cmd_config_init() {
  local root list f parsed keys_tsv keys_json status_key status_json dirs_tsv top_dir sampled=0
  local pt es de fr accents total_bytes locales map_json vals data article_glob articles_dir raw_tsv all
  if [ $# -ne 1 ]; then
    kbv_err INVALID_INPUT "usage: config-init <kb_root>"
    return 0
  fi
  if ! root=$(kbv_normalize_path "$1" "$PWD"); then
    kbv_err INVALID_INPUT "config-init: cannot normalize '$1'"
    return 0
  fi
  if [ ! -d "$root" ]; then
    kbv_err INVALID_INPUT "config-init: not a directory: $root"
    return 0
  fi

  list=$(kbv_tmpfile)
  all=$(kbv_tmpfile)
  find "$root" -type f -name '*.md' ! -name '*.kb-verify.diff' ! -path '*/.git/*' ! -path '*/.kb-verify/*' ! -path '*/node_modules/*' 2>/dev/null \
    | LC_ALL=C sort > "$all"
  head -n "$KBV_CONFIG_INIT_SAMPLE" "$all" > "$list"

  raw_tsv=$(kbv_tmpfile)      # key<TAB>value-or-empty per frontmatter key of every sampled file
  dirs_tsv=$(kbv_tmpfile)     # first-level directory (relative to root) of every sampled file
  pt=0; es=0; de=0; fr=0; accents=0; total_bytes=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    sampled=$((sampled + 1))
    parsed=$(kbv_fm_parse "$f")
    printf '%s' "$parsed" | "$KBV_JQ" -r '.raw | to_entries[] | .key + "\t" + (if (.value | type) == "string" then .value else "" end)' >> "$raw_tsv"
    printf '%s\n' "$(kbv_relpath "$f" "$root")" | awk -F/ '{print (NF > 1 ? $1 : ".")}' >> "$dirs_tsv"
    total_bytes=$((total_bytes + $(wc -c < "$f" | tr -d ' ')))
    pt=$((pt + $(kbv_count_chars "$f" 'ã õ ç Ã Õ Ç')))
    es=$((es + $(kbv_count_chars "$f" 'ñ ¿ ¡ Ñ')))
    de=$((de + $(kbv_count_chars "$f" 'ß ü ä ö Ü Ä Ö')))
    fr=$((fr + $(kbv_count_chars "$f" 'è œ ê È Œ Ê')))
    accents=$((accents + $(kbv_count_chars "$f" 'á é í ó ú à â ê ô ã õ ç ñ ü ö ä ß è œ')))
  done < "$list"

  keys_json=$(LC_ALL=C awk -F'\t' '{c[$1]++} END {for (k in c) print c[k] "\t" k}' "$raw_tsv" \
    | LC_ALL=C sort -t"$(printf '\t')" -k1,1nr -k2,2 \
    | "$KBV_JQ" -R -s -c '[split("\n")[] | select(length > 0) | split("\t")] | map({key: .[1], value: (.[0] | tonumber)}) | from_entries')
  map_json=$("$KBV_JQ" -c -n \
    --argjson keys "$keys_json" \
    --arg title "$(kbv_config_init_candidates title)" --arg tags "$(kbv_config_init_candidates tags)" \
    --arg topic "$(kbv_config_init_candidates topic)" --arg status "$(kbv_config_init_candidates status)" '
    def guess($canon; $cands):
      ([($cands | split(" "))[] | select(length > 0) | select($keys[.] != null)] | first) // $canon;
    {title: guess("title"; $title), tags: guess("tags"; $tags), topic: guess("topic"; $topic), status: guess("status"; $status)}')
  status_key=$(printf '%s' "$map_json" | "$KBV_JQ" -r '.status')
  status_json=$(LC_ALL=C awk -F'\t' -v k="$status_key" '$1 == k && $2 != "" {c[$2]++} END {for (v in c) print c[v] "\t" v}' "$raw_tsv" \
    | LC_ALL=C sort -t"$(printf '\t')" -k1,1nr -k2,2 \
    | "$KBV_JQ" -R -s -c '[split("\n")[] | select(length > 0) | split("\t")] | map({key: .[1], value: (.[0] | tonumber)}) | from_entries')
  top_dir=$(LC_ALL=C sort "$dirs_tsv" | uniq -c | LC_ALL=C sort -k1,1nr -k2,2 | awk 'NR == 1 {print $2}')
  [ -n "$top_dir" ] || top_dir='.'
  if [ "$top_dir" = '.' ]; then articles_dir='.'; article_glob='**/*.md'; else articles_dir="$top_dir"; article_glob="$top_dir/**/*.md"; fi

  # Locale guess: English by default; add the language whose markers dominate
  # when accented characters are frequent enough (>= 1 per 400 bytes sampled).
  locales='["en"]'
  if [ "$total_bytes" -gt 0 ] && [ "$((accents * 400))" -ge "$total_bytes" ]; then
    if [ "$pt" -ge "$es" ] && [ "$pt" -ge "$de" ] && [ "$pt" -ge "$fr" ] && [ "$pt" -gt 0 ]; then locales='["en","pt-BR"]'
    elif [ "$es" -ge "$de" ] && [ "$es" -ge "$fr" ] && [ "$es" -gt 0 ]; then locales='["en","es"]'
    elif [ "$de" -ge "$fr" ] && [ "$de" -gt 0 ]; then locales='["en","de"]'
    elif [ "$fr" -gt 0 ]; then locales='["en","fr"]'
    fi
  fi
  vals=$(printf '%s' "$status_json" | "$KBV_JQ" -c 'keys')
  data=$("$KBV_JQ" -c -n --arg root "$root" --argjson sampled "$sampled" --argjson keys "$keys_json" \
    --argjson status "$status_json" --argjson map "$map_json" --argjson locales "$locales" --argjson vals "$vals" \
    --arg adir "$articles_dir" --arg glob "$article_glob" \
    --argjson scores "$("$KBV_JQ" -c -n --argjson pt "$pt" --argjson es "$es" --argjson de "$de" --argjson fr "$fr" --argjson acc "$accents" --argjson bytes "$total_bytes" '{"pt-BR": $pt, es: $es, de: $de, fr: $fr, accented_chars: $acc, bytes: $bytes}')" '
    {kb_root: $root, sampled: $sampled, frontmatter_keys: $keys, status_values: $status, locale_scores: $scores,
     config: {version: 1, kb_root: $root, articles_dir: $adir, triage_dir: "kb-verify/triage/bugs",
              gh: {repo: "org/monorepo"},
              budgets: {search_calls_per_article: 15, fetch_calls_per_article: 40, index_i18n_files: 20},
              integration: {article_glob: $glob, locales: $locales, frontmatter_map: $map,
                            verify_when: {status_in: (if ($vals | length) > 0 then $vals else ["draft", "review"] end)},
                            bug_template: null, triage_labels: ["needs-triage", "needs-info", "ready-for-agent", "ready-for-human", "wontfix"]}},
     questions: [
       "1. Which frontmatter fields hold the title, tags, topic and status? Sampled keys (with counts): \($keys | to_entries | map("\(.key)=\(.value)") | join(", ")). Proposed frontmatter_map: \($map | tojson).",
       "2. Which folder does the rewriter write articles to? Proposed articles_dir \"\($adir)\" and article_glob \"\($glob)\" (most sampled files live there). Also set gh.repo to the org/monorepo the articles describe.",
       "3. Which status value marks an article as ready to verify? Values seen under \"\($map.status)\": \($vals | tojson). Proposed verify_when.status_in: \(if ($vals | length) > 0 then $vals else ["draft", "review"] end | tojson)."
     ]}')
  kbv_ok "$data" "sampled $sampled files; review data.config and answer data.questions, then save $KBV_CONFIG_NAME in $root"
}

# kbv_count_chars <file> <space-separated UTF-8 characters> -> total occurrences
kbv_count_chars() {
  local f="$1" chars="$2" c n=0 k
  for c in $chars; do
    # grep exits 1 when nothing matches; that is a count of 0, not an error.
    k=$( { LC_ALL=C grep -o -F -e "$c" -- "$f" 2>/dev/null || true; } | wc -l | tr -d ' ')
    n=$((n + k))
  done
  printf '%s\n' "$n"
}
