# Structured output patterns

Which format to use, and how to prompt for each.

## Format choice

| Format | When to pick |
|---|---|
| JSON | Default for machine consumption. Widely supported, easy to parse. |
| XML | When values can contain arbitrary text including JSON-breaking characters, or when nesting is heavy. Anthropic models in particular often produce clean XML. |
| YAML | Avoid for model output. Indentation-sensitive and the model often miscounts spaces. |
| Custom delimiter | Single-field outputs ("Answer: X"). Simpler than JSON. |
| TSV / CSV | When the output is rows of the same shape and you want it spreadsheet-ready. JSON arrays of objects are usually a better fit. |

## JSON output template

```
You are <persona>.

Task: <task description>.

Return your answer as a JSON object with exactly these fields:
- "category": string, one of: <closed list>
- "confidence": number between 0 and 1
- "reason": string, no more than 100 characters

Output the JSON object only. No preamble, no markdown fences, no commentary.

Input:
<input>
{user_input}
</input>
```

Common pitfalls:
- The model wraps JSON in ```json ... ``` fences. Either accept them and strip, or instruct "no markdown fences."
- The model adds a trailing comma. Validate with a tolerant parser or post-process.
- The model adds explanatory text after the JSON. The `Output the JSON only` instruction helps; a regex extractor as a backstop is more reliable.

## XML output template

```
You are <persona>.

Task: <task description>.

Return your answer in this exact format:

<response>
  <category>...</category>
  <confidence>...</confidence>
  <reason>...</reason>
</response>

Do not include any text outside the <response> tags.

Input:
<input>
{user_input}
</input>
```

Why XML can outperform JSON:
- Values can contain arbitrary characters including unescaped quotes and newlines.
- Easier to read in transcripts.
- More forgiving to parse — a small validator can extract fields by tag.

When NOT to use XML: when the downstream consumer expects JSON and you don't want to convert.

## Multi-record output

```
Return one JSON object per line (JSONL format). One line per finding.

Example output:
{"finding": "...", "severity": "high"}
{"finding": "...", "severity": "medium"}

Now process: <input>
```

JSONL is friendlier to streaming and to large outputs than a single big JSON array.

## Sentinel-token output

For lightweight branching, sentinels beat JSON:

```
If the input is in scope, output the answer.
If out of scope, output exactly: OUT_OF_SCOPE
If unsure, output exactly: NEED_MORE_INFO
```

Downstream code switches on the sentinel; no parsing needed.

## Combining with schema-enforcement mechanisms

When the API supports function/tool calling or JSON mode, you still write the prompt. The mechanism guarantees shape; the prompt guarantees content quality.

```python
# pseudo-code with a hypothetical SDK
response = client.complete(
    prompt=prompt_above,
    response_format={"type": "json_object", "schema": {...}}
)
```

Even with schema enforcement:
- Describe the fields in the prompt; the schema doesn't tell the model what to put in them.
- Test edge cases — what should the model produce if no good category exists? Decide and prompt for it ("if no category fits, set category to 'other' and explain in reason").

## When the model returns *almost*-valid output

Common drift modes:
- Trailing comma in JSON.
- Field with `None` (Python) instead of `null` (JSON).
- Numbers as strings.
- Markdown fences around the JSON.

Two layers of defense:
1. **Lenient parser**: use `json5` or a forgiving custom parser that handles common drift.
2. **Retry with feedback**: if parsing fails, send the model its own output plus the parse error, ask for the fix. Cap retries at 1–2.

Layered enforcement (prompt + parsing tolerance + retry) is more robust than any single defense.
