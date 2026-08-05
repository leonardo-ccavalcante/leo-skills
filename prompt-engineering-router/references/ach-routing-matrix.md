# ACH routing matrix — disconfirmation check per skill

This file applies **Analysis of Competing Hypotheses (ACH)** to the routing problem. For each of the 8 skills, it lists:

- **Confirming signals**: things a user query would say if they really need this skill.
- **Disconfirming signals**: things that, if present, mean the skill is *not* the right primary pick (even if some confirming signals match).
- **Near neighbors**: which other skill could be confused with this one, and how to tell them apart.

When routing, run the candidate skill(s) against this matrix. The one with the most confirming signals *and* the fewest disconfirming signals wins. If two skills tie, the query is a combo.

---

## prompt-foundations

**Confirms**: "help me write a prompt", "is this good", "what are best practices", "few-shot", "zero-shot", "make this clearer", "instruction", explicit beginner framing, no other domain in the query.

**Disconfirms**: any mention of multi-step / chain / pipeline (→ orchestration); any mention of a named reasoning technique (→ reasoning); any mention of JSON or schema (→ output-control); any application-specific task name like "classify" or "summarize" (→ task-patterns).

**Near neighbor**: task-patterns. Foundations covers *how to write a prompt in general*; task-patterns covers *the recipe for a specific task family*. If the user names a task (classify, summarize, extract), task-patterns wins.

---

## prompt-reasoning

**Confirms**: CoT, ToT, ReAct, self-consistency, generated knowledge, APE, "step by step", math/logic problem, planning, "model rushes to wrong answer", task decomposition (within one prompt), multi-step reasoning.

**Disconfirms**: pure formatting issue (→ output-control); the "wrong answer" is factual not logical (→ reliability); the chain is across multiple LLM calls (→ orchestration); the user wants a recipe for a specific task family (→ task-patterns).

**Near neighbor**: reliability. Reasoning improves *single-pass quality* via prompting techniques; reliability tests/measures/grounds across many runs. Self-consistency lives in both: technique mechanics in reasoning, application-for-reliability framing in reliability.

---

## prompt-role-and-context

**Confirms**: "act as", "pretend to be", "you are a…", "system prompt" (designing it), "persona", "tutor", "expert mode", multilingual handling, "respond in {language}", "the model breaks character".

**Disconfirms**: the persona is incidental and the real ask is reasoning/format/etc. (→ that other skill); the user wants to *protect* the system prompt from extraction (→ security); the persona is for an application-specific task pattern (→ task-patterns, with role as a sub-element).

**Near neighbor**: prompt-foundations (where persona is one of the six anatomy parts). Role-and-context goes deeper on *when* personas help and how to design them; foundations names personas at a high level.

---

## prompt-orchestration

**Confirms**: chain, pipeline, sequence, "first do X then Y", template, Jinja2, parameterize, map-reduce, fan-out, "feed output into next prompt", running same prompt over many inputs, "ten different prompts".

**Disconfirms**: only one prompt is in scope (→ foundations or the relevant skill); the "chain" is the in-prompt reasoning chain (CoT — → reasoning); the user is asking *what shape* the boundary should take (→ output-control for the boundary, orchestration for the wiring).

**Near neighbor**: reasoning. Reasoning chains the *thinking* inside one prompt; orchestration chains the *calls* across multiple prompts. If steps are separate LLM invocations, orchestration; if all in one model output, reasoning.

---

## prompt-output-control

**Confirms**: JSON, schema, structured output, function/tool calling (as output), XML output, length cap, "exactly N words", "avoid", "don't include", "constrain", "preamble", "format keeps drifting", refusal sentinel.

**Disconfirms**: the user wants the *content* to be more accurate (→ reliability); the user wants a *better-reasoning* output (→ reasoning); the user is securing against adversarial input that affects output (→ security).

**Near neighbor**: orchestration. Output shape per-prompt = output-control; typed interface between chained prompts = orchestration (with output-control as the underlying mechanism). Both can apply.

---

## prompt-reliability

**Confirms**: evaluate, A/B test, golden set, LLM-as-judge, hallucination, factuality, "the model invents", grounding, RAG citation, bias, calibration, "consistent across runs", "test prompt", optimization (data-driven).

**Disconfirms**: the failure is structural (wrong format, broken persona) — not content-correctness (→ output-control or role); the user wants in-prompt reasoning, not eval/measurement (→ reasoning); the user is defending against attackers (→ security).

**Near neighbor**: reasoning (for self-consistency) and security (for "evaluation" of attacks). Reliability is about *trustworthy benign-input behavior*; security is about *adversarial-input behavior*.

---

## prompt-security

**Confirms**: injection, prompt leak, jailbreak, DAN, Waluigi, "ignore previous", indirect injection, red team, "protect system prompt", "user input changes behavior", ethical refusal, harmful content.

**Disconfirms**: the issue is benign-input failure (→ reliability); the user is just designing a system prompt for behavior (→ role-and-context); the user wants a refusal as part of output shape, not adversarial defense (→ output-control's refusal section).

**Near neighbor**: reliability. Both deal with "the model behaves badly". Security = adversarial cause; reliability = benign-input cause. Ask: would a friendly user accidentally trigger this? Yes → reliability. Only an attacker → security.

---

## prompt-task-patterns

**Confirms**: classify, categorize, label, extract, pull fields, summarize, TL;DR, Q&A from documents, code generation, creative writing, image-gen prompt — i.e., a named task family.

**Disconfirms**: no task family is named, just a general prompt question (→ foundations); the task is named but the user actually wants reasoning techniques (→ reasoning); the task involves an output schema and that's the headline (→ output-control as primary, task-patterns as supporting).

**Near neighbor**: foundations. Foundations is generic prompt advice; task-patterns is the recipe for specific tasks. If a task is named, task-patterns wins.

---

## Worked ACH example — three routes

> "I want to build a system that takes inbound customer emails, extracts the customer's intent and any deadline mentioned, and routes the email to the right team. It needs to handle 5000 emails/day."

Candidate scores:

| Skill | Confirming | Disconfirming | Verdict |
|---|---|---|---|
| task-patterns (extraction) | "extract intent", "deadline" | none — extraction is core | strong primary |
| orchestration | "5000 emails/day" (map), routing logic | none — pipeline structure | strong secondary |
| reliability | scale + "routes to right team" → accuracy matters | not explicitly mentioned but implied | weaker tertiary |
| output-control | structured fields (intent, deadline) | none, but subsumed under extraction recipe | implicit via task-patterns |
| security | not mentioned | "customer emails" hint at injection surface | watch-out |

Final routing:
- **Primary**: `prompt-task-patterns` (the extraction recipe).
- **Secondary**: `prompt-orchestration` (map-reduce over 5000/day).
- **Tertiary watch-outs**: `prompt-reliability` (eval and grounding) and `prompt-security` (inbound email = injection surface).

This is the kind of multi-skill answer the router exists to produce.

---

## Routing test cases (for self-check)

Run these quick. If your routing matches, the matrix is internalized; if not, re-read the section.

| Query | Expected primary | Expected combo |
|---|---|---|
| "Why does my prompt give a fluent but wrong final number?" | reasoning | reasoning + reliability (if "across runs") |
| "How do I get strict JSON?" | output-control | + reasoning if "with explanation first" |
| "User input is overriding my instructions" | security | + output-control for delimiters |
| "How do I write a few-shot example for sentiment?" | task-patterns (classification) | + foundations for example design |
| "Build a tutor persona that refuses off-topic questions" | role-and-context | + output-control for refusal |
| "My RAG QA invents citations" | reliability | + task-patterns (QA section) |
| "I have 10 prompts that should all output the same JSON shape" | orchestration | + output-control |
| "Compare two prompt versions on 100 inputs" | reliability | (singleton) |
| "Translate this to French and don't let users hijack" | role-and-context | + security |
| "The model loses its character after 5 turns" | role-and-context | + reliability (if multi-turn drift) |
