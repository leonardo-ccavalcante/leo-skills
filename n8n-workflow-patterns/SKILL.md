---
name: n8n-workflow-patterns
description: Expert guidance on n8n workflow design patterns. Auto-load when the user says "design a workflow", "I want to automate X", "what's the best way to structure Y", or asks for workflow architecture advice. Covers template search, graph proposal, common pattern archetypes, and reuse-first conventions.
---

# n8n Workflow Patterns

## Design flow

```
search_templates({query, limit:10})
→ get_template({templateId, mode:"structure"})   # nodes+connections only
→ propose graph in chat
→ wait for user approval before n8n_create_workflow
```

Never create a workflow without user approval of the proposed graph. The proposal must name real node types and reference the closest matching template.

## Reuse-first convention

Keep an inventory of your active workflows (e.g., a table in your project's CLAUDE.md: name, n8n ID, trigger, status). Common archetypes worth naming in that inventory: conversational AI + CRM, multi-path sync merge (e.g., new-record / existing-with-open-item / existing-without-open-item — preserve every branch when editing), batch content generation, session-aware webhook chat, and a dev/test mirror on a second channel (e.g., Telegram).

When the user describes an automation that resembles an existing archetype in your inventory, propose extending the existing workflow rather than creating a new one (unless they explicitly want a new one).

## Graph proposal format

```
[Trigger] → [Transform A] → [Transform B] → [Output]
                                          ↘ [Output B]
```

Include:
- Real node types using `nodes-base.*` short form
- Which credential each integration needs (reference your n8n instance's credential store names)
- Whether the workflow is net-new or a modification of an existing ID

## Common patterns

### Conversational AI (WhatsApp/Telegram)
```
WhatsApp/Telegram Trigger
→ Memory (Supabase/Postgres window buffer)
→ AI Agent (@n8n/n8n-nodes-langchain.agent)
  → Tools: googleSheetsTool, HTTP Request, Code — tool outputs are untrusted: an HTTP-fetch tool reading user-suggested URLs feeds attacker-controlled text into context; allowlist fetch domains, and never give one agent both an open-ended fetch tool and write tools
→ WhatsApp/Telegram Send
```
Default to a small, fast model (e.g. `openai/gpt-4o-mini`). Benchmark before upsizing: swapping a bigger model onto one high-traffic agent node has been observed to slow the whole pipeline 5–10x. Always set the agent's `maxIterations` — it is the only bound on the tool-call loop.

**Injection is a design problem, not a prompt problem.** The entire trigger payload is attacker-controlled (anyone can message the bot) and flows into an agent holding write-capable tools; no systemMessage phrasing prevents injection. Mitigate at design level: minimum tool set (no delete ops, no open-ended HTTP Request tool with an LLM-fillable URL — that is an exfiltration/SSRF vector), hardcode identity and destructive parameters instead of `$fromAI`, never put secrets in the systemMessage (extractable), and validate the agent's output in a fail-CLOSED Code-node gate before the Send node.

Stored injection: the Memory node replays past user messages into every later prompt, and records written by `$fromAI` tools re-enter the prompt when lookup tools read them back. Treat memory contents and lookup results as untrusted input, never as instructions.

When cloning or extending any conversational workflow, verify EVERY `$('Node')` reference matches an existing node name (extract refs with regex `\$\(\s*['"]([^'"]+)['"]\s*\)` and check membership in the node-name set) — copied trigger refs (e.g. a `$('My WhatsApp Trigger')` pointing at a renamed trigger) break silently at runtime and static validation won't catch them. Note: fixing a stale ref activates a previously dead path — review its downstream config first.

### CRM sync (Pipedrive)
```
Schedule Trigger
→ HTTP Request (Pipedrive list)
→ Split in Batches
→ IF (condition routing)
→ Pipedrive Update / HTTP Request (add note with pinned_to_deal_flag)
```
Notes must use HTTP Request with `specifyBody:"json"` + `pinned_to_deal_flag:true` — the native Pipedrive node doesn't support pinning. Same lesson generalizes: when a CRM feature is missing from the native node, fall back to HTTP Request for that call.

### Newsletter / content generation
```
Schedule / Manual Trigger
→ HTTP Request (data source)
→ AI Agent or Basic LLM Chain
→ Gmail / Google Sheets write
```

### Webhook intake → data store
```
Webhook (version:"2.0", authentication: headerAuth or provider HMAC signature check)
→ Validate payload schema (IF / Code)
→ IF / Switch (route by event type)
→ Supabase / Postgres Insert
→ (optional) Respond to Webhook
```
Never expose an unauthenticated webhook that writes to a datastore — verify a shared secret (header-auth credential) or the provider's HMAC signature and validate the payload schema before the Insert. Add an IP allowlist and/or rate limiting at the proxy where available.

### Error-branch upsert (get → 404 → create)
The `continueErrorOutput` item is just `{ error: "<message string>" }` — no `httpCode`, and the original input row is gone. Branch on the message text (e.g. IF `String($json.error || '')` contains the API's not-found phrase — no `?.`/`??`), have the create node read identity fields via `$('Batch/Trigger').item.json['Col']` not `$json`, prefer a single native create-or-update/upsert node when the API offers one, and route every error branch to a logger.

## Guardrails before proposing

- No `?.` or `??` in IF/Switch expressions — use `($('Node').item.json.field || '') `.
- `googleSheetsTool`: only READ/lookup tools (`operation: "getAll"`) need a manual `toolDescription` (the key is `toolDescription`, not `description`) plus an `options.queryString` filter — don't dump all rows. Append/`appendOrUpdate` tools auto-describe from operation + column schema; adding one blindly is the documented easy-path mistake. tv4.7 `getAll`-vs-`read` validator false positive (do NOT "fix" it): see `n8n-pack/LANDMINES.md`.
- Agent nodes: check if typeVersion is v3 or v3.1+ to know where systemMessage lives (`parameters.systemMessage` vs `parameters.options.systemMessage`).
- Pipedrive webhook default `version:"2.0"` since 2025-03-17 — check each vendor webhook node's current default API version before proposing.
- An empty-but-healthy read result (HTTP `[]`, Postgres 0 rows) emits ZERO items — the branch dies and a splitInBatches loop-back edge never fires; the execution ends "successfully" having processed nobody. On every read node whose empty result is a legitimate state (watermark lookups, consent fetches, discovery queries), set node-level `"alwaysOutputData": true` and make the consuming node tolerate a bare `{}` item. Keep the three downstream states distinct: error item (`$json.error`), empty item (`{}`), and real rows.
