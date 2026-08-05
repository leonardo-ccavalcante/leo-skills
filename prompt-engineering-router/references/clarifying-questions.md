# Clarifying questions — when to ask, what to ask

Most routing decisions don't need clarification — the query has enough signal. But some don't, and the right one-question follow-up saves the user from a wrong handoff.

The principle (from problem-solving / Pyramid): **a clarifying question is justified only if the answer would change the recommendation.** If both possible answers lead to the same skill, don't ask.

## When NOT to ask

Skip clarification when:
- A single skill is the clear primary, even if details vary. Hand off and let the downstream skill ask if needed.
- The query is exploratory ("tell me about prompt engineering") — present the 8-skill map, don't interrogate.
- You can route confidently to 2 skills and ask the user to pick — same effect, less friction.

## When to ask

Ask one clarifying question when:
- The same query could plausibly route to 2+ skills, AND
- The right routing depends on a fact the user can clarify in one sentence, AND
- The skills you'd route to have meaningfully different first responses.

## Clarifying-question menu by ambiguity type

### Ambiguity A — Single prompt or system?

> "I want to extract dates and amounts from documents."

Could be: single-prompt extraction recipe (task-patterns) OR a batch pipeline over many documents (orchestration + task-patterns).

**Ask**: "Is this for a handful of documents you'll process interactively, or a batch over many — say, 100+?"

Routing by answer:
- Few → `prompt-task-patterns` (extraction).
- Many → `prompt-orchestration` + `prompt-task-patterns`.

### Ambiguity B — Reasoning quality or content correctness?

> "The model keeps getting the wrong answer."

Could be: reasoning failure (CoT can help) OR factual failure (hallucination, grounding needed).

**Ask**: "Is the answer wrong because the model's reasoning skipped a step, or because it's stating something factually incorrect that isn't in the source?"

Routing by answer:
- Reasoning skipped → `prompt-reasoning` (CoT, decomposition).
- Factually wrong → `prompt-reliability` (grounding, RAG).

### Ambiguity C — Persona design or persona protection?

> "I'm working on my system prompt."

Could be: designing it (role-and-context) OR protecting it from extraction (security).

**Ask**: "Are you focused on what the system prompt should *say* and how the model should behave, or on preventing users from extracting/overriding it?"

Routing by answer:
- Design / behavior → `prompt-role-and-context`.
- Protection → `prompt-security`.

### Ambiguity D — One prompt or template across many?

> "I want consistent JSON output."

Could be: getting one prompt to reliably output JSON (output-control) OR keeping JSON shape consistent across a template family (orchestration + output-control).

**Ask**: "Is this one prompt that should produce JSON, or many prompts that should all conform to the same shape?"

Routing by answer:
- One → `prompt-output-control`.
- Many → `prompt-orchestration` + `prompt-output-control`.

### Ambiguity E — In-prompt step-by-step or multi-call chain?

> "I want to decompose this task."

Could be: in-prompt task decomposition (reasoning) OR a chain of separate prompts (orchestration).

**Ask**: "Do you want the model to break it down in a single response, or do you want each step to be its own LLM call?"

Routing by answer:
- Single response → `prompt-reasoning` (task decomposition).
- Separate calls → `prompt-orchestration`.

### Ambiguity F — Adversarial or accidental misbehavior?

> "Users are making the model do things it shouldn't."

Could be: deliberate attacks (security) OR users tripping over poorly-defined refusal logic (output-control).

**Ask**: "Are these users intentionally trying to bypass the system, or hitting edge cases by accident?"

Routing by answer:
- Intentional → `prompt-security`.
- Accidental → `prompt-output-control` (refusal patterns) + `prompt-foundations` (clearer instructions).

### Ambiguity G — Evaluate during dev or monitor in production?

> "I want to evaluate this prompt."

Could be: build a golden set for dev iteration (reliability) OR live monitoring on real traffic (reliability — different sub-pattern).

**Ask**: "Are you trying to A/B compare two prompt versions before launch, or monitor a prompt that's already live?"

Routing: both go to `prompt-reliability` but with different framing. Mention the distinction; the downstream skill handles depth.

## Template: the clarifying question itself

When you ask, frame it as a fast disambiguation, not as an interview:

```
**Quick check before I route you:** {one specific question}.

If A → I'll hand off to `{skill A}`.
If B → I'll hand off to `{skill B}`.
```

Why this works:
- It's short (one question).
- The user sees the consequence of each answer.
- It primes them to think about routing, not solution.

## When the user resists clarification

Sometimes the user says "just give me your best guess". In that case:

- Pick the more common case (e.g., "single prompt" beats "system" when in doubt).
- Hand off with a note: "Routing to `{skill}` based on the more common case. If you're actually doing {alternative}, swap to `{other skill}`."
- Don't apologize for the uncertainty — make it transparent and move on.

## Anti-pattern: routing-by-interrogation

The router is not a chatbot. If you find yourself asking 3+ clarifying questions, you're misusing the skill. Two failure modes:

1. **Over-clarifying easy queries** — most queries have enough signal. Trust the keyword/failure-mode signal and route.
2. **Stacking questions** — never ask a second clarifier in the same turn. One question, one routing decision, hand off.
