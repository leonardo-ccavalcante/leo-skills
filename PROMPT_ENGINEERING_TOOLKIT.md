# Prompt Engineering Toolkit — MECE Skill Set

Eight specialized skills + 1 meta-router, mutually exclusive and collectively exhaustive, covering the union of:

- [DAIR.AI Prompt Engineering Guide — `guides/`](https://github.com/dair-ai/Prompt-Engineering-Guide/tree/main/guides)
- [DAIR.AI Prompt Engineering Guide — `pages/prompts/`](https://github.com/dair-ai/Prompt-Engineering-Guide/tree/main/pages/prompts)
- [NirDiamant's `Prompt_Engineering/all_prompt_engineering_techniques`](https://github.com/NirDiamant/Prompt_Engineering/tree/main/all_prompt_engineering_techniques)

## The meta-router

[`prompt-engineering-router`](prompt-engineering-router/SKILL.md) — picks the right specialized skill(s) for a given query. Use when the question is broad, ambiguous, spans 2+ skills, or you're unsure which to invoke. Built using McKinsey **issue-tree + Pyramid Principle** and CIA SAT's **Key Assumptions Check + Analysis of Competing Hypotheses**.

## The eight specialized skills

| # | Skill | One-line | When it triggers |
|---|---|---|---|
| 1 | [`prompt-foundations`](prompt-foundations/SKILL.md) | Single-prompt anatomy, structure, clarity, formatting, zero-shot, few-shot | "How do I write a prompt for X?", "Is this prompt good?" |
| 2 | [`prompt-reasoning`](prompt-reasoning/SKILL.md) | CoT, zero-shot CoT, self-consistency, ToT, ReAct, Generated Knowledge, APE, task decomposition | "Think step by step", reasoning, math, planning |
| 3 | [`prompt-role-and-context`](prompt-role-and-context/SKILL.md) | Personas, role prompting, system messages, multilingual | "Act as", persona, system prompt, "respond in language X" |
| 4 | [`prompt-orchestration`](prompt-orchestration/SKILL.md) | Prompt chaining, sequencing, parameterized templates, Jinja2 | "Pipeline", "chain", "template", running prompt over a dataset |
| 5 | [`prompt-output-control`](prompt-output-control/SKILL.md) | Structured output, schema enforcement, length, negative prompting, refusal, constrained generation | "JSON output", "force schema", "the model adds preamble" |
| 6 | [`prompt-reliability`](prompt-reliability/SKILL.md) | Evaluation, optimization, hallucination/factuality, bias, calibration, grounding | "Evaluate prompt", "hallucination", "test prompt", "golden set" |
| 7 | [`prompt-security`](prompt-security/SKILL.md) | Injection, leaking, jailbreaks, indirect injection, defenses, ethics | "Prompt injection", "jailbreak", "harden", "red team" |
| 8 | [`prompt-task-patterns`](prompt-task-patterns/SKILL.md) | Application recipes: classification, extraction, summarization, QA, code gen, creative writing, image gen | "Classify", "extract", "summarize", "image prompt", domain-specific tasks |

## How the cuts work

The set divides along **what the user wants to accomplish**:

1. *Write or improve a single prompt* → `prompt-foundations`.
2. *Make the model reason better within a single prompt* → `prompt-reasoning`.
3. *Anchor the model's identity or language* → `prompt-role-and-context`.
4. *Build a multi-prompt system* → `prompt-orchestration`.
5. *Constrain or shape what comes out* → `prompt-output-control`.
6. *Test, measure, and improve trustworthiness across many runs* → `prompt-reliability`.
7. *Defend against adversarial inputs or guard ethics* → `prompt-security`.
8. *Apply a known recipe for a specific task family* → `prompt-task-patterns`.

These cuts are mutually exclusive: a user query has exactly one most-natural home. Collective exhaustion is verified against the source repositories (mapping table below).

## Source coverage (collective exhaustion check)

### DAIR.AI Prompt Engineering Guide — `guides/`

| Source file | Mapped to skill(s) |
|---|---|
| `prompts-intro.md` | `prompt-foundations` |
| `prompts-basic-usage.md` | `prompt-foundations` |
| `prompts-advanced-usage.md` | `prompt-reasoning` (CoT, ToT, ReAct, self-consistency, GKP, APE) |
| `prompts-applications.md` | `prompt-task-patterns` |
| `prompts-chatgpt.md` | `prompt-task-patterns` + `prompt-role-and-context` |
| `prompts-adversarial.md` | `prompt-security` |
| `prompts-reliability.md` | `prompt-reliability` |
| `prompts-miscellaneous.md` | `prompt-task-patterns` |

### DAIR.AI prompts catalog — `pages/prompts/`

| Subdirectory | Mapped to |
|---|---|
| `adversarial-prompting` | `prompt-security` |
| `classification` | `prompt-task-patterns` |
| `coding` | `prompt-task-patterns` |
| `creativity` | `prompt-task-patterns` |
| `evaluation` | `prompt-reliability` |
| `image-generation` | `prompt-task-patterns` |
| `information-extraction` | `prompt-task-patterns` |
| `mathematics` | `prompt-task-patterns` + `prompt-reasoning` |
| `question-answering` | `prompt-task-patterns` |
| `reasoning` | `prompt-reasoning` |
| `text-summarization` | `prompt-task-patterns` |
| `truthfulness` | `prompt-reliability` |

### NirDiamant techniques (22)

| Technique | Mapped to |
|---|---|
| `intro-prompt-engineering-lesson` | `prompt-foundations` |
| `basic-prompt-structures` | `prompt-foundations` |
| `prompt-formatting-structure` | `prompt-foundations` |
| `prompt-length-complexity-management` | `prompt-foundations` |
| `ambiguity-clarity` | `prompt-foundations` |
| `instruction-engineering-notebook` | `prompt-foundations` |
| `zero-shot-prompting` | `prompt-foundations` |
| `few-shot-learning` | `prompt-foundations` |
| `cot-prompting` | `prompt-reasoning` |
| `self-consistency` | `prompt-reasoning` |
| `task-decomposition-prompts` | `prompt-reasoning` |
| `role-prompting` | `prompt-role-and-context` |
| `multilingual-prompting` | `prompt-role-and-context` |
| `prompt-chaining-sequencing` | `prompt-orchestration` |
| `prompt-templates-variables-jinja2` | `prompt-orchestration` |
| `constrained-guided-generation` | `prompt-output-control` |
| `negative-prompting` | `prompt-output-control` |
| `evaluating-prompt-effectiveness` | `prompt-reliability` |
| `prompt-optimization-techniques` | `prompt-reliability` |
| `prompt-security-and-safety` | `prompt-security` |
| `ethical-prompt-engineering` | `prompt-security` |
| `specific-task-prompts` | `prompt-task-patterns` |

Every source file or technique appears in at least one skill; no two skills claim the same primary topic.

## Disambiguation — where overlaps could occur

A few topics legitimately touch multiple skills. Each skill cross-references the others so the user is routed correctly:

- **Few-shot prompting** — home: `prompt-foundations`. Cross-referenced in `prompt-reasoning` (for few-shot CoT) and `prompt-task-patterns` (for task-specific examples).
- **Self-consistency** — home: `prompt-reasoning` (technique). Cross-referenced in `prompt-reliability` (use for trustworthy outputs).
- **System messages / system prompts** — home: `prompt-role-and-context` (framing). Cross-referenced in `prompt-security` (injection-resistant placement).
- **Negative prompting** — home: `prompt-output-control` (shaping output). Cross-referenced in `prompt-foundations` (positive vs. negative phrasings).
- **Output schemas / JSON** — home: `prompt-output-control`. Cross-referenced in `prompt-orchestration` (typed interfaces between chained steps).
- **Hallucination** — home: `prompt-reliability`. Cross-referenced in `prompt-task-patterns` (grounding for QA, summarization).
- **Math problems** — home: `prompt-reasoning` for techniques, `prompt-task-patterns` for application-specific recipes.

## Each skill's anatomy

Every skill follows the same structure:

```
prompt-<skill>/
├── SKILL.md              ← main file with frontmatter (name, description) + body
└── references/           ← deeper material loaded on demand
    └── *.md
```

The `SKILL.md` files are intentionally tight (each ≤ ~350 lines) and pointer-style — they direct to references for depth. References include: drop-in recipes, decision trees, checklists, design patterns, and failure-mode catalogs.

## Sources

- DAIR.AI Prompt Engineering Guide — https://github.com/dair-ai/Prompt-Engineering-Guide
- NirDiamant Prompt Engineering techniques — https://github.com/NirDiamant/Prompt_Engineering

Generated 2026-05-15 using the `skill-creator` skill.
