---
name: n8n-code-python
description: Expert guidance for writing Python in n8n Code nodes. Auto-load when the user asks to "write Python for a Code node", "python code node", or needs Python logic in n8n. Covers the Python Code node API, input/output format, available libraries, and common patterns.
---

# n8n Code Node — Python

## Runtime

n8n Python Code nodes run Python 3. The environment is sandboxed — only standard library and a small set of pre-installed packages are available. `asyncio` is NOT supported; all code is synchronous.

## Input / output contract

**Input**: `_input` is an accessor object — `_input.all()` returns the list of input items; each item has a `json` key.

**Zero input items = this node never runs.** An empty `[]`/0-row upstream result emits no items and silently skips this node. If empty is a legitimate state, set `alwaysOutputData: true` on the upstream read node and make the code tolerate a bare `{}` item (`if not item["json"].get("expected_field"): …`), distinguishing it from an error item and from real rows.

**Output**: must `return` a list of dicts, each with a `json` key.

```python
# Minimal valid Python Code node
results = []
for item in _input.all():
    results.append({"json": {**item["json"], "processed": True}})
return results
```

## Core API

| Symbol | Description |
|---|---|
| `_input.all()` | List of all input items `[{"json": {...}}, ...]` |
| `_input.item` | First/current item |
| `_input.first()` | First item |
| `_input.last()` | Last item |
| `_json` | Shorthand for `_input.item["json"]` |
| `_env["VAR_NAME"]` | Environment variable — never write secrets read from `_env` into returned `json` (execution data is visible in the UI and logs) |
| `_now` | Current datetime (ISO string) |

Note: cross-node references exist in Python with the underscore prefix — `_('NodeName').all()` / `_('NodeName').first()` — mirroring JS `$('NodeName')`.

## Available libraries

Standard library is fully available. Commonly used modules (all stdlib):
- `json` (stdlib)
- `re` (stdlib)
- `datetime` (stdlib)
- `math` (stdlib)
- `hashlib` (stdlib)
- `base64` (stdlib)
- `urllib` (stdlib)

If you need `requests` or other packages, use an HTTP Request node instead of a Code node.

## Common patterns

### Transform all items
```python
return [
    {
        "json": {
            "id": item["json"]["id"],
            "name": (item["json"].get("name") or "").strip(),
            "email": (item["json"].get("email") or "").lower(),
        }
    }
    for item in _input.all()
]
```

### Filter items
```python
return [
    {"json": item["json"]}
    for item in _input.all()
    if item["json"].get("status") == "active"
]
```

### Aggregate
```python
items = _input.all()
total = sum(item["json"].get("amount", 0) for item in items)
return [{"json": {"total": total, "count": len(items)}}]
```

### Parse JSON string
```python
import json

results = []
for item in _input.all():
    raw = item["json"].get("payload", "{}")
    if isinstance(raw, str):
        data = json.loads(raw)
    else:
        data = raw
    results.append({"json": {"id": data.get("id"), "label": data.get("name")}})
return results
```

### Date formatting
```python
from datetime import datetime

return [
    {
        "json": {
            **item["json"],
            "formatted_date": datetime.fromisoformat(
                item["json"]["createdAt"].replace("Z", "+00:00")
            ).strftime("%d/%m/%Y"),
        }
    }
    for item in _input.all()
]
```

### Regex extraction
```python
import re

pattern = re.compile(r'\b[A-Z]{3}-\d{4}\b')
results = []
for item in _input.all():
    text = item["json"].get("message", "")
    matches = pattern.findall(text)
    results.append({"json": {**item["json"], "codes": matches}})
return results
```

### Text cleaning / normalization
```python
import re

def clean(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

return [
    {"json": {**item["json"], "clean_text": clean(item["json"].get("text", ""))}}
    for item in _input.all()
]
```

## Output format rules

- Always return a **list** of `{"json": {...}}` dicts.
- Never return `None` or a plain dict — n8n will error.
- If there's nothing to output (e.g., all filtered out), return `[]`.
- Use `.get()` with defaults instead of direct key access to avoid KeyError.

## When to use JavaScript instead

Prefer the JavaScript Code node when:
- You need async/await
- Performance matters for large item counts

Use Python when:
- The team is more comfortable with Python
- The logic is naturally expressed with list comprehensions or `re`/`datetime` stdlib
- There is no async requirement
