---
name: n8n-node-configuration
description: Expert guidance on n8n node parameter configuration. Auto-load when the user says "build it", "create the workflow", "add nodes", "configure this node", or reports that a node parameter is missing/wrong after a typeVersion change. Covers the full node schema, typeVersion migration paths, and agent systemMessage location.
---

# n8n Node Configuration

> If you also run the official n8n-io skills plugin, it ships a skill with this same name — where the two conflict, this pack's guardrails win.

## Node schema structure

```json
{
  "id": "<uuid>",
  "name": "Human-readable label",
  "type": "n8n-nodes-base.<nodeType>",
  "typeVersion": 1,
  "position": [x, y],
  "parameters": { ... },
  "credentials": { "<credType>": { "id": "<credId>", "name": "<credName>" } }
}
```

## nodeType format — the one that bites

| Tool context | Format | Example |
|---|---|---|
| `search_nodes`, `get_node`, `validate_node` | `nodes-base.*` | `nodes-base.httpRequest` |
| `n8n_create_workflow`, `n8n_update_partial_workflow` | `n8n-nodes-base.*` | `n8n-nodes-base.httpRequest` |
| LangChain search/validate | `nodes-langchain.*` | `nodes-langchain.agent` |
| LangChain create/update | `@n8n/n8n-nodes-langchain.*` | `@n8n/n8n-nodes-langchain.agent` |

## typeVersion migration: AI Agent v3 → v3.1+

This is one of the most common post-upgrade breakages in n8n.

| Parameter | v3 path | v3.1+ path |
|---|---|---|
| System message | `parameters.systemMessage` | `parameters.options.systemMessage` |
| Max iterations | `parameters.maxIterations` | `parameters.options.maxIterations` |

**After any agent typeVersion upgrade**: re-read the live workflow JSON and verify `parameters.options.systemMessage` contains the expected prompt. If it's blank, the upgrade dropped it — restore from backup.

## Key node configuration examples

### AI Agent (LangChain)
```json
{
  "type": "@n8n/n8n-nodes-langchain.agent",
  "typeVersion": 3.1,
  "parameters": {
    "promptType": "define",
    "text": "={{ $json.message }}",
    "options": { "systemMessage": "...", "maxIterations": 5 }
  }
}
```
There is no `agentType` parameter at v3; sub-agents attach as `@n8n/n8n-nodes-langchain.agentTool` (observed at typeVersion 2.2 in a live instance). After any typeVersion bump re-verify `parameters.options.systemMessage` (see the migration table above; `n8n-pack/LANDMINES.md` #11).
Always set `parameters.options.maxIterations` (5 is a sane default) — it is the only bound on the agent's tool-call loop; without it an injected or confused agent burns tokens and hammers tools without limit. It lives under `options.*` at v3.1+ — verify it survives upgrades (same landmine as `systemMessage`).

### HTTP Request (Pipedrive notes with pin)
```json
{
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "method": "POST",
    "url": "https://api.pipedrive.com/v1/notes",
    "specifyBody": "json",
    "jsonBody": "={{ { content: $json.noteText, deal_id: $json.dealId, pinned_to_deal_flag: true } }}"
  }
}
```
`jsonBody` is a single string value with the `=` prefix — a JS object expression that n8n serializes as the JSON body. Expressions without the leading `=` are never evaluated.
The native Pipedrive node does not support `pinned_to_deal_flag`. Always use HTTP Request for notes.

### Google Sheets AI Tool
```json
{
  "type": "n8n-nodes-base.googleSheetsTool",
  "typeVersion": 4.7,
  "parameters": {
    "operation": "getAll",
    "toolDescription": "Look up the record by ID before writing",
    "options": {
      "useQueryString": true,
      "queryString": "={{ 'id = \"' + $json.recordId + '\"' }}"
    }
  }
}
```
Note the type: `n8n-nodes-base.googleSheetsTool` (a base node used as an AI tool), not a `@n8n/n8n-nodes-langchain.*` type. Only READ/lookup tools (`getAll`) need a manual `toolDescription` (the key is `toolDescription`, not `description`) plus a `queryString` filter; `append`/`appendOrUpdate` tools auto-describe from operation + column schema — a live-proven append tool with no toolDescription works fine. At tv4.7 the read op is `"getAll"`, NOT `"read"`; the MCP validator suggesting `read` is a version-skew false positive (`n8n-pack/LANDMINES.md` #3) — do not change it.
A common stable-identity variant keys the lookup on the WhatsApp payload's `contacts[0].wa_id` phone field. Phone numbers are PII — be deliberate about where they land (spreadsheets, LLM prompts, and logs each create data-processing obligations); minimize or mask where possible and check your model provider's data-processing terms.
Formula injection: model-filled cell values starting with `=`, `+`, `-`, or `@` can execute as spreadsheet formulas — escape or strip them, and check the node's cell-format option (RAW vs USER_ENTERED).

### OpenRouter chat model — missing `model` is NOT a bug
`@n8n/n8n-nodes-langchain.lmChatOpenRouter` (v1) with `parameters.options:{}` and no `model` silently runs the node default `openai/gpt-4.1-mini` — which may differ from your project's pinned default model. Never blind-patch a missing model on an active agent: pinning CHANGES behavior, it doesn't repair a crash. Treat it as an owner cost/quality decision, or pin the current effective default explicitly for zero behavior change (re-check via `get_node` — defaults shift across n8n versions).

### Webhook
```json
{
  "type": "n8n-nodes-base.webhook",
  "typeVersion": 2,
  "parameters": {
    "path": "your-path",
    "responseMode": "onReceived"
  }
}
```

### IF node (safe expression pattern, tv2)
```json
{
  "type": "n8n-nodes-base.if",
  "typeVersion": 2,
  "parameters": {
    "conditions": {
      "options": { "caseSensitive": true, "typeValidation": "strict" },
      "combinator": "and",
      "conditions": [{
        "leftValue": "={{ ($('PrevNode').item.json.data || [{}])[0].id || '' }}",
        "rightValue": "",
        "operator": { "type": "string", "operation": "notEmpty", "singleValue": true }
      }]
    }
  }
}
```
Never use `?.` or `??` in leftValue/rightValue — n8n's condition parser rejects them in IF/Switch condition fields (fine in other contexts: Set, HTTP bodies, Code — `n8n-pack/LANDMINES.md` #7).

## Backup before mutating active workflows

Always export a backup before any `n8n_update_partial_workflow` / `n8n_update_workflow` / delete on an active workflow — nothing enforces this unless you add tooling:
```bash
mkdir -p backups
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_API_URL/api/v1/workflows/<id>" \
  > "backups/<id>-$(date -u +%Y%m%dT%H%M%SZ).json"
```
Treat backup exports as production data: keep `backups/` in `.gitignore`, restrict filesystem access, and strip `pinData` before sharing an export outside the team.
Prefer staging-first: clone the workflow, edit and test it inactive, then promote — never iterate live on an active production workflow.
The pack's optional backup-guard hook (`n8n-pack/hooks/pre-tool-prod-guard.sh`) can enforce this: it blocks n8n mutation tools when no `backups/<id>-*.json` younger than 60 minutes exists.

**Key handling**: Always reference the key as `$N8N_API_KEY` from a gitignored `.env` — never type the literal key in a command (shell history persists it), never inline it in a committed `.mcp.json`, and never debug auth with `curl -v`/`--trace` (it prints the key header). Agent tooling may persist terminal output outside your repo — never print credentials at all; verify keys via status-code checks only. 401 → the key is expired/revoked: create a new API key in the n8n UI (Settings → n8n API), update `N8N_API_KEY` in your environment, restart your MCP client — it caches the key at launch.

## Editing large parameters via REST (GET → Python → PUT)

For multi-KB `jsCode` or any heavy param, don't hand-escape it into a partial update: GET the workflow, patch in Python (`str.replace`, with a dry-run asserting `OLD in / NEW in`), strip `settings` to the allowed keys, PUT back.
**Caveat**: a Postgres `query` written literal-first (`=SELECT … {{ expr }} …`) loses its leading `=` on the GET→PUT round-trip and becomes a literal string that fails at runtime. Always write fully-wrapped `={{ … }}` queries, and re-read the workflow after every PUT to confirm the `=` (and nested options) actually stuck — full-PUTs can also drop values a prior partial update set.

## `n8n_update_partial_workflow` operations

```json
[
  { "type": "addNode", "node": { "...": "full node object, full prefix" } },
  { "type": "updateNode", "nodeName": "NodeName",
    "updates": { "parameters.options.systemMessage": "=You are a..." } },
  { "type": "addConnection", "source": "NodeA", "target": "NodeB", "branch": "true" },
  { "type": "replaceConnections", "connections": { "...": "whole map" } },
  { "type": "removeNode", "nodeName": "NodeName" }
]
```

`updateNode` takes `nodeName` + `updates` (dot-notation paths), NOT `{name, parameters}` — the latter fails or no-ops.

Always pass `intent: "<short why>"` to `n8n_update_partial_workflow` — it produces better diffs and audit logs.

**Connection landmine**: `addConnection` with `sourceOutput:"0"` creates `type:"0"` instead of `type:"main"`. When connecting nodes with multiple outputs (IF, Switch), use `branch:"true"/"false"` or `case:0/1` instead of `sourceOutput`. When in doubt, use `replaceConnections` for a clean overwrite.

**Array-index landmine**: never target an array element by index in an `updates` path (e.g. `parameters.conditions.conditions[1].leftValue`) — the tool reports `success:true` but the element is unchanged and a junk sibling key like `"conditions[1]"` is written. Fetch the node, patch the array in code, and update the whole parent object (`"parameters.conditions": <full object>`). Always verify with `curl $N8N_API_URL/api/v1/workflows/<id>` that the value actually changed — do not trust the success message.

---
Last verified: 2026-08-11 against n8n cloud (agent v3/v3.1, `agentTool` tv2.2, `googleSheetsTool` tv4.7). typeVersion-pinned advice applies to those versions, not forever — re-verify after upgrades.
