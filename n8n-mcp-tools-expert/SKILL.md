---
name: n8n-mcp-tools-expert
description: Expert guidance for n8n MCP tool usage. Auto-load when the user asks to find a node, asks "what node does X", "which node for Y", or wants to discover n8n integrations. Also auto-load when a create/update or search MCP call fails with "Node not found". Covers search_nodes → get_node discovery flow, the format trap (nodes-base.* vs n8n-nodes-base.*), and result interpretation.
---

# n8n MCP Tools Expert

> Requires the community `n8n-mcp` server (czlonkowski/n8n-mcp) connected; the official n8n instance MCP server and the REST API via `curl` are alternatives.

## Node discovery flow

```
search_nodes({query, limit:20, mode:"OR"})
→ get_node({nodeType:"nodes-base.<name>", detail:"standard"})
```

Use `detail:"full"` only if `standard` is missing a specific property the user needs. It returns much more data — only worth it for edge cases.

## The format trap (most common mistake)

n8n MCP tools use **two different prefix formats** for the same nodes. Mixing them causes "Node not found" silently.

| Context | Prefix format | Example |
|---|---|---|
| `search_nodes`, `get_node`, `validate_node` | `nodes-base.*` | `nodes-base.slack` |
| `n8n_create_workflow`, `n8n_update_partial_workflow` | `n8n-nodes-base.*` | `n8n-nodes-base.slack` |
| LangChain nodes (search/validate) | `nodes-langchain.*` | `nodes-langchain.agent` |
| LangChain nodes (create/update) | `@n8n/n8n-nodes-langchain.*` | `@n8n/n8n-nodes-langchain.agent` |

`search_nodes` returns **both** as `nodeType` (short form) and `workflowNodeType` (full form). Always read the correct field for the next call.

## Discovery result format

Return to the user:
- A short list of candidate node types (`nodes-base.*` short form) with a one-line use case each.
- A recommendation with rationale (cost, latency, feature fit).
- Next step: confirm and proceed to create/update (or hand off to your builder agent, if your setup has one), or ask for more detail.

## Common search strategies

- Prefer `mode:"OR"` for broad discovery.
- For integrations (e.g., "send to Slack"), search the service name directly: `search_nodes({query:"slack"})`.
- For transforms (e.g., "loop over items"), search the pattern: `search_nodes({query:"loop split items"})`.
- For AI/LLM nodes, search `search_nodes({query:"ai agent llm"})` — LangChain-based nodes appear under `nodes-langchain.*` (short form); use `@n8n/n8n-nodes-langchain.*` only in create/update payloads.

## Available MCP tools — community server (czlonkowski `n8n-mcp`, the driver)

Tool surface: n8n-MCP by Romuald Czlonkowski — https://github.com/czlonkowski/n8n-mcp (MIT).

> **Pin the server version.** Launch a reviewed release (`npx n8n-mcp@x.y.z`, never `-y` latest) — this server proxies an API key that is root-equivalent on most n8n plans. Verify provenance (npm package ↔ GitHub source) and clear it through your security review before use.

- `search_nodes` — full-text search across node types
- `get_node` — fetch node schema at `standard` or `full` detail
- `validate_node` — validate a single node config against profile
- `validate_workflow` — full workflow validation pass
- `n8n_create_workflow` — create new workflow
- `n8n_update_partial_workflow` — patch existing workflow via operations
  - ⚠️ `updateNode` `updates` paths must NOT contain an array index (e.g. `parameters.conditions.conditions[1].leftValue`) — the op reports success but silently no-ops and writes a junk sibling key named `conditions[1]`. Fetch the node, patch the array in code, and update the whole parent object (`parameters.conditions`) instead. Always re-fetch via `curl $N8N_API_URL/api/v1/workflows/<id>` and assert the value actually changed — `operationsApplied` is not proof.
- `search_templates` — search community template library
- `get_template` — fetch template at `structure` (nodes+connections) or `full` detail
- `n8n_executions` — list recent executions for a workflow
  - ⚠️ REST `/api/v1` has no run endpoint — manual-trigger workflows can't be executed via the API; test via the official server's `execute_workflow` or a temporary webhook-harness workflow. `GET /api/v1/executions` omits running executions unless you add `?status=running`.
- `n8n_autofix_workflow` — preview or apply auto-fixes
  - ⚠️ With `fixTypes`/`confidenceThreshold` filters it often returns "No fixes" — drop the filters or do manual `updateNode` ops. More landmines: `n8n-pack/LANDMINES.md`.

A second, official n8n MCP server (the verifier) may also be connected — its tool names differ, and calling a tool on the wrong server fails with "tool not found". Check `/mcp` first. Division of labor: the community server drives discovery and surgical partial edits; the official server independently validates, tests, and executes; the REST API (`curl` against `/api/v1` with the `X-N8N-API-KEY` header) is the always-available fallback.

## API key staleness check

If any MCP tool returns 401:
```bash
curl -s -o /dev/null -w "%{http_code}\n" -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_API_URL/api/v1/workflows?limit=1"
```

> **Key handling:** the key lives only in the environment (gitignored `.env` or a secret manager) — never paste it literally into commands, commit it, or print it; don't debug auth with `curl -v` (it echoes headers). The `-o /dev/null -w "%{http_code}"` shape is deliberate: status code only, no body, no secrets in logs.

`401` → the key is expired or revoked. Create a new API key in the n8n UI (Settings → n8n API), update `N8N_API_KEY` in your environment, then restart your MCP client — it caches the key at launch.
