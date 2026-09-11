# kb-verify -- scripts/cmd/learn.sh
# Subcommand: memory-append. Sourced by scripts/kbv.sh; defines functions only.

KBV_MEMORY_SECTIONS='Search heuristics|Fragile assumptions|False-positive patterns'
KBV_MEMORY_MAX_LINES=60
KBV_MEMORY_MAX_STATEMENT=300

# kbv_memory_template -> the built-in memory.md used when templates/memory.md is absent
kbv_memory_template() {
  cat <<'EOF'
# kb-verify memory

Heuristics, not instructions. Curated by humans; `kbv memory-append` adds numbered lines. Keep this file at 60 lines or fewer; retire a lesson by deleting its line.

## Search heuristics

## Fragile assumptions

## False-positive patterns
EOF
}

# ---------------------------------------------------------------------------
# memory-append --run <id> <inbox-name>
#   Inbox lesson: {section: "Search heuristics"|"Fragile assumptions"|"False-positive patterns",
#                  statement: "...", article?: "articles/x.md", run?: "<run>"}
#   Provenance may also be nested, as kb-learn writes it:
#   {from: {run: "<source run>", article: "articles/x.md", claims?: [...]}}.
#   from{} wins over the top-level fields; with neither, the line records the
#   current run and "-" for the article.
#   Appends "L-nn <statement> — from: <run> <article>" at the end of the
#   section of <kb_root>/.kb-verify/memory.md (created from
#   templates/memory.md, or the built-in template, when absent; a missing
#   section header is appended at the end). Refuses with INVALID_INPUT when
#   the file would exceed 60 lines. nn = highest existing L-nn + 1.
#   data: {path, id, section, line, lines_total}
# ---------------------------------------------------------------------------
kbv_cmd_memory_append() {
  local run='' name='' section statement article from_run mem tmpl total add=1 next id line out data
  while [ $# -gt 0 ]; do
    case "$1" in
      --run) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--run needs a value"; return 0; }; run="$2"; shift 2 ;;
      -*) kbv_err INVALID_INPUT "memory-append: unexpected option '$1' (usage: memory-append --run <id> <inbox-name>)"; return 0 ;;
      *)
        if [ -n "$name" ]; then kbv_err INVALID_INPUT "memory-append: exactly one <inbox-name> is expected"; return 0; fi
        name="$1"; shift ;;
    esac
  done
  kbv_require_run "$run" || return 0
  kbv_read_inbox "$name" || return 0

  section=$(kbv_inbox_get 'if (.section | type) == "string" then .section else "" end')
  case "$section" in
    'Search heuristics'|'Fragile assumptions'|'False-positive patterns') ;;
    *) kbv_err INVALID_INPUT "memory-append: section must be one of: $KBV_MEMORY_SECTIONS"; return 0 ;;
  esac
  statement=$(kbv_inbox_get 'if (.statement | type) == "string" then .statement else "" end' | tr '\n\r\t' '   ' | sed -e 's/  */ /g' -e 's/^ //' -e 's/ $//' | kbv_redact)
  if [ -z "$statement" ]; then
    kbv_err INVALID_INPUT "memory-append: statement must be a non-empty string"
    return 0
  fi
  if [ "${#statement}" -gt "$KBV_MEMORY_MAX_STATEMENT" ]; then
    kbv_err INVALID_INPUT "memory-append: statement longer than $KBV_MEMORY_MAX_STATEMENT characters; shorten it"
    return 0
  fi
  article=$(kbv_inbox_get '((if (.from | type) == "object" then .from.article else null end) // .article) as $a
    | if ($a | type) == "string" and $a != "" then $a else "-" end' | tr '\n\r\t' '   ' | sed -e 's/^ *//' -e 's/ *$//')
  from_run=$(kbv_inbox_get '((if (.from | type) == "object" then .from.run else null end) // .run) as $r
    | if ($r | type) == "string" and $r != "" then $r else "" end' | tr '\n\r\t' '   ' | sed -e 's/^ *//' -e 's/ *$//')
  [ -n "$article" ] || article='-'
  [ -n "$from_run" ] || from_run="$KBV_RUN_ID"

  mem="$KBV_STATE_DIR/memory.md"
  if [ ! -f "$mem" ]; then
    mkdir -p "$KBV_STATE_DIR"
    tmpl="$KBV_PLUGIN_ROOT/templates/memory.md"
    if [ -f "$tmpl" ]; then
      cat "$tmpl" | kbv_atomic_write "$mem"
    else
      kbv_memory_template | kbv_atomic_write "$mem"
    fi
  fi
  if ! LC_ALL=C grep -q "^## $section[[:space:]]*\$" "$mem"; then
    add=2
  fi
  total=$(wc -l < "$mem" | tr -d ' ')
  if [ "$((total + add))" -gt "$KBV_MEMORY_MAX_LINES" ]; then
    kbv_err INVALID_INPUT "memory.md has $total lines; adding $add would exceed $KBV_MEMORY_MAX_LINES. Retire a lesson first (delete its line)"
    return 0
  fi
  next=$(LC_ALL=C sed -n 's/^L-\([0-9][0-9]*\) .*/\1/p' "$mem" | sed 's/^0*//' | awk 'BEGIN{m=0} $0+0 > m {m=$0+0} END{print m+1}')
  id=$(printf 'L-%02d' "$next")
  line="$id $statement — from: $from_run $article"

  out=$(kbv_tmpfile)
  if [ "$add" -eq 2 ]; then
    { cat "$mem"; printf '## %s\n%s\n' "$section" "$line"; } > "$out"
  else
    # Insert after the last non-blank line of the section, so the blank line
    # that separates sections stays before the next header.
    LC_ALL=C awk -v sec="## $section" -v ins="$line" '
      function flush(   i, last) {
        if (insec && !done) {
          last = 0
          for (i = 1; i <= n; i++) if (buf[i] !~ /^[ \t]*$/) last = i
          for (i = 1; i <= last; i++) print buf[i]
          print ins
          for (i = last + 1; i <= n; i++) print buf[i]
          done = 1
        } else {
          for (i = 1; i <= n; i++) print buf[i]
        }
        n = 0
      }
      BEGIN { n = 0; insec = 0; done = 0 }
      {
        if ($0 ~ /^## /) { flush(); insec = ($0 == sec); print; next }
        if (insec && !done) { buf[++n] = $0; next }
        print
      }
      END { flush() }' "$mem" > "$out"
  fi
  cat "$out" | kbv_atomic_write "$mem"
  total=$(wc -l < "$mem" | tr -d ' ')
  data=$("$KBV_JQ" -c -n --arg path "$mem" --arg id "$id" --arg section "$section" --arg line "$line" --argjson total "$total" \
    '{path: $path, id: $id, section: $section, line: $line, lines_total: $total}')
  kbv_ok "$data" "$id appended under '$section' ($total/$KBV_MEMORY_MAX_LINES lines)"
}
