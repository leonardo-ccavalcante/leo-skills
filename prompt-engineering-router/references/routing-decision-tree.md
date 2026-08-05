# Routing decision tree — stage × signal

This is the full decision tree the router uses. Read top-to-bottom. Stop at the first row that matches.

## Level 1 — Stage of work

Ask: *What level is the user operating at?*

| Stage | What it sounds like | Skill universe to consider |
|---|---|---|
| Single prompt | "Help me write a prompt that…", "Is this prompt good?" | foundations, role-and-context, output-control, task-patterns |
| Multi-prompt system | "I have a pipeline that…", "After step 1, I want…", "Run this over N inputs" | orchestration + above |
| Reasoning-heavy task | "Multi-step", "complex reasoning", "model rushes" | reasoning + above |
| Production / scale | "We're shipping…", "1000 inputs/day", "needs to be reliable" | reliability, security + above |

A query can fit two stages (e.g., production + reasoning). Take the union of skill universes; Step 2 narrows further.

## Level 2 — Dominant signal type

Within the stage's skill universe, the signal determines which specific skill leads.

### Signal A — Named keyword

Direct mapping (run keyword → skill):

| Keyword (and common variants) | Primary skill |
|---|---|
| chain-of-thought, CoT, "let's think step by step" | reasoning |
| self-consistency, majority vote, sampling | reasoning |
| tree-of-thoughts, ToT, branching reasoning | reasoning |
| ReAct, agent loop, reason+act | reasoning |
| generated knowledge | reasoning |
| task decomposition, plan-then-solve | reasoning (technique) OR orchestration (chain) — see disambiguation |
| zero-shot, no examples | foundations |
| few-shot, n-shot, demonstrations, examples | foundations |
| ambiguity, clarity, prompt structure | foundations |
| instruction engineering, instruction tuning (the prompt sense) | foundations |
| persona, role, "act as", "you are a…" | role-and-context |
| system message, system prompt (the message itself, not protecting it) | role-and-context |
| multilingual, code-switch, translate context | role-and-context |
| prompt chain, sequence, multi-prompt, pipeline | orchestration |
| Jinja, template, variables, parameterize | orchestration |
| map-reduce, fan-out | orchestration |
| JSON, schema, structured output, YAML, XML output | output-control |
| function calling, tool calling (as output shape) | output-control |
| length cap, word limit, brevity | output-control |
| negative prompt, "avoid", "don't include" | output-control |
| constrained generation, grammar, guided | output-control |
| refusal, "say no when…" | output-control (+security if for safety) |
| evaluate, eval, golden set, A/B test prompt | reliability |
| hallucination, fabrication, factuality | reliability |
| grounding, RAG, citation | reliability |
| bias, fairness, calibration | reliability |
| prompt optimization (auto) | reliability (APE belongs there as a tool) |
| prompt injection, prompt leak, jailbreak, DAN, Waluigi | security |
| indirect injection (via retrieved content) | security |
| red team, adversarial test (defensive) | security |
| ethical AI, safe prompt, refuse harmful | security |
| classify, categorize, label | task-patterns (classification) |
| extract, pull out, structured extraction | task-patterns (extraction) |
| summarize, TL;DR, condense | task-patterns (summarization) |
| Q&A, question answering, answer from docs | task-patterns (QA) |
| code generation, generate code, write code | task-patterns (code) |
| creative writing, story, poem, copy | task-patterns (creative) |
| image prompt, DALL-E, Stable Diffusion, Midjourney | task-patterns (image gen) |

### Signal B — Failure mode

When the user describes what's wrong, not what they want.

| Failure pattern | First-stop skill | Why |
|---|---|---|
| "Confidently wrong final answer" on multi-step | reasoning | Symptom of missing CoT |
| "Confidently wrong factual claim" | reliability | Symptom of hallucination |
| "Random behavior across runs" | reliability | Self-consistency or temperature issue |
| "Output format drifts" | output-control | Format-instruction failure |
| "Model adds 'Sure! Here's…' preamble" | output-control | Common preamble-suppression need |
| "Model breaks character" | role-and-context | Persona insufficient |
| "Model leaks system prompt" | security | Prompt-leak attack |
| "User input changes behavior unexpectedly" | security | Prompt injection |
| "Long input → garbage output" | foundations OR orchestration | Length issue or needs split |
| "Worked on test data, fails on real data" | reliability | Distribution shift / weak eval |
| "Too slow / too expensive" | orchestration | Reduce calls or model size |
| "Model says I don't know too much / not enough" | reliability | Calibration / refusal tuning |

### Signal C — Goal / context

When neither a keyword nor a failure is named.

| Goal phrasing | First-stop skill |
|---|---|
| "Help me prompt" (no further detail) | foundations |
| "Make this more accurate" | reliability (define accurate first) |
| "Make this faster" | orchestration (fewer/smaller calls) |
| "Make this safer" | security |
| "Make this an expert" | role-and-context |
| "Build a [classifier/summarizer/etc.]" | task-patterns |
| "Productionize" | reliability + security |
| "Test my prompt" | reliability |

## Level 3 — Combo check

After Step 2 picks a primary, scan for combo signals:

- Production keywords ("ship", "production", "1000/day", "users") → add reliability + security.
- Task-family + scale → add orchestration (map-reduce).
- Task-family + accuracy concerns → add reliability.
- Reasoning + format ("step by step AND JSON output") → add output-control.
- Persona + refusal/scope → add output-control (sentinel/refusal patterns).
- Multilingual + adversarial → add security.

If a combo applies, the primary skill is the *entry point* but the user should know which secondary to consult next.

## Disambiguation table

Borderline cases that recur:

**Task decomposition: reasoning or orchestration?**
- *Within one prompt* (the model decomposes and answers) → reasoning.
- *Across multiple prompts* (each subtask gets its own call) → orchestration.

**System message: role-and-context or security?**
- *Designing the system message persona* → role-and-context.
- *Protecting the system message from extraction* → security.

**JSON output: output-control or orchestration?**
- *Want one prompt to return JSON* → output-control.
- *Want typed boundary between chained prompts* → orchestration (with reference to output-control).

**Few-shot: foundations or task-patterns?**
- *Asking how few-shot works in general* → foundations.
- *Asking for few-shot examples for a specific domain* → task-patterns (domain pattern) but the example design rules live in foundations.

**Self-consistency: reasoning or reliability?**
- *Technique mechanics* → reasoning.
- *Reliability across many runs* → reliability (which references reasoning for the technique).

**Hallucination: reliability or task-patterns?**
- *General hallucination mitigation* → reliability.
- *Hallucination in a specific task (e.g., summarization)* → task-patterns first (for the recipe), then reliability for the grounding strategy.

## Terminating cases (no router needed)

These queries are unambiguous; route directly without invoking this skill:

- "How do I write a CoT prompt?" → `prompt-reasoning`.
- "How do I extract JSON?" → `prompt-output-control`.
- "How do I prevent jailbreaks?" → `prompt-security`.
- "How do I evaluate a prompt?" → `prompt-reliability`.
- "How do I build a classifier?" → `prompt-task-patterns`.

If the user already named the technique/concept/task, trust the keyword and ship.
