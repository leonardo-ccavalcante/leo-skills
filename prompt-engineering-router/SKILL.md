---
name: prompt-engineering-router
description: Meta-router that picks the right skill(s) from the 8-skill Prompt Engineering Toolkit (prompt-foundations, prompt-reasoning, prompt-role-and-context, prompt-orchestration, prompt-output-control, prompt-reliability, prompt-security, prompt-task-patterns) for the user's actual need. Use this skill whenever the user has a prompt-engineering question that is broad ("how should I prompt for X", "what's the best approach", "help me with this prompt"), spans multiple sub-skills, or doesn't obviously map to one of the eight; whenever the user asks "which prompt skill should I use" or asks for an overview of available techniques; and whenever a query mixes keywords across domains (e.g., "structured JSON output from a chained pipeline" — output-control + orchestration). Trigger on phrases like "which technique", "what's the right approach", "help me prompt", "I'm not sure how to", "my prompt isn't working" (failure mode without obvious cause), or any prompt-engineering question that doesn't clearly belong to one of the eight specialized skills. Do NOT trigger when the user's query already maps unambiguously to a single skill — in that case let that skill fire directly.
---

# Prompt Engineering Router

This is a **meta-router** for the 8-skill Prompt Engineering Toolkit. Its job: given a user query, pick the right specialized skill (or combination) and hand off cleanly. The router itself does not solve the prompt-engineering problem — the downstream skill does.

The router exists because the 8 skills are MECE *by primary topic*, but real user queries cross boundaries:
- "I want JSON output from my reasoning chain" → output-control + orchestration + maybe reasoning.
- "My summarization prompt hallucinates" → task-patterns + reliability.
- "How do I get the model to act like a tutor but refuse out-of-scope questions?" → role-and-context + output-control.

A single-skill view is incomplete for those cases. The router resolves the ambiguity.

## The 8 skills at a glance

| # | Skill | Owns |
|---|---|---|
| 1 | `prompt-foundations` | Single-prompt anatomy, structure, clarity, zero/few-shot, formatting |
| 2 | `prompt-reasoning` | CoT, ToT, ReAct, self-consistency, generated knowledge, APE, decomposition |
| 3 | `prompt-role-and-context` | Personas, system messages, multilingual prompting |
| 4 | `prompt-orchestration` | Chaining, sequencing, Jinja2 templates, multi-prompt pipelines |
| 5 | `prompt-output-control` | JSON/schema, length, negative prompting, constrained generation |
| 6 | `prompt-reliability` | Evaluation, optimization, hallucination, bias, grounding |
| 7 | `prompt-security` | Injection, leaking, jailbreaks, defenses, ethics |
| 8 | `prompt-task-patterns` | Application recipes: classification, summarization, extraction, QA, code gen, image gen |

## When this skill is the right call

The router is invoked when **any** of these is true:

- The query is broad ("how should I prompt for X", "best approach for Y").
- The query spans 2+ skills (mixed keywords from different domains).
- The user describes a failure mode without naming a cause ("the model keeps doing X").
- The user asks "which technique" or wants an overview.
- The query has a stated keyword but the underlying need points elsewhere (see *Common misroutes* below).

Do **not** invoke the router when the query unambiguously points to one skill:
- "Help me write a CoT prompt" → `prompt-reasoning` directly.
- "How do I defend against prompt injection?" → `prompt-security` directly.
- "Build me a classifier for support tickets" → `prompt-task-patterns` directly.

## The routing algorithm — three steps

The algorithm is intentionally explicit, mirroring **Pyramid Principle (problem-solving)** for the answer structure and **Key Assumptions Check + ACH (SAT)** for the discrimination logic.

### Step 1 — Diagnose the stage

What level of work is the user at? This narrows the skill universe roughly in half.

| Stage signal | Likely skills |
|---|---|
| Writing or critiquing **one prompt** | foundations, output-control, role-and-context, task-patterns |
| Designing a **multi-prompt system** | orchestration (primary), reasoning, output-control (typed boundaries) |
| Hardening for **production** | reliability, security |

Surface signals: "I have a prompt that…" (one prompt) vs. "I'm building a pipeline that…" (system) vs. "We're about to ship…" (production).

### Step 2 — Identify the dominant signal

There are three signal types. Each maps to a different routing logic.

**A. Keyword signal** — user names a specific technique or concept.

```
"Chain-of-Thought", "CoT"          → prompt-reasoning
"self-consistency", "vote"         → prompt-reasoning
"ToT", "Tree of Thoughts"          → prompt-reasoning
"ReAct"                            → prompt-reasoning
"JSON", "schema", "structured"     → prompt-output-control
"few-shot", "examples"             → prompt-foundations
"zero-shot"                        → prompt-foundations
"persona", "act as", "you are a…"  → prompt-role-and-context
"system message", "system prompt"  → prompt-role-and-context
"multilingual", "translate"        → prompt-role-and-context
"chain", "pipeline", "sequence"    → prompt-orchestration
"Jinja", "template"                → prompt-orchestration
"injection", "jailbreak", "DAN"    → prompt-security
"prompt leak", "extract sys prompt"→ prompt-security
"hallucination", "grounding", "RAG"→ prompt-reliability
"eval", "golden set", "A/B"        → prompt-reliability
"classify", "categorize"           → prompt-task-patterns (classification)
"extract", "pull out fields"       → prompt-task-patterns (extraction)
"summarize", "TL;DR"               → prompt-task-patterns (summarization)
"image prompt", "DALL-E", "SD"     → prompt-task-patterns (image gen)
"code", "generate code"            → prompt-task-patterns (code gen)
"creative", "story", "poem"        → prompt-task-patterns (creative)
```

Keyword routing is cheap and usually right — but see *Common misroutes* below before committing.

**B. Failure-mode signal** — user describes what's going wrong, not what they want.

| User says | First-stop skill |
|---|---|
| "Model rushes / wrong answer / fluent but wrong" | prompt-reasoning |
| "Model invents facts / hallucinates" | prompt-reliability |
| "Output format keeps drifting / extra preamble" | prompt-output-control |
| "Model breaks character / drifts persona" | prompt-role-and-context |
| "Same prompt gives different answers" | prompt-reliability (self-consistency) |
| "Long input → degraded output" | prompt-foundations (length) or prompt-orchestration (split) |
| "Works on test, fails on real input" | prompt-reliability |
| "Users are bypassing my guardrails" | prompt-security |

Failure mode → diagnostic skill. Then the diagnostic skill points to root cause.

**C. Goal signal** — user states an outcome, not a technique.

| User wants | First-stop skill |
|---|---|
| "A better prompt for [vague task]" | prompt-foundations |
| "More accurate reasoning on math/logic" | prompt-reasoning |
| "The model to follow strict format" | prompt-output-control |
| "To measure if my prompt is good" | prompt-reliability |
| "To run this over 1000 documents" | prompt-orchestration |
| "An expert-sounding response" | prompt-role-and-context |
| "To handle [specific domain task]" | prompt-task-patterns |
| "To make this production-safe" | prompt-security + prompt-reliability |

### Step 3 — ACH check (consider 2–3 candidates, pick by disconfirmation)

Before committing, generate the top 2–3 candidate skills and ask: *what would a query that's actually about each candidate look like?* The strongest match wins.

This is borrowed from **Analysis of Competing Hypotheses**: route by which hypothesis best explains the evidence, not by which one was first to mind.

Worked example:

> User query: "I want my prompt to return JSON, but I have ten different prompts that need it. How do I keep them consistent?"

Candidate skills:
1. `prompt-output-control` — JSON output is its territory.
2. `prompt-orchestration` — "ten different prompts" sounds like a template system.
3. `prompt-reliability` — "consistent" sounds like measurement.

Disconfirmation pass:
- If it were *only* output-control, the user wouldn't have mentioned "ten different prompts". → output-control is necessary but not sufficient.
- If it were *only* orchestration, the user wouldn't have emphasized the JSON detail. → orchestration is part of it but not the headline.
- If it were *only* reliability, the user would talk about evaluation, not consistency-of-format. → reliability is not the main fit.

Verdict: primary = `prompt-orchestration` (the *system* is the headline), secondary = `prompt-output-control` (the *shape* each prompt produces). Recommend both; orchestration is the entry point.

## Common misroutes (Devil's Advocacy)

A short list of cases where the keyword and the right skill diverge. Memorize.

| Surface keyword | Naive route | But check for | Then route to |
|---|---|---|---|
| "JSON" | output-control | "across multiple prompts" | + orchestration |
| "persona" | role-and-context | "and refuse off-topic" | + output-control |
| "step by step" | reasoning | "and output JSON at the end" | + output-control |
| "summarize" | task-patterns | "without making things up" | + reliability |
| "translate" | role-and-context | "and prevent attackers" | + security |
| "extract" | task-patterns | "with high accuracy" + scale | + reliability + orchestration |
| "few-shot" | foundations | "for a multi-step pipeline" | + orchestration |
| "the model is wrong" | reasoning | depends on whether it's a math/logic vs. factual error | reasoning OR reliability |
| "constrain output" | output-control | "to prevent injection" | + security |
| "evaluate" | reliability | "during prompt drafting" | reliability + foundations |

## When 2–3 skills should be invoked together

Some patterns recur. These combos are the right call most of the time:

- **Production deployment** = `prompt-reliability` + `prompt-security` + (the relevant task skill).
- **RAG QA system** = `prompt-task-patterns` (QA section) + `prompt-reliability` (grounding, citations).
- **Multi-prompt pipeline** = `prompt-orchestration` + `prompt-output-control` (typed interfaces).
- **Reasoning + structured output** = `prompt-reasoning` + `prompt-output-control`.
- **Agent with tools** = `prompt-reasoning` (ReAct) + `prompt-security` (action gating).
- **Domain-specific classifier** = `prompt-task-patterns` + `prompt-foundations` (instruction tuning) + `prompt-reliability` (eval).

If you find yourself recommending 4+ skills, you're probably padding. Cut to the 2–3 that carry the load.

## Output format — what the router produces

When the router fires, return a structured recommendation following Pyramid Principle:

```
**Governing thought** (one line): The user's need is best served by {primary skill} [+ {secondary} if combo].

**Why** (3 lines max):
- Key signal: {what in the query pointed here}
- Stage: {single-prompt / system / production}
- Why not {top runner-up}: {disconfirming evidence}

**Hand-off**:
- Start with: `{primary skill}` — focuses on {its specialty for this query}.
- {If combo:} Then layer in `{secondary skill}` for {its specialty for this query}.
- {If watch-out:} If you also see {signal X}, swap/add `{tertiary}`.
```

Keep it to ~10 lines. The user wants to be routed, not lectured.

## Worked routing examples

### Example 1 — Single keyword, clean route

> "How do I write a chain-of-thought prompt for math word problems?"

- Stage: single prompt.
- Signal: keyword (CoT, math).
- ACH: only `prompt-reasoning` survives — math word problems is its canonical use case.
- **Route**: `prompt-reasoning` (see `references/cot-recipes.md` for the template).

### Example 2 — Failure mode, two candidates

> "My summarizer keeps inventing dates that aren't in the source document."

- Stage: single prompt.
- Signal: failure mode (hallucination) + task family (summarization).
- ACH:
  - `prompt-task-patterns` — summarization is its territory, but the prompt template alone won't fix hallucination.
  - `prompt-reliability` — grounding and "I don't know" licensing is the headline.
- **Route**: primary = `prompt-reliability` (factuality is the root cause); secondary = `prompt-task-patterns` (summarization-specific patterns).

### Example 3 — Production system, three candidates

> "We're about to ship an email-drafting assistant for customer support. What should I think about?"

- Stage: production system.
- Signal: goal (ship safely), domain (customer support).
- ACH:
  - `prompt-task-patterns` — customer support is a task family.
  - `prompt-security` — production email assistant has injection surface.
  - `prompt-reliability` — production = evaluation needed.
  - `prompt-role-and-context` — assistant persona matters.
- **Route**: lead with `prompt-security` and `prompt-reliability` (production safety is the framing). Layer `prompt-task-patterns` for the support-specific patterns and `prompt-role-and-context` for the persona work.

### Example 4 — User asks for overview

> "Can you walk me through how to prompt for a complex task?"

- Stage: ambiguous.
- Signal: broad goal.
- This is a router-stays-in-charge moment. Don't pick one downstream skill — present the 8-skill map and ask one clarifying question to narrow (single prompt or multi-step? expected output format? do you have a real task in mind?). Once they answer, route as above.

## Honest limits of routing

Borrowed from the SAT critique: routing is not a substitute for the user's judgment. Three caveats:

1. **Keyword ≠ intent.** Users say "JSON" when they mean "structured" — sometimes the right skill is orchestration (typed boundary), not output-control. Always check the stage.
2. **Failure modes often have multiple causes.** "Model gives wrong answers" can be reasoning, reliability, or output-format drift. When ambiguous, route to *both* candidate skills with a note that the user should pick whichever maps better to their case.
3. **The router can be wrong.** If the downstream skill doesn't fit, say so explicitly — don't double down. Reroute.

## Reference material

- `references/routing-decision-tree.md` — full decision tree with stage × signal cells.
- `references/ach-routing-matrix.md` — Key Assumptions Check + ACH worked through each of the 8 skills, with disconfirming evidence patterns.
- `references/combo-patterns.md` — catalog of 2–3 skill combos for recurring real-world setups.
- `references/clarifying-questions.md` — when the query is too vague, the right one-question follow-ups (mapped to which routing dimension they clarify).

## Sources distilled

This skill combines:
- **Skill-creator structure** — progressive disclosure with reference files, lean SKILL.md, MECE design.
- **Problem-solving (McKinsey) — issue tree, Pyramid Principle output, distinction between summary (listing skills) and synthesis (recommending one and why).
- **SAT (CIA Tradecraft Primer)** — Key Assumptions Check (what we assume about the user), ACH (compare candidates by disconfirmation), Devil's Advocacy (the "common misroutes" table).

The 8 downstream skills it routes to live in their own SKILL.md files alongside this router.
