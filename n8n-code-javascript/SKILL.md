---
name: n8n-code-javascript
description: Expert guidance for writing JavaScript in n8n Code nodes. Auto-load when the user asks to "write JavaScript for a Code node", "write JS", "code node", or needs to implement logic in an n8n Code node. Covers the Code node API, input/output format, common patterns, and common n8n data shapes.
---

# n8n Code Node — JavaScript

## Runtime

n8n Code nodes run Node.js. `await` is supported. Requireable libraries are a curated hard list: `crypto` and `moment` (deprecated — use the global Luxon `DateTime` instead) are reliably present; `lodash` appears in some instances — test `require('lodash')` live before relying on it. You cannot install packages, and no HTTP client is bundled.

## Input / output contract

**Input**: always an array of items. Each item has a `.json` property (the data object).

**Zero input items = this node never runs.** A 200-OK `[]` or 0-row query upstream emits NO items, so the Code node and everything after it are silently skipped (and a splitInBatches loop-back never fires). If empty is a legitimate state, set `alwaysOutputData: true` on the upstream read node and make this code tolerate the resulting bare `{}` item — distinguish error items (`item.json.error`), empty items (missing expected fields), and real rows.

**Output**: must return an array of objects with a `json` key. Every item you return becomes a node output item.

```javascript
// Minimal valid Code node
const results = [];
for (const item of $input.all()) {
  results.push({ json: { ...item.json, processed: true } });
}
return results;
```

## Core API

| Symbol | Description |
|---|---|
| `$input.all()` | Array of all input items `[{json: {...}}, ...]` |
| `$input.item` | First/current item (single-item mode) |
| `$input.first()` | First item |
| `$input.last()` | Last item |
| `$json` | Shorthand for `$input.item.json` |
| `$('NodeName').all()` | All items from a named upstream node |
| `$('NodeName').item` | Item from that node *linked to the current item* via paired-item lineage (use for per-item lookups; use `.first()` when you literally want the first item) |
| `$now` | Current Luxon DateTime |
| `$today` | Today at midnight |
| `$workflow.id` | Workflow ID |
| `$execution.id` | Execution ID |
| `$env.VAR_NAME` | Environment variable. ⚠️ `$env` values referenced in code persist into saved execution data — keep secrets in the credential store, never log or return them in items |

**`$json` is always the previous node's OUTPUT.** After a Postgres/Supabase insert, that output is the inserted DB row — upstream fields (email bodies, formatted text) are gone and read as `undefined`. Any code downstream of a DB or transform node must reference the producing node explicitly: `$('Format Node').first().json.field`, never bare `$json`.

## Common patterns

### Transform all items
```javascript
return $input.all().map(item => ({
  json: {
    id: item.json.id,
    name: (item.json.name || '').trim(),
    email: (item.json.email || '').toLowerCase(),
  }
}));
```

### Filter items
```javascript
return $input.all()
  .filter(item => item.json.status === 'active')
  .map(item => ({ json: item.json }));
```

### Aggregate / reduce
```javascript
const total = $input.all().reduce((sum, item) => sum + (item.json.amount || 0), 0);
return [{ json: { total, count: $input.all().length } }];
```

### HTTP calls
There is NO HTTP client in Code nodes — `$http`, `axios`, `fetch`, `node-fetch` are all unavailable. Do outbound HTTP with an HTTP Request node (it already runs once per input item; add SplitInBatches only for rate-limiting/batching); use Code nodes only to shape the request body before it and the response after it.

### Parse and reshape JSON
```javascript
return $input.all().map(item => {
  const raw = typeof item.json.payload === 'string'
    ? JSON.parse(item.json.payload)
    : item.json.payload;
  return { json: { id: raw.id, label: raw.name } };
});
```

### Date formatting
```javascript
// DateTime (Luxon) is available globally — do NOT require('luxon')
return $input.all().map(item => ({
  json: {
    ...item.json,
    formattedDate: DateTime.fromISO(item.json.createdAt).toFormat('dd/MM/yyyy'),
  }
}));
```

## Common n8n data shapes (examples)

### WhatsApp message body
```javascript
const msg = $('WhatsApp Trigger').item.json.messages[0].text.body;
const phone = $('WhatsApp Trigger').item.json.contacts[0].wa_id;
```
⚠️ Node references match by EXACT node name. Code copied from another workflow keeps the source workflow's trigger name — e.g. a copied `$('WhatsApp Trigger')` in a workflow whose trigger is named `Incoming Message` resolves to a nonexistent node, fails silently at runtime ("node not found"), and static validation will NOT catch it. Before shipping, extract every `$('X')` reference (regex `\$\(\s*['"]([^'"]+)['"]\s*\)`) and verify each name exists in the workflow's nodes.

### Pipedrive deal label mapping
```javascript
// <FIELD_DEF_ID> is the dealField DEFINITION id — Pipedrive deal payloads do NOT carry it as a key.
// Pattern: normalize status → label_id once, reference it downstream.
const LABEL_MAP = { hot: <HOT_ID>, warm: <WARM_ID>, cold: <COLD_ID> }; // your account's label option ids (Hot/Warm/Cold are Pipedrive's defaults)
const label_id = LABEL_MAP[(item.json.status || '').toLowerCase()] || LABEL_MAP.cold;
return [{ json: { ...item.json, label_id } }];
// Downstream nodes read it via $('Normalize Fields').item.json.label_id
```

### Supabase/Postgres rows
```javascript
const rows = $input.all(); // each item.json is one DB row
const ids = rows.map(r => r.json.id);
```

## Error handling

Only add error handling at true boundaries (external API calls, JSON.parse of untrusted input). Don't wrap internal transforms in try/catch — let errors bubble to n8n's execution error handler.

```javascript
// Only at real boundaries:
let parsed;
try {
  parsed = JSON.parse(item.json.rawPayload);
} catch {
  return [{ json: { error: 'invalid_json', raw: item.json.rawPayload } }];
}
```

**Consuming an error branch (`onError: continueErrorOutput`):** the incoming item is `{ error: "<message string>" }` — a string, so `item.json.error.httpCode` is always `undefined`; branch on the message text. The original row is gone from `$json`; recover it via `$('UpstreamNode').item.json`.

**Gate/guardrail Code nodes must fail CLOSED.** When parsing LLM output for a safety/validation gate, unparseable or garbage input must route to the blocking branch — never fall through to "pass". Prove it before shipping by running the gate's jsCode against garbage-input fixtures (see "Testing jsCode offline" below), and re-run after fixes to prove them.

## Output format rules

- Always return an **array** of `{ json: {...} }` objects.
- Never return `undefined`, `null`, or a plain object — n8n will error.
- If there's nothing to return (filtered to empty), return `[]`.
- Binary data: `{ json: {}, binary: { data: { data: base64str, mimeType: 'image/png' } } }`.

## Testing jsCode offline

Extract `parameters.jsCode` from the workflow JSON and run it with `new Function('$', '$input', 'DateTime', code)` plus small mocks (`$(name)` / `$input` backed by fixture items, a minimal Luxon `DateTime` shim). Feed it the shapes n8n really produces — error items `{error:"…"}`, alwaysOutputData `{}`, fenced/garbage LLM output — and assert on the returned items. Any gate parsing LLM output must fail CLOSED on unparseable input. Re-run the harness after fixes to prove them.
