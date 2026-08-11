---
name: n8n-expression-syntax
description: Expert guidance on n8n expression syntax. Auto-load when the user asks to "fix this expression", references "$json", "$input", "$('Node')", "$fromAI", "$now"/Luxon date formatting, asks about `?.`/`??`/optional chaining in IF or Switch conditions, expression errors, or needs to write n8n template expressions. Covers the expression engine rules, safe patterns, and common n8n data shapes.
---

# n8n Expression Syntax

## Expression basics

n8n expressions start with `=`. Two forms: fully-wrapped `={{ ... }}`, and mixed literal `=Some text {{ expr }} more text` (used e.g. in agent systemMessage). **Prefer the fully-wrapped form for Postgres `query` fields** — the REST GET→PUT round-trip silently strips the leading `=` from mixed-form queries, turning them into literal strings; re-read after every PUT to confirm the `=` survived.

```json
{ "value": "={{ $json.fieldName }}" }
```

Strings that do not start with `=` are literal — they are NOT evaluated.

## Core variables

| Variable | Available in | Description |
|---|---|---|
| `$json` | any node | Current item's JSON data (`$input.item.json` shorthand) |
| `$input` | any node | Current execution input object |
| `$input.item` | any node | Current item |
| `$input.all()` | any node | All items in current input |
| `$('NodeName')` | any node | Reference a specific node's output |
| `$('NodeName').item` | any node | Item *linked to the current item* (paired-item lineage — in loops this tracks the matching row, not item 0; use `.first()` for the literal first item) |
| `$('NodeName').first()` | any node | Literal first item from named node |
| `$('NodeName').all()` | any node | All items from named node |
| `$now` | any node | Current timestamp (Luxon DateTime) |
| `$today` | any node | Today at midnight |
| `$env` | any node | Environment variables |
| `$workflow` | any node | Workflow metadata (id, name, active) |
| `$execution` | any node | Execution metadata (id, mode) |
| `$itemIndex` | loop contexts | Current item index |
| `$runIndex` | loop contexts | Current run index |

> **`$env` caution:** a `$env.SECRET` referenced in any parameter persists into saved execution data and, if it reaches agent context, is extractable by chat users. Keep secrets in the n8n credential store. On shared/self-hosted instances, set `N8N_BLOCK_ENV_ACCESS_IN_NODE=true` to block `$env` in expressions and Code nodes.

> **`$json` is the PREVIOUS node's output, not "your data".** A DB node (Postgres/Supabase insert) replaces the item json with the DB row — fields produced further upstream become `undefined`. Across any DB/transform node, reference the producing node explicitly: `={{ $('Format Node').first().json.emailSubject }}`.

## `$fromAI()` — AI-tool parameter fills

Inside an AI Agent's tool parameters, `={{ $fromAI('key', 'description for the LLM', 'string') }}` lets the LLM fill the value at call time. Commonly used in Google Sheets write tools (`columns.value`). Mix with hardcoded expressions for identity keys — hardcode the lookup/write key (e.g. the trigger's `wa_id`) so the read tool and the write tool key on the same stable value. Only valid in tool-node parameters attached to an agent, not in ordinary nodes.

> ⚠️ **`$fromAI` values are untrusted input** — same trust level as the raw user message (hallucination or injection can set them to anything). Never let `$fromAI` fill identity/key columns (upsert match keys, user ids, phone/email) or destructive params (deletes, amounts, URLs) — hardcode those to deterministic trigger/node refs. Where a value must be model-filled, constrain it in the tool schema (type/enum, tight description) or route the tool through a toolWorkflow whose first node validates before the write — inside a plain tool node there is no way to interpose validation. This includes query fields: never string-concatenate `$fromAI` or free-text user values into a Sheets `queryString` or SQL query — a crafted value widens the filter (leaking other rows into agent context) or injects SQL.
>
> **Formula injection:** model/user-supplied values starting with `=`, `+`, `-` or `@` can execute as formulas when the sheet or its CSV export opens (`=IMPORTXML` exfiltrates); prefix-escape or strip leading formula chars on model-filled columns — and check your Sheets node's cell-format option (RAW input neutralizes formulas; USER_ENTERED does not).

## Accessing nested data

```javascript
// simple field
={{ $json.name }}

// nested object
={{ $json.contact.email }}

// array item
={{ $json.items[0].id }}

// safe array access (no ?. — safe even when the array is missing OR empty; legal in IF/Switch conditions)
={{ (($json.items || [])[0] || {}).id || '' }}
```

## The forbidden operators: `?.` and `??`

**Never use optional chaining `?.` or nullish coalescing `??` in IF/Switch `leftValue` or `rightValue`.**
n8n's expression parser does not support them in condition fields — they silently break or throw.

Safe pattern for IF/Switch conditions:
```javascript
// WRONG
={{ $('PrevNode').item.json.data?.[0]?.id ?? '' }}

// CORRECT
={{ ($('PrevNode').item.json.data || [{}])[0].id || '' }}
```

You CAN use `?.` in other expression contexts (HTTP Request body, Set node values, etc.) — the restriction is specifically in IF/Switch `leftValue`/`rightValue` fields.

> ⚠️ Collision note: the official n8n skill `n8n-expressions` (github.com/n8n-io/skills) auto-fires on the same keywords and recommends `?.`/`??` freely. Its advice is fine for Set/HTTP/Code contexts but must NOT be applied to IF/Switch `leftValue`/`rightValue` — this restriction wins.

## Date/time expressions (Luxon)

```javascript
// current ISO string
={{ $now.toISO() }}

// format
={{ $now.toFormat('yyyy-MM-dd') }}

// add days
={{ $now.plus({ days: 7 }).toISO() }}

// parse from string
={{ DateTime.fromISO($json.dateStr).toFormat('dd/MM/yyyy') }}
```

## Common n8n data shapes (examples)

### WhatsApp trigger (`$('WhatsApp Trigger').item.json`)
```javascript
// Sender phone number (wa_id is the standard WhatsApp payload field)
={{ $('WhatsApp Trigger').item.json.contacts[0].wa_id }}

// Message text
={{ $('WhatsApp Trigger').item.json.messages[0].text.body }}
```

**⚠️ Stale-ref landmine**: node refs match by exact name. An expression copied into a workflow whose trigger is named differently (e.g. `Incoming Message` instead of `WhatsApp Trigger`) points at a node that doesn't exist and fails silently at runtime — static validation won't flag it. Before shipping, extract every `$('X')` ref (regex `\$\(\s*['"]([^'"]+)['"]\s*\)`) and verify each X is in the workflow's node names. Note: fixing a stale ref activates a previously-dead path — review the downstream config that now executes.

### Pipedrive deal fields
```javascript
// Deal ID
={{ $json.id }}

// Deal label (<FIELD_DEF_ID> is the dealField DEFINITION id; option ids are per-account — e.g. Hot/Warm/Cold, Pipedrive's defaults)
// Deal payloads do NOT carry the definition id as a key — never read $json['<FIELD_DEF_ID>'].
// Pattern: normalize once, then reference it:
={{ $('Normalize Fields').item.json.label_id }}
// Writes go through the native Pipedrive node's `label` parameter.
```

### Supabase/Postgres response
```javascript
// Each returned row is its own item — $json IS the row object
={{ $json.column_name }}

// First row from a named node
={{ $('Postgres Node').first().json.column_name }}

// Count of returned rows
={{ $input.all().length }}
```

> ⚠️ **Zero rows = zero items.** A read returning `[]`/0 rows emits NO items — downstream nodes never run, so this expression never evaluates to `0`. If an empty result must still drive the flow, set `alwaysOutputData: true` on the read node; it then emits ONE empty `{}` item (item count 1, not 0) — detect the empty case with a field check like `={{ $json.column_name || '' }}`, never with `$input.all().length`.

### Error output (`onError: continueErrorOutput`)
```javascript
// The error item is { error: '<message string>' } — a STRING, no httpCode, original fields GONE
// Branch on the message text (no `?.`/`??` — see "The forbidden operators" above):
={{ String($json.error || '').includes('could not be found') }}
// Downstream nodes needing the original row must use a node reference (paired-item lineage):
={{ $('LoopOrUpstreamNode').item.json['Col'] }}
```

## String operations

```javascript
// trim and lowercase
={{ $json.email.trim().toLowerCase() }}

// template literal equivalent
={{ `Hello ${$json.name}, your order #${$json.orderId} is ready` }}

// join array
={{ $json.tags.join(', ') }}

// check includes
={{ $json.message.toLowerCase().includes('refund') }}
```

## Conditional expressions

```javascript
// ternary (supported everywhere)
={{ $json.status === 'active' ? 'Yes' : 'No' }}

// safe default
={{ $json.name || 'Unknown' }}

// nested safe access
={{ ($json.address || {}).city || 'No city' }}
```

## Multi-item expressions (SplitInBatches / loop contexts)

```javascript
// current index
={{ $itemIndex }}

// total items count
={{ $input.all().length }}

// access sibling items
={{ $input.all()[0].json.id }}
```
