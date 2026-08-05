---
name: prompt-orchestration
description: Design multi-prompt pipelines — prompt chaining, sequencing, parameterized templates, and variable substitution with Jinja2 or similar. Use whenever the user's task can't or shouldn't fit in a single prompt: a draft-then-critique loop, an analyze-then-decompose-then-summarize pipeline, a parameterized prompt that runs over many inputs, a workflow where one model's output feeds another's input, or a templated system where prompts are built from variables. Trigger on phrases like "prompt chain", "pipeline", "multi-step prompt", "feed output into next prompt", "parameterize my prompt", "template", "Jinja2", "render prompt", "run this over a dataset", "first do X, then do Y". Do not trigger for in-prompt reasoning (use prompt-reasoning) or for single-prompt drafting (use prompt-foundations).
---

# Prompt Orchestration

When the work is bigger than a single prompt — multi-stage workflows, parameterized prompts running over batches, recursive critique loops — you need orchestration. Two related concerns live here:

1. **Prompt chaining**: many prompts, output of one feeding the next.
2. **Templating**: turning a prompt into a function over variables.

They compose: most real systems are templated prompts in a chain.

## When this skill is the right call

- The user wants to split a task across multiple LLM calls.
- The user is building a workflow where one prompt's output is another's input.
- The user is parameterizing a prompt to run over many inputs.
- The user mentions chaining, sequencing, templates, Jinja2, prompt pipelines.
- A single prompt is doing too much and getting noticeably worse for it.

Not the right call if:
- The task fits in one prompt with a CoT trace → `prompt-reasoning`.
- The user wants structured output from a single call → `prompt-output-control`.
- The user is choosing between agentic tool-use and chaining → ReAct lives in `prompt-reasoning`; chaining is fixed, not adaptive.

## When to chain vs. keep one prompt

Chain when:
- Sub-steps need different system prompts, personas, or models.
- Sub-step outputs are reused (drafted once, critiqued twice, edited once).
- Sub-steps need different temperatures (low for extraction, higher for generation).
- One step's failure should short-circuit downstream steps (cheap detection + expensive processing).
- You want to inspect or branch on intermediate results.

Don't chain when:
- The steps share heavy context that gets duplicated across calls (token waste).
- The model would benefit from seeing all sub-steps jointly (interdependent reasoning).
- Latency is critical and chained calls serialize.

Rule of thumb: if you can write the sub-steps with crisp boundaries and a typed interface between them, chain. If the boundary is fuzzy, keep them in one prompt with CoT.

## Common chain shapes

```
Linear:           A → B → C
Branching:        A → {B, C} → D       (B and C run in parallel; D merges)
Loop:             A → B → check → maybe loop B
Map:              run B over many items from A
Reduce / merge:   many B outputs → single C
Map-reduce:       A → map(B) → reduce(C)
Critique loop:    draft → critique → revise → critique → revise
```

Each shape has a stable name; using them makes design conversations cleaner.

## Designing a chain — five questions

1. **Inputs of each step**: what variables go in?
2. **Outputs of each step**: what shape comes out? (this is where `prompt-output-control` matters — structured outputs make chaining tractable)
3. **Failure handling per step**: retry, skip, fall back, fail loud?
4. **Token budgeting**: which steps carry the most context, and can context be summarized between steps?
5. **What's the cheapest version that works?** Resist the urge to add a step "for safety" — added steps multiply failure modes and cost.

## A worked example — draft / critique / revise

Goal: produce a polished customer-support reply.

**Single-prompt approach** (often good enough):

```
Draft a customer-support reply to the email below. Self-critique it before finalizing. If you find issues, revise and return only the revised version.
```

**Two-prompt chain** when the single prompt isn't critiquing rigorously:

```
Prompt A (draft):
You are a customer-support agent. Reply to the email below in 3 sentences. <email>{email}</email>

Prompt B (critique + revise):
You are a senior support lead. Below is a draft reply to a customer email. Critique it for: tone (warm, not effusive), completeness (acknowledges issue, names next step), and policy compliance (no specific timelines unless email mentions one). Then return the revised reply only.
<email>{email}</email>
<draft>{draft}</draft>
```

The chain works because Prompt B has a different persona and a sharper instruction than Prompt A. Two passes by the same agent is worse than two passes by differently-framed agents.

## Templating with variables

Most production prompts are templates: prompts with placeholder variables that get substituted at runtime. Python's `str.format`, f-strings, and Jinja2 are the common tools.

```python
# Plain Python
prompt = "Translate from {src_lang} to {tgt_lang}: {text}".format(
    src_lang="English", tgt_lang="French", text=user_input
)
```

```python
# Jinja2 — for conditionals, loops, and partials
from jinja2 import Template
t = Template("""
You are a {{ persona }}.

{% if examples %}
Examples:
{% for ex in examples %}
Input: {{ ex.input }}
Output: {{ ex.output }}
{% endfor %}
{% endif %}

Now process: {{ user_input }}
""")
prompt = t.render(persona=..., examples=[...], user_input=...)
```

When to use Jinja2 over plain f-strings:
- You have conditional sections (include examples only if available).
- You have lists that vary in length (zero to N few-shot examples).
- You want partial templates (header reused across many prompts).
- Multiple prompts share structure.

When plain f-strings are enough:
- One or two variables, no conditionals.
- The prompt is fixed-shape.

## Templating pitfalls

- **User input as a variable**: when `user_input` is interpolated directly, malicious content can hijack the prompt. Always delimit with tags or quotes, and see `prompt-security` for injection defenses.
- **Variable escaping**: if user input contains the same delimiter you used (`</article>`), the template breaks. Either escape, switch delimiters, or use Jinja's auto-escaping for HTML-ish tags.
- **Whitespace drift**: Jinja's default whitespace handling can leave extra blank lines. Use `{%- ... -%}` for trim mode.
- **Variables you forgot to render**: a `{{ user_name }}` literal in your prompt is a tell that you forgot to populate it. Lint your rendered prompt before sending.

## Map-reduce over a dataset

A common pattern: run the same prompt over N inputs (map), then aggregate (reduce).

Example: extract a structured summary from each of 200 customer-support tickets, then synthesize the top 10 themes.

```
Map step (parallelizable):
  For each ticket:
    Prompt(extract_summary_template, ticket_text) → ticket_summary

Reduce step:
  Prompt(synthesize_themes_template, all_ticket_summaries) → top_themes
```

Notes:
- The map step is embarrassingly parallel — fan it out.
- The reduce step often hits context limits. Group reduces (reduce 200 → 20 → 1) help.
- For long-tail synthesis, iterative refinement (reduce N items, then merge with the running summary) sometimes outperforms one-shot reduce.

## A worked pipeline example

User has 500 unstructured meeting notes. They want a weekly digest.

```
Stage 1 (map):   For each note → extract {date, attendees, decisions, action_items}
Stage 2 (filter): Drop notes with no decisions and no action items
Stage 3 (group):  Group remaining items by week
Stage 4 (reduce): For each week → produce a 5-bullet digest
```

Notes:
- Stage 1 is structured-output territory (`prompt-output-control`).
- Stage 2 is plain code, no LLM needed.
- Stage 3 is plain code.
- Stage 4 is the only stage that benefits from a generative prompt.

Doing fewer LLM calls and more deterministic glue is almost always cheaper and more reliable than chaining everything through the model.

## Reference material

- `references/chain-design-patterns.md` — catalog of chain shapes (map, reduce, critique loop, router) with skeletons.
- `references/jinja2-prompt-template.md` — Jinja2-specific patterns and pitfalls for prompts.

## Sources distilled

This skill condenses material from NirDiamant's Prompt Engineering techniques (prompt-chaining-sequencing, prompt-templates-variables-jinja2) and design patterns from the DAIR.AI guides (advanced usage, applications). For tool-augmented adaptive flows (ReAct), see `prompt-reasoning`.
