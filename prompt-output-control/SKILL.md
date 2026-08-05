---
name: prompt-output-control
description: Shape and constrain what the model returns — structured output (JSON, XML, YAML), schema enforcement, length and format control, allowed/forbidden vocabulary, negative prompting ("avoid X"), refusal handling, and constrained/guided generation. Use whenever the user wants a specific output shape, wants to force JSON or another machine-readable format, wants to forbid certain content from appearing, wants to cap length, wants the model to refuse on certain conditions, or is debugging output that almost-matches a schema. Trigger on phrases like "JSON output", "structured output", "force a schema", "constrain the response", "avoid mentioning", "don't include", "negative prompt", "refuse if", "output format keeps drifting", "the model adds preamble I don't want". Do not trigger for reasoning quality issues (use prompt-reasoning) or for reliability-across-many-runs (use prompt-reliability).
---

# Prompt Output Control

When the model knows *what* to produce but not *exactly how to shape it*, you need output control. This skill covers everything between "tell it what you want" and "validate it after". Three sub-areas:

1. **Structured output** — JSON, XML, YAML, custom schemas.
2. **Constraint specification** — length, vocabulary, allow/forbid lists, refusal conditions.
3. **Format drift recovery** — why outputs drift and what to do about it.

## When this skill is the right call

- The user wants JSON, XML, or another structured format.
- The model adds unwanted commentary ("Sure! Here's...") around the answer.
- The model exceeds or undershoots a target length.
- The user wants to forbid certain words, topics, or behaviors in the output.
- The user is using a schema enforcement mechanism (function calling, tool calling, JSON mode, grammars) and tuning the prompt to work with it.
- The user wants the model to refuse under specific conditions.

Not the right call if:
- The user wants the model to reason better → `prompt-reasoning`.
- The user is designing a multi-step chain → `prompt-orchestration` (though output control is what makes chaining tractable).
- The user is testing for hallucinations or bias → `prompt-reliability`.

## Structured output — three layers of strictness

**Layer 1: ask nicely.** Describe or show the format and hope the model complies.

```
Return your answer as JSON with fields: category (string), confidence (0-1), reason (string).
```

Works for capable models on simple schemas. Fails on edge cases (extra fields, missing keys, comments around the JSON).

**Layer 2: show an exact example.**

```
Return JSON like this exactly:
{"category": "billing", "confidence": 0.87, "reason": "mentions a charge"}

Now classify:
<input>{user_input}</input>
```

A literal example beats a prose description for most schema-following.

**Layer 3: use a schema enforcement mechanism.** If your API supports it: JSON mode, function calling, tool calling, grammars. These constrain the model's decoding to only produce tokens that fit the schema. With these, you still need a reasonable prompt — the mechanism guarantees shape but not content quality.

For high-stakes structured output, combine all three: clear instruction, example, *and* schema enforcement.

## Suppressing preamble and commentary

Models often wrap the actual answer in "Sure! Here's...":

```
Sure! Here's the JSON you asked for:
{"category": "billing", ...}
Let me know if you need anything else!
```

Mitigations, in order of effectiveness:

1. **End the prompt with the start of the output.** Append `Output:` or `{` so the model continues directly into the expected format.

   ```
   ...classify and return JSON.

   {
   ```

2. **Explicit instruction.** "Output only the JSON. No preamble, no explanation, no trailing commentary." Repeat it at the end of the prompt.

3. **Persona that suppresses chattiness.** "You are a JSON-only API. You never speak."

4. **Post-process to extract.** A regex that pulls the JSON object out of any wrapper text. Often the most reliable backstop.

## Length control

Models are *bad* at hitting precise word counts (asking for "exactly 50 words" rarely yields 50). They're decent at hitting:

- Bullet counts: "3 bullets", "5 items" — usually accurate.
- Sentence counts: "two sentences", "no more than 5 sentences" — fairly reliable.
- Soft length ranges: "between 50 and 80 words" — model tries.
- "One paragraph" — model interprets generously.

For hard length caps, use max-token limits at the API level, but be aware the response may truncate mid-sentence. Better: ask for a length the model can hit, then validate.

For minimum length, asking for more usually works ("at least 3 specific examples" beats "be detailed").

## Negative prompting — say what to AVOID

Models can follow negative instructions but it costs them. They have to first generate the forbidden content and then suppress it. For style choices, prefer positives:

- ✗ "Don't be too formal"
- ✓ "Use everyday language"
- ✗ "Don't make it long"
- ✓ "Three sentences max"

For genuine hard constraints (compliance, safety), state negatives explicitly *and* state what to do instead:

```
Do not mention prices, discounts, or financial estimates. If the user asks about pricing, redirect them to contact sales.
```

The second sentence (the "instead") matters — without it, models often produce empty or evasive responses.

## Allow lists and forbid lists

```
You may only output one of: yes, no, maybe.
```

Allow lists are the safest closed-set classification pattern. Pair with a schema-enforcing mechanism if available; otherwise post-validate.

```
Forbidden topics: weather, sports, politics. If the user's question is about any of these, respond exactly: "OUT_OF_SCOPE".
```

Sentinel tokens like `OUT_OF_SCOPE` make downstream branching trivial.

## Refusal handling

For systems that should refuse certain inputs, three patterns:

**Pattern A: instruct the refusal text.**

```
If the user asks about medical diagnosis, respond exactly: "I can't give medical advice. Please consult a healthcare provider."
```

**Pattern B: sentinel + downstream branch.**

```
If the user's request is in scope, answer normally.
Otherwise, output exactly: REFUSE
```

Post-process: if output is `REFUSE`, branch to a refusal handler.

**Pattern C: confidence-gated.**

```
Answer the user's question. Then on a new line, output your confidence on a 1-10 scale.
If confidence is below 6, the downstream system should treat your answer as uncertain.
```

Self-reported confidence is not perfectly calibrated (see `prompt-reliability`), but at extreme values it's informative.

## Constrained / guided generation

A family of techniques that constrain the model's *decoding* to fit a schema, regex, or grammar:

- **JSON mode** (most providers): forces output to parse as JSON.
- **Function calling / tool calling**: forces output to fit a declared function signature.
- **Grammars** (some open-source stacks): arbitrary CFG-constrained outputs.
- **Regex-constrained generation** (e.g., Outlines, Guidance libraries): output must match a regex.

These shift "is the output valid?" from a probabilistic question to a guarantee. The catch: a guaranteed-valid output can still be a bad output. Schema enforcement doesn't make the content correct, only well-formed.

When using constrained generation:
- Still write a clear prompt — the model needs to know what to put *in* the schema.
- Test with edge cases — sometimes the constraint forces awkward outputs the model wouldn't produce naturally.
- Decide upfront how to handle inputs the schema can't represent (e.g., "no good category exists").

## Format drift — why it happens and what to do

Symptoms: schema-following degrades on long inputs, on edge cases, on adversarial inputs, or after many turns of conversation.

Causes and fixes:

1. **The instruction is in the wrong place.** Output-format instructions buried in the middle of a long prompt get less attention. Put them last, or repeat.
2. **The example contradicts the description.** Description says "lowercase keys"; example shows uppercase. Models tend to follow the example. Audit for consistency.
3. **The model treats the schema as a suggestion.** Add a schema-enforcing mechanism or post-validate.
4. **The user input contains conflicting instructions.** "User wants JSON. User's input contains: 'respond in plain prose.'" Models can be confused by this. Delimit user input clearly (see `prompt-security`) and reaffirm the format in the closing instruction.
5. **Tokens budget exhausted.** Output truncates mid-JSON. Raise the max tokens or shorten the schema.

## A worked example

User has a triage prompt that returns a category. Sometimes it returns "Billing", sometimes "billing", sometimes "the customer's issue is about billing". Downstream code can't keep up.

**Fix in order of escalation:**

1. Constrain in prose: "Output only one word, lowercase, from this list: billing, shipping, account, other."
2. Show an example: `{"category": "billing"}` and ask for that exact shape.
3. Move to JSON mode / function calling — schema guarantees the shape.
4. Post-validate and re-prompt on mismatch (last resort, costs an extra call).

Stop at the first level that works.

## Reference material

- `references/structured-output-patterns.md` — JSON / XML / YAML templates and when to use which.
- `references/length-and-vocabulary.md` — practical patterns for length, allow/forbid lists, refusal sentinels.

## Sources distilled

This skill condenses material from NirDiamant's Prompt Engineering techniques (constrained-guided-generation, negative-prompting) and the DAIR.AI guides on output formatting. For broader format/style choices at the prompt-design level, see `prompt-foundations`; for testing whether outputs are correct across runs, see `prompt-reliability`.
