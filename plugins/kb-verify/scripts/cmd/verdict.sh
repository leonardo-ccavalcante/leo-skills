# kb-verify -- scripts/cmd/verdict.sh
# Subcommand: append-verdict. Sourced by scripts/kbv.sh; defines functions only.

KBV_VERDICTS='CORRECT DOC_OUTDATED CODE_BUG INCONCLUSIVE'
KBV_INCONCLUSIVE_REASONS='NOT_LOCATED PARTIAL_EVIDENCE AMBIGUOUS_INTENT NEEDS_RUNTIME ARTICLE_UNPARSEABLE BUDGET_EXHAUSTED RATE_LIMITED GH_AUTH SEARCH_UNAVAILABLE DIFF_APPLY_FAILED SKEPTIC_REFUTED SKEPTIC_UNSURE SCRIPT_ERROR'

# kbv_verdict_validator -> jq program: input = the record, output = array of error strings
kbv_verdict_validator() {
  cat <<'EOF'
def is_int: type == "number" and (tostring | test("^[0-9]+$"));
def is_pos_int: type == "number" and (tostring | test("^[1-9][0-9]*$"));
def nonempty_str: type == "string" and length > 0;
def in_list($list): . as $v | ($list | index($v)) != null;
def claim_errs($i):
  if type != "object" then ["claims[\($i)] must be an object"] else
  [ (if (.id | nonempty_str | not) then "claims[\($i)].id must be a non-empty string" else empty end),
    (if (.type | nonempty_str | not) then "claims[\($i)].type must be a non-empty string" else empty end),
    (if (.material | type) != "boolean" then "claims[\($i)].material must be a boolean" else empty end),
    (if (.text | type) != "string" then "claims[\($i)].text must be a string" else empty end),
    (if (.status | nonempty_str | not) then "claims[\($i)].status must be a non-empty string" else empty end),
    (if (.status == "SUPPORTED" or .status == "CONTRADICTED") then
       (if (.evidence | type) != "array" or (.evidence | length) == 0 then "claims[\($i)] with status \(.status) needs at least one evidence" else
          (.evidence | to_entries[] | .key as $j | .value
           | if type != "object" or (.file | nonempty_str | not) or (.line | is_pos_int | not) or (.commit | nonempty_str | not)
             then "claims[\($i)].evidence[\($j)] needs file (string), line (positive integer) and commit (string)" else empty end) end)
     else empty end),
    (if has("intent") and .intent != null then
       (if (.intent | type) != "object" then "claims[\($i)].intent must be an object"
        elif .intent.kind == "none" then
          (if (.intent | has("agrees_with")) and .intent.agrees_with != null and (.intent.agrees_with | in_list(["article", "code"]) | not)
           then "claims[\($i)].intent.agrees_with must be article|code when present" else empty end)
        elif (.intent.agrees_with | in_list(["article", "code"]) | not) then "claims[\($i)].intent.agrees_with must be article|code"
        else empty end)
     else empty end)
  ] end;
def errs($run; $verdicts; $reasons):
  [ (if (.verdict | in_list($verdicts) | not) then "verdict must be one of \($verdicts | join("|"))" else empty end),
    (if (.article | type) != "object" then "article{} must be an object" else
       ( (if (.article.id | nonempty_str | not) then "article.id must be a non-empty string" else empty end),
         (if (.article.sha256 | type) != "string" or (.article.sha256 | test("^[0-9a-f]{64}$") | not) then "article.sha256 must be 64 lowercase hex" else empty end),
         (if (.article.title | type) != "string" then "article.title must be a string" else empty end) ) end),
    (if (.commit | nonempty_str | not) then "commit must be a non-empty string" else empty end),
    (if has("run") and .run != $run then "run does not match --run" else empty end),
    (if (.claims | type) != "array" then "claims must be an array" else (.claims | to_entries[] | .key as $i | .value | claim_errs($i)[]) end),
    (if (.investigator | type) != "object" then "investigator{} missing or not an object" else
       ( (if (.investigator.layer | in_list(["a", "b", "c", "d", "e"]) | not) then "investigator.layer must be one of a-e" else empty end),
         (if (.investigator.anchor_type | type) != "string" then "investigator.anchor_type must be a string" else empty end),
         (["search_calls", "fetch_calls", "seconds"][] as $k | if (.investigator[$k] | is_int | not) then "investigator.\($k) must be a non-negative integer" else empty end) ) end),
    (if has("kac") and .kac != null and (.kac | type) != "array" then "kac must be an array" else empty end),
    (if has("notes") and .notes != null and (.notes | type) != "array" then "notes must be an array" else empty end),
    (if has("skeptic") and .skeptic != null and (.skeptic | type) != "object" then "skeptic must be an object" else empty end),
    (if has("actions") and .actions != null and (.actions | type) != "object" then "actions must be an object" else empty end),
    (if .verdict == "CODE_BUG" or .verdict == "DOC_OUTDATED" then
       (if (.skeptic | type) != "object" or .skeptic.result != "CONFIRMED" then "\(.verdict) requires skeptic.result CONFIRMED" else empty end)
     else empty end),
    (if .verdict == "CODE_BUG" then
       ( (if (.actions | type) != "object" or (.actions.bug_report | nonempty_str | not) then "CODE_BUG requires actions.bug_report" else empty end),
         (if ([(.claims // [])[]? | select(type == "object" and .material == true and .status == "CONTRADICTED" and ((.intent | type) == "object" and .intent.agrees_with == "article"))] | length) == 0
          then "CODE_BUG requires a material CONTRADICTED claim with intent.agrees_with article" else empty end) )
     else empty end),
    (if .verdict == "DOC_OUTDATED" then
       (if (.actions | type) != "object" or (.actions.doc_diff | nonempty_str | not) then "DOC_OUTDATED requires actions.doc_diff" else empty end)
     else empty end),
    (if .verdict == "INCONCLUSIVE" then
       (if (.inconclusive_reason | in_list($reasons) | not) then "INCONCLUSIVE requires inconclusive_reason in \($reasons | join("|"))" else empty end)
     else
       (if has("inconclusive_reason") and .inconclusive_reason != null then "inconclusive_reason is only allowed for INCONCLUSIVE" else empty end)
     end)
  ];
if type != "object" then ["record must be a JSON object"] else errs($run; $verdicts; $reasons) end
EOF
}

# ---------------------------------------------------------------------------
# append-verdict --run <id> <inbox-name>
#   Validates the record (see kbv_verdict_validator), redacts every snippet,
#   stamps run/recorded_at, drops the inbox-only mapping_delta (mapping-update
#   reads it from the inbox file), and appends one line to
#   <kb_root>/.kb-verify/verdicts.jsonl under a mkdir lock. Nothing is
#   written when validation fails (INVALID_INPUT lists the problems).
#   data: {run, article_id, sha256, verdict, inconclusive_reason, path, line_no, redacted_snippets}
# ---------------------------------------------------------------------------
kbv_cmd_append_verdict() {
  local run='' name='' errors record lock vfile line_no now iso data nsnip tries=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --run) [ $# -ge 2 ] || { kbv_err INVALID_INPUT "--run needs a value"; return 0; }; run="$2"; shift 2 ;;
      -*) kbv_err INVALID_INPUT "append-verdict: unexpected option '$1' (usage: append-verdict --run <id> <inbox-name>)"; return 0 ;;
      *)
        if [ -n "$name" ]; then kbv_err INVALID_INPUT "append-verdict: exactly one <inbox-name> is expected"; return 0; fi
        name="$1"; shift ;;
    esac
  done
  kbv_require_run "$run" || return 0
  kbv_read_inbox "$name" || return 0

  errors=$(printf '%s' "$KBV_INBOX_JSON" | "$KBV_JQ" -c --arg run "$KBV_RUN_ID" \
    --argjson verdicts "$(printf '%s' "$KBV_VERDICTS" | "$KBV_JQ" -R -c 'split(" ")')" \
    --argjson reasons "$(printf '%s' "$KBV_INCONCLUSIVE_REASONS" | "$KBV_JQ" -R -c 'split(" ")')" \
    "$(kbv_verdict_validator)")
  if [ "$(printf '%s' "$errors" | "$KBV_JQ" 'length')" -ne 0 ]; then
    kbv_err INVALID_INPUT "verdict record rejected: $(printf '%s' "$errors" | "$KBV_JQ" -r '.[0:6] | join("; ")')"
    return 0
  fi

  now=$(kbv_now)
  iso=$(kbv_iso_utc "$now")
  nsnip=$(printf '%s' "$KBV_INBOX_JSON" | "$KBV_JQ" '[paths(type == "string") | select(.[-1] == "snippet")] | length')
  record=$(kbv_redact_json_snippets "$KBV_INBOX_JSON")
  # mapping_delta is inbox-only (references/verdict-schema.md): mapping-update
  # reads it from the same file, and kb-learn should not see it in the record.
  record=$(printf '%s' "$record" | "$KBV_JQ" -c --arg run "$KBV_RUN_ID" --arg ts "$iso" \
    '.run = $run | .recorded_at = $ts | .notes = (.notes // []) | .kac = (.kac // []) | del(.mapping_delta)')

  mkdir -p "$KBV_STATE_DIR"
  vfile="$KBV_STATE_DIR/verdicts.jsonl"
  lock="$vfile.lock"
  while ! mkdir "$lock" 2>/dev/null; do
    tries=$((tries + 1))
    if [ "$tries" -ge 50 ]; then
      kbv_err INVALID_INPUT "verdicts.jsonl is locked by another writer ($lock); retry"
      return 0
    fi
    sleep 0.1
  done
  printf '%s\n' "$record" >> "$vfile"
  rmdir "$lock"
  line_no=$(wc -l < "$vfile" | tr -d ' ')

  data=$(printf '%s' "$record" | "$KBV_JQ" -c --arg path "$vfile" --argjson line "$line_no" --argjson nsnip "$nsnip" \
    '{run: .run, article_id: .article.id, sha256: .article.sha256, verdict: .verdict,
      inconclusive_reason: (.inconclusive_reason // null), path: $path, line_no: $line, redacted_snippets: $nsnip}')
  kbv_ok "$data" "verdict appended as line $line_no"
}
