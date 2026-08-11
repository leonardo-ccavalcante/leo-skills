---
name: n8n-validation-expert
description: Expert guidance on n8n workflow validation. Auto-load when the user says "validate", "why does this fail validation", "validation error", "false positive", "validator says", "workflow fails", or hits a known landmine. Covers validation profiles, known false positives (do NOT fix), and real landmines with workarounds.
---

# n8n Validation Expert

## Validation tool sequence

```
validate_node({nodeType, config, profile:"runtime"})   # single node
validate_workflow({workflow})                          # full pass on a local/draft workflow JSON
n8n_validate_workflow({id})                            # full pass on a deployed workflow by ID
```

## Validation profiles

| Profile | Use when |
|---|---|
| `minimal` | Required fields only. Fastest. Use to triage giant workflows. |
| `runtime` | Values + types. **Recommended default.** |
| `ai-friendly` | Relaxed for AI/agent nodes. Use when the validator over-reports on AI Agent / sub-agent (agentTool) nodes. |
| `strict` | Pre-production gate. Use before activating. |

## Known false positives — do NOT fix

These are hardcoded validator bugs. The workflows work correctly in production. Items 1–3 are unconditional — never propose changes for them. Item 4 requires the config check it describes before returning a verdict.

### 1. `vectorStoreSupabase` "cannot output ai_tool"
- **Real config**: `parameters.mode = "retrieve-as-tool"` + `parameters.toolDescription` set.
- **Why it fires**: validator has a hardcoded type rule that ignores the `mode` field.
- **Action**: return `false_positive`. Do not change the node.

### 2. `toolCode` "has no toolDescription"
- **Real config**: `parameters.description` is set (n8n's actual schema field).
- **Why it fires**: validator checks internal key `toolDescription`, not the schema field `description`.
- **Action**: return `false_positive`. Do not change the node.

### 3. googleSheets tv4.7 `operation: "getAll"` flagged as `invalid_value`
- **Real config**: `googleSheetsTool` pinned at typeVersion 4.7 where the read op IS `getAll` (live-proven; a real `n8n import:workflow` accepts it).
- **Why it fires**: the MCP registry validates against a newer googleSheets typeVersion where the op was renamed `read` — version skew.
- **Action**: return `false_positive`. Do NOT change `getAll` to `read` on a tv4.7 node — it breaks the live-proven config.

### 4. "error handler in main[0]" on a node named (Fail)/Error
- **Symptom**: `validate_workflow` says a node "appears to be an error handler but is in main[0]".
- **Why it fires**: the validator pattern-matches node NAMES containing fail/error; `main[0]` can legitimately fan out to multiple success targets.
- **Action**: check the source node's actual config. Only a real error path (source has `onError: continueErrorOutput` AND a populated `main[1]`) should move. If no error output is configured, return `false_positive` — moving the node to `main[1]` breaks a live success branch.

## Real landmines (actual bugs — use workarounds)

Full text in `n8n-pack/LANDMINES.md`. Quick reference:

### `n8n_autofix_workflow` broken with filters
`n8n_autofix_workflow` with `applyFixes:true` + `fixTypes` filter OR `confidenceThreshold:"high"` returns "No fixes needed" even when preview shows fixes.
**Workaround**: use `n8n_update_partial_workflow` with explicit `updateNode` operations instead.

### PUT settings 400
`PUT /api/v1/workflows/{id}` 400 error when `settings` object has unsupported fields.
Only these fields are accepted: `executionOrder`, `callerPolicy`, `timezone`, `saveDataErrorExecution`, `saveDataSuccessExecution`, `saveManualExecutions`, `saveExecutionProgress`, `executionTimeout`, `errorWorkflow`.
Strip `availableInMCP`, `binaryMode`, and any others before PUT.

### IF/Switch `?.` or `??` not supported
These optional chaining operators are not supported in n8n expression leftValue/rightValue.
Safe pattern: `($('NodeName').item.json.data || [{}])[0].id || ''`

### `addConnection` creates wrong type
`addConnection` with `sourceOutput:"0"` creates `type:"0"` instead of `type:"main"`.
Use `branch:"true"/"false"` for IF nodes, `case:0/1` for Switch, or `replaceConnections` to overwrite cleanly.

### `googleSheetsTool` not called by LLM
Only READ/lookup tools (`operation: "getAll"`) need a manual `toolDescription` plus an `options.queryString` filter — the auto-description for a generic "get rows" is too vague. Append/update tools (`appendOrUpdate`) auto-describe from their column schema and need none (a live-proven append tool with no toolDescription works fine); if an append tool is inert, the gap is elsewhere. Check the operation before adding anything (see known false positive #3 above).

### typeVersion v3 → v3.1+ drops systemMessage
After upgrading agent nodes, `systemMessage` moves from `parameters.systemMessage` to `parameters.options.systemMessage`. Re-read and verify content survived.

## Static validation ≠ runtime health

A clean `validate_workflow` is necessary, not sufficient — it is blind to external-API latency, retired model IDs, DB constraints, and empty lookups. For any "why is this failing" request, pull the last error execution (`n8n_executions action=get mode=error includeStackTrace=true`) and diff the failing node's real output against its contract BEFORE returning a verdict. Never return `real_bug`/`false_positive` on static output alone when executions exist. Execution payloads contain real user data — handle them as production PII: do not paste them unredacted into tickets, chat, or external LLMs.

## Output format

For every validation request, return:
- **Verdict**: `real_bug` | `false_positive` | `landmine` | `needs_more_info`
- **Cause**: one sentence
- **Fix**: exact node parameter path + value, or "do not change — known false positive"
- **Reference**: the matching false-positive/landmine section above (or `n8n-pack/LANDMINES.md` entry), if applicable

## API key staleness

If any n8n MCP tool returns 401:
```bash
curl -s -o /dev/null -w "%{http_code}\n" -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_API_URL/api/v1/workflows?limit=1"
```
`401` → the key is expired/revoked. Create a new API key in the n8n UI (Settings → n8n API), update `N8N_API_KEY` in your environment, restart your MCP client — it caches the key at launch.

**Key handling**: pass the key via env var only (`$N8N_API_KEY`) — never echo it, commit it, or paste it into chat; verify health with status-code checks (`-o /dev/null -w "%{http_code}"`) only.

## Hand-off rule

If diagnosis ends with "the workflow needs a real edit," return the verdict + fix and let the caller (or a builder agent, if your setup has one) apply the edit. Validation is read-only — don't mutate workflows directly.
