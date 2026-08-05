---
name: prompt-foundations
description: Foundational prompt-engineering building blocks — anatomy of a prompt, clarity, formatting, length management, instruction crafting, zero-shot and few-shot prompting. Use this skill whenever the user wants to write, draft, refine, or critique a single prompt; asks "how should I prompt for X", "is this a good prompt", "what's a few-shot prompt", "make this prompt clearer", or is new to prompt engineering. Trigger even when the user doesn't say "prompt engineering" — any time the task is constructing or improving an LLM prompt at the single-prompt level (not multi-step chains, not reasoning techniques like CoT, not application-specific recipes). This is the default starting point when the user wants help asking an LLM something.
---

# Prompt Foundations

The job of this skill is to help the user write a single, well-formed prompt. Everything more advanced (chains, reasoning techniques, role-personas, output schemas, evals, safety) lives in a sibling skill — point the user there when relevant.

## When this skill is the right call

- The user is drafting or rewriting a single prompt.
- The user asks about basics: "how should I phrase this", "is this a good prompt", "what's the difference between zero-shot and few-shot".
- The user pastes a vague or messy prompt and wants it cleaner.
- The user wants the model to do something simple and is unsure how to ask.

If the user mentions chain-of-thought, self-consistency, tree-of-thoughts, ReAct → `prompt-reasoning`.
If the user wants a multi-step pipeline → `prompt-orchestration`.
If the user wants JSON/structured output → `prompt-output-control`.
If the user is doing classification, summarization, extraction, code-gen, etc. → `prompt-task-patterns`.

## Anatomy of a prompt

A prompt has up to six parts. Not every prompt needs all six — use only what the task calls for. Naming the parts helps the user think about what's missing.

1. **Instruction** — the verb. What you want the model to do.
2. **Context** — facts, background, retrieved passages the model needs.
3. **Input data** — the specific thing being acted on (text to classify, code to fix, etc.).
4. **Examples** — demonstrations of the input → output mapping (few-shot).
5. **Output format** — how the answer should look (one word, JSON, markdown table…). For deep treatment use `prompt-output-control`.
6. **Persona / role** — who the model is pretending to be. For deep treatment use `prompt-role-and-context`.

Naming them out loud when reviewing a prompt is a fast diagnostic. "You've got instruction and input, but no examples and no output format — that's why the model keeps drifting."

## The six principles

These compound — a prompt that violates one of them usually violates two or three.

### 1. Be specific about the task

Vague instructions invite vague answers. "Summarize this" leaves the model guessing about length, audience, and what to keep. "Summarize the article above for a tired executive, in 3 bullets, no jargon" gives it something to optimize against.

Specificity dimensions to consider: audience, length, tone, format, what to include, what to exclude, what to do if information is missing.

### 2. Use clear delimiters around input

When the prompt has both instructions and user-supplied content, separate them. Triple quotes, XML tags, markdown headers, or fenced code blocks all work. Without delimiters, models can mistake input for instruction (this is also how prompt injection sneaks in — see `prompt-security`).

```
Summarize the text between the <article> tags in one sentence.
<article>
{{user_text}}
</article>
```

### 3. Show, don't just tell

If you can write three examples of correct input/output faster than you can describe the rule, write the examples. Models pick up patterns from demonstrations more reliably than from prose specifications, especially for formatting, edge cases, and tone. This is few-shot prompting (covered below).

### 4. Put the most important instruction first or last

The middle of long prompts is the weakest position — models attend to it less reliably. The instruction itself ("Translate to French") should be at the top or repeated at the bottom after long context.

### 5. State positive instructions, not negative ones

"Write in plain English" beats "don't use jargon." Negative instructions force the model to first generate the forbidden thing and then suppress it — which often fails. Save negatives for hard constraints you actually need (see `prompt-output-control`).

### 6. Length: enough but not bloated

Long prompts are not automatically better. Each added sentence is overhead that competes for attention. The right length is whatever makes the task unambiguous and no more. If you find yourself writing a fifth paragraph of "and also", reach for examples instead — they convey constraints more efficiently than prose.

## Zero-shot vs. few-shot

**Zero-shot**: instruction with no examples. The model has to infer the task from the instruction alone. Works when the task is common (translation, sentiment, simple Q&A) and the instruction is unambiguous.

```
Classify the sentiment as positive, negative, or neutral.
Text: "The new update finally fixed the lag."
```

**Few-shot**: include 1–8 input/output examples before the real input. Use when:

- The task has a specific output format the model wouldn't guess.
- The task is unusual (made-up classification scheme, domain jargon, custom tone).
- Zero-shot kept getting it almost-right.

```
Q: Is this tweet about sports? Tweet: "He shoots, he scores!"
A: yes

Q: Is this tweet about sports? Tweet: "Just upgraded my GPU."
A: no

Q: Is this tweet about sports? Tweet: "Best dunk I've ever seen."
A:
```

**Tips for few-shot examples**:

- Pick examples that span the input space — include edge cases, not just easy positives.
- Balance the labels. Three "yes" and three "no" beats five "yes" and one "no" — models pick up on the imbalance and over-predict the majority class.
- Randomize order. Don't put all positives first then all negatives.
- Keep example formatting identical to what you want the real answer to look like. Down to capitalization and punctuation.
- More isn't always better. Past ~8 examples the gain flattens for most tasks; long demonstration lists also push the real instruction into the weak middle.

If the model is still wrong after 5–8 good examples, the issue is usually the instruction, not the example count — rewrite the instruction.

## Formatting & structure

- **Markdown headers and lists** help the model parse multi-part prompts.
- **Numbered steps** for instructions that must happen in order.
- **XML/HTML-style tags** are useful when you want the model to refer to specific spans (`<article>`, `<schema>`, `<examples>`). They're easier to nest than triple quotes.
- **Fenced code blocks** for code input/output, since they preserve whitespace.
- **Keep one task per prompt** when possible. Two unrelated asks in one prompt halve attention to each.

## Length & complexity management

Three handles when a prompt feels too long:

1. **Cut redundancy.** If two sentences say the same thing in different words, keep one. Models don't get more convinced by repetition; they get distracted.
2. **Replace prose with examples.** Three example pairs often replace a paragraph of rules.
3. **Split into stages.** If one prompt has to "first analyze, then critique, then rewrite," consider a chain — see `prompt-orchestration`.

Conversely, if the model keeps getting it wrong, the cure is rarely a longer prompt. It's a clearer one or one with examples.

## A short diagnostic checklist

When the user shares a prompt that "isn't working", run through these in order. Stop at the first hit.

1. Is the instruction in the first or last sentence, or buried in the middle?
2. Are inputs and instructions visually separated (tags, delimiters)?
3. Is the desired output format described or shown?
4. Are there examples? If not, would two examples help?
5. Are there negative instructions that could be rephrased positively?
6. Is the prompt asking for one thing or three? Split if three.
7. Is the audience/length/tone specified?

Most "bad prompt" cases are a miss on items 1–4.

## A worked rewrite

**Before** (the prompt the user came in with):

> can you help me figure out what this customer is mad about and how upset they are and write a response

**After** (applying the checklist):

> You are a customer-support agent. Read the customer email between <email> tags below. Then return a JSON object with three fields:
> - `complaint_category`: one of `billing`, `shipping`, `product_quality`, `account_access`, `other`
> - `severity`: integer 1–5, where 5 means the customer is threatening to churn or escalate publicly
> - `reply`: a 3-sentence response that acknowledges the issue, names the next step, and avoids promising specific timelines unless the email mentions one
>
> <email>
> {{customer_email}}
> </email>

What changed: split the three tasks, gave a closed-set classification, defined the severity rubric, constrained the reply, named the persona, delimited the input. Same underlying request, ten times more steerable.

## Reference material

- `references/six-part-anatomy.md` — longer treatment of the prompt anatomy with worked examples per part.
- `references/few-shot-design.md` — deeper notes on selecting and ordering examples, including pitfalls.
- `references/quick-checklist.md` — a one-page printable checklist for prompt review.

## Sources distilled

This skill condenses material from the DAIR.AI Prompt Engineering Guide (intro, basic usage) and NirDiamant's Prompt Engineering techniques (intro, basic structures, ambiguity/clarity, formatting, length/complexity, instruction engineering, zero-shot, few-shot). Hand off to sibling skills for everything beyond a single prompt.
