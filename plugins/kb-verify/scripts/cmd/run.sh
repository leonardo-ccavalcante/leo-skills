# kb-verify -- scripts/cmd/run.sh
# Subcommands: armed, run-begin, pending. Sourced by scripts/kbv.sh; defines
# functions only. Helpers it relies on live in kbv.sh (kbv_require_*, kbv_now,
# ...) and lib/common.sh (kbv_find_config, kbv_load_config, kbv_ok, kbv_err).

# ---------------------------------------------------------------------------
# armed
#   No arguments. Reports whether the guard is armed from the current
#   directory (config found walking up from $PWD, or KB_VERIFY_CONFIG).
#   data: {state:"ARMED", config_path, config:{sanitized}, jq, data_dir, mock}
#      or {state:"DISARMED", jq, data_dir, cwd}
#   A config that is found but invalid is INVALID_INPUT "config invalid (<piece>)":
#   the guard denies every tool in that state, so the skill must stop.
# ---------------------------------------------------------------------------
kbv_cmd_armed() {
  local cfg data sanitized
  if [ $# -ne 0 ]; then
    kbv_err INVALID_INPUT "armed takes no arguments"
    return 0
  fi
  if ! cfg=$(kbv_find_config "$PWD"); then
    data=$("$KBV_JQ" -c -n --arg jq "$KBV_JQ" --arg dd "$KBV_DATA" --arg cwd "$PWD" \
      '{state: "DISARMED", jq: $jq, data_dir: $dd, cwd: $cwd}')
    kbv_ok "$data" "DISARMED: no $KBV_CONFIG_NAME found walking up from $PWD"
    return 0
  fi
  if ! kbv_load_config "$cfg"; then
    kbv_err INVALID_INPUT "config invalid ($KBV_CONFIG_ERROR): $cfg"
    return 0
  fi
  kbv_config_globals
  # Sanitized = only the documented keys, paths resolved, budgets with defaults.
  sanitized=$(printf '%s' "$KBV_CONFIG_JSON" | "$KBV_JQ" -c \
    --arg root "$KBV_KB_ROOT" --arg art "$KBV_ARTICLES_DIR" --arg tri "$KBV_TRIAGE_DIR" \
    --arg repo "$KBV_GH_REPO" --argjson bs "$KBV_BUDGET_SEARCH" --argjson bf "$KBV_BUDGET_FETCH" \
    --argjson bi "$KBV_BUDGET_I18N" \
    '{version: (.version // 1), kb_root: $root, articles_dir: $art, triage_dir: $tri,
      gh: {repo: $repo},
      budgets: {search_calls_per_article: $bs, fetch_calls_per_article: $bf, index_i18n_files: $bi},
      integration: ((.integration // {}) | if type == "object" then . else {} end)}')
  data=$("$KBV_JQ" -c -n --argjson config "$sanitized" --arg path "$KBV_CONFIG_PATH" \
    --arg jq "$KBV_JQ" --arg dd "$KBV_DATA" --arg mock "${KB_VERIFY_GH_MOCK:-}" \
    '{state: "ARMED", config_path: $path, config: $config, jq: $jq, data_dir: $dd, mock: ($mock != "")}')
  kbv_ok "$data" "ARMED"
}

# kbv_new_run_id -> yyyymmdd-HHMMSS-4hex (UTC clock, 4 hex from $RANDOM)
kbv_new_run_id() {
  local stamp hex
  stamp=$(date -u +%Y%m%d-%H%M%S)
  hex=$(printf '%04x' $((RANDOM % 65536)))
  printf '%s-%s\n' "$stamp" "$hex"
}

# kbv_last_commit_from_verdicts <run-id> -> commit of the last verdict of that run, or rc 1
kbv_last_commit_from_verdicts() {
  local run="$1" f="$KBV_STATE_DIR/verdicts.jsonl" c
  [ -f "$f" ] || return 1
  c=$("$KBV_JQ" -r --arg run "$run" 'select(type == "object" and .run == $run) | .commit // empty' "$f" 2>/dev/null | tail -n 1) || return 1
  [ -n "$c" ] || return 1
  printf '%s\n' "$c"
}

# ---------------------------------------------------------------------------
# run-begin [--resume <id>] [--learn]
#   Creates runs/<id>/{run.json, inbox/, cache/}. Pins the default-branch
#   commit (two gh calls, or the mock's fixed SHA). --learn creates the inbox
#   without touching GitHub (commit: null). --resume reuses the commit from
#   run.json or, when the run dir was cleaned, from the last verdict of that
#   run in verdicts.jsonl.
#   data: {run, commit, run_dir, inbox, cache, resumed, learn, repo}
# ---------------------------------------------------------------------------
kbv_cmd_run_begin() {
  local resume='' learn=false resumed=false run='' run_dir commit='' now iso data existing tries=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --resume)
        if [ $# -lt 2 ]; then kbv_err INVALID_INPUT "--resume needs a run id"; return 0; fi
        resume="$2"; shift 2 ;;
      --learn) learn=true; shift ;;
      *) kbv_err INVALID_INPUT "run-begin: unexpected argument '$1' (usage: run-begin [--resume <id>] [--learn])"; return 0 ;;
    esac
  done
  now=$(kbv_now)
  iso=$(kbv_iso_utc "$now")

  if [ -n "$resume" ]; then
    if ! kbv_valid_run_id "$resume"; then
      kbv_err INVALID_INPUT "run id must match ^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$"
      return 0
    fi
    run="$resume"
    run_dir="$KBV_DATA/runs/$run"
    resumed=true
    if [ -f "$run_dir/run.json" ]; then
      if ! existing=$("$KBV_JQ" -c 'if type == "object" then . else error("x") end' "$run_dir/run.json" 2>/dev/null); then
        kbv_err INVALID_INPUT "run.json malformed: $run_dir/run.json"
        return 0
      fi
      commit=$(printf '%s' "$existing" | "$KBV_JQ" -r '.commit // ""')
      learn=$(printf '%s' "$existing" | "$KBV_JQ" -r 'if .learn == true then "true" else "false" end')
      mkdir -p "$run_dir/inbox" "$run_dir/cache"
      printf '%s' "$existing" | "$KBV_JQ" -c --arg ts "$iso" '.resumed = true | .resumed_at = $ts' | kbv_atomic_write "$run_dir/run.json"
    else
      if ! commit=$(kbv_last_commit_from_verdicts "$run"); then
        if [ "$learn" = true ]; then
          commit=''
        else
          kbv_err INVALID_INPUT "unknown run '$run': no run.json and no verdict of that run in verdicts.jsonl"
          return 0
        fi
      fi
      kbv_write_run_json "$run" "$commit" "$iso" "$learn" true
    fi
  else
    while :; do
      run=$(kbv_new_run_id)
      run_dir="$KBV_DATA/runs/$run"
      [ -e "$run_dir" ] || break
      tries=$((tries + 1))
      if [ "$tries" -ge 5 ]; then
        kbv_err INVALID_INPUT "could not allocate a fresh run id under $KBV_DATA/runs"
        return 0
      fi
    done
    if [ "$learn" = true ]; then
      commit=''
    else
      if ! kbv_tx_resolve_commit; then
        kbv_tx_fail
        return 0
      fi
      commit="$KBV_TX_OUT"
    fi
    kbv_write_run_json "$run" "$commit" "$iso" "$learn" false
  fi

  data=$("$KBV_JQ" -c -n --arg run "$run" --arg commit "$commit" --arg dir "$run_dir" \
    --argjson resumed "$resumed" --argjson learn "$learn" --arg repo "$KBV_GH_REPO" \
    '{run: $run, commit: (if $commit == "" then null else $commit end), run_dir: $dir,
      inbox: ($dir + "/inbox"), cache: ($dir + "/cache"), resumed: $resumed, learn: $learn, repo: $repo}')
  kbv_ok "$data" "run $run ready"
}

# kbv_write_run_json <run> <commit|''> <iso> <learn:true|false> <resumed:true|false>
kbv_write_run_json() {
  local run="$1" commit="$2" iso="$3" learn="$4" resumed="$5" dir="$KBV_DATA/runs/$1"
  mkdir -p "$dir/inbox" "$dir/cache"
  "$KBV_JQ" -c -n --arg run "$run" --arg repo "$KBV_GH_REPO" --arg commit "$commit" --arg ts "$iso" \
    --argjson learn "$learn" --argjson resumed "$resumed" \
    --argjson bs "$KBV_BUDGET_SEARCH" --argjson bf "$KBV_BUDGET_FETCH" \
    '{run: $run, repo: $repo, commit: (if $commit == "" then null else $commit end),
      started_at: $ts, learn: $learn, resumed: $resumed, search_available: true,
      budgets: {search_calls_per_article: $bs, fetch_calls_per_article: $bf}}' \
    | kbv_atomic_write "$dir/run.json"
}

# ---------------------------------------------------------------------------
# pending --run <id> <dir>
#   Lists the articles under <dir> that match integration.article_glob and are
#   not concluded in this run. Concluded = the latest verdict of this run for
#   the article carries the file's current sha256 AND its inconclusive_reason
#   is not RATE_LIMITED or GH_AUTH. Glob handling is deliberately simple: the
#   part before the first "*" is the base directory (relative to kb_root) and
#   the last segment is the file-name pattern given to `find -name`.
#   data: {run, dir, glob, pending:[{id,path,sha256,sha12,reason}], done:[{id,sha12,verdict}], total}
# ---------------------------------------------------------------------------
kbv_cmd_pending() {
  local run='' dir='' glob base name_pat base_abs f rel sha tsv verdicts vfile data
  while [ $# -gt 0 ]; do
    case "$1" in
      --run)
        if [ $# -lt 2 ]; then kbv_err INVALID_INPUT "--run needs a run id"; return 0; fi
        run="$2"; shift 2 ;;
      -*) kbv_err INVALID_INPUT "pending: unexpected option '$1' (usage: pending --run <id> <dir>)"; return 0 ;;
      *)
        if [ -n "$dir" ]; then kbv_err INVALID_INPUT "pending: exactly one <dir> is expected"; return 0; fi
        dir="$1"; shift ;;
    esac
  done
  kbv_require_run "$run" || return 0
  if [ -z "$dir" ]; then
    kbv_err INVALID_INPUT "pending: <dir> is required"
    return 0
  fi
  if ! dir=$(kbv_normalize_path "$dir" "$PWD"); then
    kbv_err INVALID_INPUT "pending: cannot normalize <dir>"
    return 0
  fi
  if [ ! -d "$dir" ]; then
    kbv_err INVALID_INPUT "pending: not a directory: $dir"
    return 0
  fi

  glob=$(kbv_config_get '.integration.article_glob // "**/*.md"')
  # Last segment -> file-name pattern; the literal directory part before the
  # first "*" -> base dir under kb_root ("articles/**/*.md" -> articles,
  # "articles/sub*/x.md" -> articles, "*.md" -> kb_root, "docs/x.md" -> docs).
  name_pat="${glob##*/}"
  [ -n "$name_pat" ] || name_pat='*.md'
  case "$glob" in
    *\**)
      base="${glob%%\**}"
      case "$base" in
        ''|*/) base="${base%/}" ;;
        *) base=$(dirname -- "$base") ;;
      esac
      ;;
    *) base=$(dirname -- "$glob") ;;
  esac
  [ "$base" != '.' ] || base=''
  if [ -n "$base" ]; then base_abs="$KBV_KB_ROOT/$base"; else base_abs="$KBV_KB_ROOT"; fi

  tsv=$(kbv_tmpfile)
  find "$dir" -type f -name "$name_pat" ! -name '*.kb-verify.diff' ! -path '*/.git/*' ! -path '*/.kb-verify/*' 2>/dev/null \
    | LC_ALL=C sort \
    | while IFS= read -r f; do
        kbv_under "$f" "$base_abs" || continue
        sha=$(kbv_sha256 "$f") || continue
        rel=$(kbv_relpath "$f" "$KBV_KB_ROOT")
        printf '%s\t%s\t%s\n' "$rel" "$f" "$sha"
      done > "$tsv"

  vfile="$KBV_STATE_DIR/verdicts.jsonl"
  verdicts='[]'
  if [ -f "$vfile" ]; then
    if ! verdicts=$("$KBV_JQ" -c -s --arg run "$KBV_RUN_ID" '[.[] | select(type == "object" and .run == $run)]' "$vfile" 2>/dev/null); then
      kbv_err INVALID_INPUT "verdicts.jsonl malformed: $vfile"
      return 0
    fi
  fi

  data=$("$KBV_JQ" -c -R -s --argjson v "$verdicts" --arg run "$KBV_RUN_ID" --arg dir "$dir" --arg glob "$glob" '
    (reduce $v[] as $x ({}; .[$x.article.id // ""] = {sha: ($x.article.sha256 // ""), reason: ($x.inconclusive_reason // ""), verdict: ($x.verdict // "")})) as $last
    | [split("\n")[] | select(length > 0) | split("\t") | {id: .[0], path: .[1], sha256: .[2], sha12: .[2][0:12]}] as $arts
    | ($arts | map(. as $a | ($last[$a.id] // null) as $l
        | if $l == null then . + {reason: "new"}
          elif $l.sha != $a.sha256 then . + {reason: "sha_changed"}
          elif ($l.reason == "RATE_LIMITED" or $l.reason == "GH_AUTH") then . + {reason: ("transient:" + $l.reason)}
          else . + {done: true, verdict: $l.verdict} end)) as $all
    | {run: $run, dir: $dir, glob: $glob,
       pending: [$all[] | select(.done != true) | {id, path, sha256, sha12, reason}],
       done: [$all[] | select(.done == true) | {id, sha12, verdict}],
       total: ($all | length)}' "$tsv")
  kbv_ok "$data" "$(printf '%s' "$data" | "$KBV_JQ" -r '"\(.pending | length) pending of \(.total)"')"
}
