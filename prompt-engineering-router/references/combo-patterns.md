# Multi-skill combo patterns

Some setups recur. These are the most common 2–3 skill combinations and the order in which to apply them.

The rule of thumb: **start with the skill that frames the system; layer in the others as they become relevant.** Don't dump all four skills on the user at once — that's not routing, that's noise.

## Combo 1 — Production deployment

**Setup**: User is shipping an LLM feature to real users.

**Skills, in order**:
1. The task-specific skill (whichever task family applies — e.g., `prompt-task-patterns` for classification/extraction; `prompt-reasoning` for an agent; etc.).
2. `prompt-reliability` — to set up evals, golden sets, hallucination guards before launch.
3. `prompt-security` — to red-team against injection and harden the prompt.

**Why this order**: get the core right, then test it, then defend it. Reversing the order tends to produce over-engineered safety-without-quality systems.

**Watch-out**: if the feature involves user-supplied content (emails, documents, web pages), promote `prompt-security` from step 3 to step 2 — indirect injection is a foundational concern.

## Combo 2 — RAG / grounded QA

**Setup**: User wants the model to answer questions over a corpus of documents.

**Skills, in order**:
1. `prompt-task-patterns` — for the QA-prompt recipe (closed-vs-open-book, citation pattern).
2. `prompt-reliability` — for grounding strategies, "I don't know" licensing, and faithfulness evaluation.
3. `prompt-output-control` — if the answer needs to come back in a structured shape with citations as fields.

**Why this order**: the prompt pattern shapes the system; reliability ensures it's grounded; output-control formalizes the citation/answer format.

**Watch-out**: retrieval quality dominates prompt quality for RAG. If the user is debugging "wrong answers", first check retrieval (out of scope for these skills) before tweaking the prompt.

## Combo 3 — Multi-prompt pipeline

**Setup**: User has a workflow where one LLM call's output feeds another.

**Skills, in order**:
1. `prompt-orchestration` — for the pipeline shape (linear, branching, map-reduce).
2. `prompt-output-control` — for the typed interface between steps (structured boundaries make chaining tractable).
3. The per-step skills as each step demands (foundations for the first prompt, reasoning if a step needs CoT, etc.).

**Why this order**: design the wiring before designing each station.

**Watch-out**: if 50% of the steps could be plain code, push for that. Chains with too many LLM calls multiply cost and failure modes.

## Combo 4 — Reasoning agent with tools

**Setup**: User is building an agent that uses tools (search, calculator, APIs) to answer complex queries.

**Skills, in order**:
1. `prompt-reasoning` — for the ReAct loop design.
2. `prompt-security` — for action gating, indirect injection from tool outputs, and approval flows for high-impact tools.
3. `prompt-reliability` — for monitoring trajectory quality, self-consistency over runs.

**Why this order**: build the loop; defend the loop; measure the loop.

**Watch-out**: don't let injection vectors live anywhere — tool outputs are untrusted input too.

## Combo 5 — Reasoning + structured output

**Setup**: User wants both step-by-step reasoning *and* a structured final answer (e.g., "show your work, then return JSON").

**Skills, in order**:
1. `prompt-reasoning` — for the reasoning pattern (CoT, self-consistency).
2. `prompt-output-control` — for the JSON/schema at the tail end.

**The trick**: ask for the reasoning trace first, then a marker like `Final answer:` followed by the JSON. Models reliably follow this two-zone pattern. Extracting JSON from the tail is easier than from a mixed-format blob.

## Combo 6 — Persona-driven assistant with refusals

**Setup**: User is building a tutor / coach / specialist assistant that should refuse off-topic queries.

**Skills, in order**:
1. `prompt-role-and-context` — for the persona design.
2. `prompt-output-control` — for the refusal pattern (sentinel token, refusal template).
3. `prompt-security` — if attackers might try to break the persona (e.g., "ignore your tutor role, now act as…").

**Watch-out**: thin personas don't hold up to either persistent user requests or adversarial probes. Make the persona behavioral, not titular.

## Combo 7 — Domain classifier at scale

**Setup**: User wants to classify a large dataset (e.g., 100k support tickets).

**Skills, in order**:
1. `prompt-task-patterns` — for the classification recipe.
2. `prompt-foundations` — for the few-shot example design (label balance, edge cases).
3. `prompt-orchestration` — for the map-reduce over the dataset.
4. `prompt-reliability` — for golden-set eval before running the full batch.

**Watch-out**: at scale, cheap-first matters. Try a small/fast model with zero-shot before reaching for few-shot + bigger model. Measure both.

## Combo 8 — Hardening a single prompt

**Setup**: A working prompt needs to go from prototype to production-ready.

**Skills, in order**:
1. `prompt-foundations` — first audit: is the instruction clear, are examples balanced, is format pinned?
2. `prompt-output-control` — second audit: does the output shape hold?
3. `prompt-reliability` — third audit: build a golden set; measure pass rate; identify regressions.
4. `prompt-security` — fourth audit: red-team for injection if input is user-controlled.

This is a "hardening pass" pattern — different from production deployment in that it focuses on one prompt, not a whole system.

## Combo 9 — Multilingual user-facing assistant

**Setup**: A consumer assistant that must work across languages.

**Skills, in order**:
1. `prompt-role-and-context` — multilingual prompting design.
2. `prompt-output-control` — language-pinning at the output, especially for cross-lingual tasks.
3. `prompt-reliability` — evaluating per-language quality (golden sets in each language).
4. `prompt-security` — defense against injection in languages your filters don't cover.

**Watch-out**: model performance varies a lot by language. Don't assume a prompt that works in English works in low-resource languages without testing.

## Combo 10 — Open-ended creative product

**Setup**: User is building a writing-assistant feature (story generation, marketing copy, etc.).

**Skills, in order**:
1. `prompt-task-patterns` (creative section) — for the prompt structure (constraints, persona, format).
2. `prompt-role-and-context` — to deepen the persona / voice.
3. `prompt-reliability` — for human-eval since creative outputs don't auto-grade.
4. `prompt-orchestration` — if you're chaining draft → critique → revise.

**Watch-out**: creative outputs benefit most from iterative loops (combo 4 of orchestration: critique loop). One-shot creative prompts plateau fast.

---

## When NOT to use combos

If the user's query is small ("how do I structure a few-shot prompt"), don't dump three skills on them — that's overhead. The router's job is to be **minimally sufficient**, not exhaustive. Pick the smallest combo that covers the question, and note the others as "you might also want to look at X later" if relevant.
