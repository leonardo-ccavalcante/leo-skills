# n8n landmines — symptom → cause → workaround

The canonical registry the pack's skills reference. Every entry is production-verified.

## Validator false positives (do NOT "fix")

### 1. `vectorStoreSupabase` "cannot output ai_tool"

**Symptom**: validator says a Supabase vector store node can't connect as an `ai_tool` source to an AI Agent.
**Cause**: the n8n-mcp validator has a hardcoded type rule that ignores `mode: "retrieve-as-tool"`. Nodes configured this way ARE valid `ai_tool` sources at runtime.
**Workaround**: keep `parameters.mode = "retrieve-as-tool"` + `parameters.toolDescription` set. Ignore the warning.

### 2. `toolCode` "has no toolDescription"

**Symptom**: validator says a `toolCode` node lacks `toolDescription`.
**Cause**: validator checks internal key `toolDescription`, but the actual schema field is `parameters.description`. False alarm when `description` is set.
**Workaround**: confirm `parameters.description` is non-empty. Ignore the warning.

### 3. googleSheets tv4.7 `operation: "getAll"` flagged as `invalid_value`

**Symptom**: `validate_node`/`get_node` flag `operation: "getAll"` and suggest `"read"`.
**Cause**: the MCP registry validates against a newer googleSheets typeVersion where the op was renamed — version skew.
**Workaround**: at typeVersion 4.7 the read op IS `getAll` (accepted by a real `n8n import:workflow`). Do NOT change it to `read` on a tv4.7 node.

### 4. "error handler in main[0]" on a node named (Fail)/Error

**Symptom**: `validate_workflow` says a node "appears to be an error handler but is in main[0]".
**Cause**: the validator pattern-matches node NAMES containing fail/error; `main[0]` can legitimately fan out to multiple success targets.
**Workaround**: only a real error path (source has `onError: continueErrorOutput` AND a populated `main[1]`) should move. Otherwise it's a false positive — moving the node breaks a live success branch.

## Real bugs with workarounds

### 5. `n8n_autofix_workflow` returns "No fixes needed" despite preview

**Cause**: bug in the autofix path when filtering by `fixTypes` or `confidenceThreshold`.
**Workaround**: drop the filters, or apply manual `updateNode` operations via `n8n_update_partial_workflow`.

### 6. PUT `/api/v1/workflows/{id}` returns 400

**Cause**: the REST API rejects unknown fields in `settings`.
**Workaround**: strip `settings` to: `executionOrder, callerPolicy, timezone, saveDataErrorExecution, saveDataSuccessExecution, saveManualExecutions, saveExecutionProgress, executionTimeout, errorWorkflow`.

### 7. IF/Switch `leftValue`/`rightValue` with `?.` or `??`

**Cause**: the condition-field expression parser doesn't support optional chaining / nullish coalescing (fine in other contexts).
**Workaround**: `($('Node').item.json.data || [{}])[0].id || ''` — binary `||` chains.

### 8. `addConnection` with `sourceOutput: "0"` creates `type:"0"`

**Symptom**: connection looks fine in the UI but doesn't execute.
**Workaround**: use smart params — IF: `branch:"true"/"false"`; Switch: `case:0/1` — or `replaceConnections` with the full map.

### 9. `updateNode` with an array-index path silently no-ops

**Symptom**: `{"updates": {"parameters.conditions.conditions[1].leftValue": ...}}` returns `success:true` but nothing changes; a junk sibling key `"conditions[1]"` is written.
**Workaround**: fetch the node, patch the array in code, update the whole parent object. Always re-fetch via `curl` and assert the value changed — `operationsApplied` is not proof.

### 10. `googleSheetsTool` ignored by the LLM

**Cause/workaround**: only READ/lookup tools (`getAll`) need a manual `toolDescription` + `options.queryString` filter. Append/`appendOrUpdate` tools auto-describe from operation + column schema — adding a description blindly is the easy-path mistake; check the operation first.

### 11. Agent typeVersion v3 → v3.1+ moves the system message

**Symptom**: after a typeVersion bump the agent ignores instructions; prompt looks empty.
**Cause**: `parameters.systemMessage` → `parameters.options.systemMessage` (same for `maxIterations`).
**Workaround**: after ANY agent typeVersion upgrade, re-read the new path and re-set the prompt (`"updates": {"parameters.options.systemMessage": "=You are ..."}`).

### 12. GET→PUT round-trip strips the leading `=` from mixed-form expressions

**Symptom**: a query written literal-first (`=SELECT … {{ expr }}`) comes back as a plain literal string and fails at runtime.
**Workaround**: write fully-wrapped `={{ ... }}` expressions for query fields; re-read after every PUT.

### 13. Empty-but-healthy result = zero items = dead branch

**Symptom**: a 200-OK `[]`/0-row read emits NO items; downstream nodes never run; a splitInBatches loop-back never fires; the run "succeeds" having processed nothing.
**Workaround**: set `alwaysOutputData: true` on reads whose empty result is legitimate; make consumers tolerate a bare `{}` item; keep error item / empty item / real rows distinct.

### 14. Error output shape (`onError: continueErrorOutput`)

**Symptom**: routing on `$json.error.httpCode` never matches; downstream reads are `undefined`.
**Cause**: the error item is `{ "error": "<message string>" }` — a string, and the original input fields are gone.
**Workaround**: branch on message text; recover the original row via `$('UpstreamNode').item.json` (paired-item lineage survives error outputs).

### 15. Stale `$('Node')` references after copy/rename

**Symptom**: a copied expression references a node name that doesn't exist in this workflow; it fails silently at runtime and static validation does not flag it.
**Workaround**: extract every `$('X')` ref (regex `\$\(\s*['"]([^'"]+)['"]\s*\)`) and verify each name against the workflow's node set. Fixing a stale ref activates a previously dead path — review what now executes.

## Performance notes (verified patterns, generic form)

- Model sizing is a measured decision: upsizing the model on one sub-agent once caused a 5–10× end-to-end slowdown. Default to a small fast model; upsize only with measurements.
- Bound agents: set `maxIterations` (a low single-digit value works for most orchestrations); trim memory `contextWindowLength`; keep vector-store `topK` small (~4); give each tool to the one agent that needs it.
