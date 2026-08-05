---
name: prompt-task-patterns
description: Application-specific prompt recipes for common task families — text classification, information extraction, summarization, question answering, code generation, mathematical reasoning, creative writing, image-generation prompts, and ChatGPT/Claude-specific application patterns. Use whenever the user has a concrete domain task — "build a classifier", "extract dates and amounts from receipts", "summarize this article", "answer questions from this document", "generate code from a spec", "write a poem", "prompt an image model" — and needs the prompt pattern that's known to work for that family. Trigger on phrases like "classify", "categorize", "extract", "pull out", "summarize", "TL;DR", "answer questions from", "Q&A", "RAG", "generate code", "write code", "image prompt", "Stable Diffusion", "DALL-E", "creative writing", "poem", "story". Do not trigger for generic single-prompt advice (use prompt-foundations) or for reasoning techniques (use prompt-reasoning).
---

# Prompt Task Patterns

When the user has a specific task — classify, summarize, extract, write code, generate an image — the question is rarely "what is prompt engineering" but "what's the known-good pattern for *this* task". This skill is a catalog of those patterns.

Each pattern below names the task family, the prompt skeleton, and the most common pitfalls. For depth on any given task family, see the matching reference file.

## When this skill is the right call

The user has a concrete application in mind and wants to know how to prompt for it. They've crossed the "how do I prompt at all" stage (`prompt-foundations`) and need a recipe tuned to a known task family.

Not the right call if:
- The user is asking general prompting basics → `prompt-foundations`.
- The user wants reasoning techniques regardless of task → `prompt-reasoning`.
- The user has a multi-step pipeline → `prompt-orchestration`.
- The user wants structured/JSON output → `prompt-output-control`.

## The task families covered

```
Task patterns
├── Classification         — assign labels from a closed set
├── Information extraction — pull structured fields from unstructured text
├── Summarization          — condense long text faithfully
├── Question answering     — answer Qs over a corpus / context
├── Code generation        — write or modify code
├── Math / reasoning tasks — see prompt-reasoning; covered here only as application
├── Creative writing       — open-ended generation (stories, copy, etc.)
└── Image-gen prompting    — text → image (Stable Diffusion / DALL-E / etc.)
```

Each gets a short pattern below. Reference files have depth and worked examples.

## Classification

```
You are a classifier for {domain}.

Classify the text below into one of: {label_1}, {label_2}, ..., {label_N}.

Definitions:
- {label_1}: ...
- {label_2}: ...

If none fits, output: other.

Output only the label, lowercase, no explanation.

<text>{input}</text>
```

Pitfalls:
- Class imbalance in few-shot examples biases predictions.
- Definitions matter more than people expect — vague definitions cause drift.
- For low-confidence cases, add a sentinel ("uncertain") rather than forcing a guess.

See `references/classification.md`.

## Information extraction

```
Extract the following fields from the text below. Output JSON.

Fields:
- date: the date mentioned, in ISO 8601 format. Null if not mentioned.
- amount: the dollar amount, as a number. Null if not mentioned.
- party: the counterparty name. Null if not mentioned.

If a field is not present, return null — do not guess.

<text>{input}</text>
```

Pitfalls:
- Models hallucinate plausible-sounding values for missing fields. Explicit "return null if not present" is essential.
- Date and number formats drift. Specify ISO 8601 dates, decimal-point numbers, etc.
- For high-stakes extraction, pair with a validator that checks each field's format.

See `references/extraction.md`.

## Summarization

```
Summarize the text below in {N} {bullets|sentences} for {audience}.

Constraints:
- Stay grounded in the source. Do not add information.
- Preserve {specific aspects, e.g., named entities, numbers, dates}.
- {Tone constraints}

<text>{input}</text>
```

Pitfalls:
- Hallucinated facts in summaries — see grounding strategies in `prompt-reliability`.
- "Make it shorter" tends to drop concrete details first. Specify what *not* to drop.
- Long inputs may need map-reduce summarization — see `prompt-orchestration`.

See `references/summarization.md`.

## Question answering (QA)

Two flavors:

**Closed-book QA** (no external context, model relies on training knowledge): high hallucination risk. Only safe for general knowledge tasks where verification isn't possible anyway.

**Open-book / RAG QA** (provide source documents): the standard production pattern.

```
Answer the question using only the information in <context>. If the answer is not in the context, output: "Not in provided context."

Cite each fact with the passage ID in [brackets].

<context>
[doc-1] {passage 1}
[doc-2] {passage 2}
...
</context>

<question>{question}</question>
```

Pitfalls:
- Retrieval quality often matters more than prompt quality.
- Models will guess if you don't explicitly license "I don't know."
- Multi-hop questions (needing info from multiple passages) often need CoT — see `prompt-reasoning`.

See `references/question-answering.md`.

## Code generation

```
You are a {language} engineer. Write the smallest correct implementation of the function described below.

Requirements:
- {explicit input/output spec}
- {edge cases to handle}
- {constraints: dependencies, style, etc.}

If anything is ambiguous, list the ambiguities at the top and pick a reasonable default for each.

<spec>{spec}</spec>

Return the code only, no commentary, in a fenced ```{language} block.
```

Pitfalls:
- Vague specs produce buggy code. Force the model to surface ambiguities up front.
- Models invent library APIs. Specify exact dependency versions; verify imports.
- For multi-file changes, decompose into smaller prompts.
- For modifying existing code, give the relevant file plus a unified diff format requirement.

See `references/code-generation.md`.

## Math / quantitative reasoning

Math is mostly a reasoning concern — see `prompt-reasoning` for CoT, self-consistency, and ReAct + calculator. Patterns specific to math prompts:

- For arithmetic over 3+ digit numbers, use a calculator tool (ReAct).
- For symbolic math, "show your work step by step" + symbolic constraints.
- Pin units explicitly in the question; pin the expected output format.

## Creative writing

```
You are a {persona}. Write a {form} about {topic}.

Constraints:
- {length}
- {tone, voice, register}
- {must-include or must-avoid}
- {audience}

If you'd like to draft a few approaches first, list 3 directions in one line each, then write the final piece based on the best one.
```

Pitfalls:
- Open prompts give average outputs. Constraints make outputs distinctive.
- "Be creative" rarely helps; specifying genre / constraints does.
- Iterate by critique loop (see `prompt-orchestration`) — single-shot creative prompts plateau.

See `references/creative-writing.md`.

## Image-generation prompts

Image-gen models reward different patterns than LLMs:

- **Subject before style.** Lead with what's depicted, then style modifiers.
- **Concrete adjectives.** "Wet cobblestone at dusk, warm yellow streetlamps" beats "moody street scene".
- **Negative prompts** (where supported). List what to exclude: text, watermarks, extra limbs, etc.
- **Camera / lens vocabulary.** "35mm, shallow depth of field, golden hour" channels photographic styles.
- **Aspect ratio / resolution** as separate parameters, not prompt text.

```
{Subject in detail}, {composition / pose}, {environment / setting}, {lighting}, {style / medium}, {camera / lens / mood}.

Negative prompt: {what to exclude}
```

Note that quality of image-gen output is model-specific — patterns that work for Stable Diffusion don't all transfer to DALL-E or Imagen.

See `references/image-gen.md`.

## Reference material

- `references/classification.md` — extended patterns and pitfalls for text classification.
- `references/extraction.md` — structured extraction patterns including dates, amounts, entities.
- `references/summarization.md` — faithful summarization patterns and length control.
- `references/question-answering.md` — RAG QA patterns and refusal handling.
- `references/code-generation.md` — code-gen patterns by task type (new code, modifications, reviews).
- `references/creative-writing.md` — constraint design for distinctive creative output.
- `references/image-gen.md` — prompt patterns for image-generation models.

## Sources distilled

This skill condenses material from the DAIR.AI Prompt Engineering Guide (applications, ChatGPT-specific, miscellaneous), the DAIR.AI prompts catalog (classification, coding, creativity, image-generation, information-extraction, mathematics, question-answering, text-summarization), and NirDiamant's Prompt Engineering techniques (specific-task-prompts). Reasoning-heavy tasks are cross-referenced to `prompt-reasoning`; output-shape concerns to `prompt-output-control`.
