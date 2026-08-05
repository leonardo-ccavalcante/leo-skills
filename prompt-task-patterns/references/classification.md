# Text classification — extended patterns

Classification is the most-used LLM application pattern. It's also where naive prompts fail in the most predictable ways. Patterns and pitfalls below.

## The skeleton, fleshed out

```
You are a classifier for {domain}.

Classify the text below into exactly one of these labels:
- {label_1}: {definition with examples of what fits / doesn't fit}
- {label_2}: {definition}
- ...
- other: use only when no other label fits

Output one of the labels, lowercase, no punctuation, no explanation.

<text>
{input}
</text>
```

## Why definitions matter

The model has its own priors about what "billing" means. If your "billing" includes subscription pauses but your "account" handles them, the model will guess based on its prior — not your policy. Pin the definitions:

```
- billing: charges, refunds, invoices, payment failures, plan upgrades/downgrades.
- account: login, password reset, profile changes, account closure.
- billing or account?: pauses count as billing; deletion counts as account.
```

The "edge case clarifications" line is often the most valuable part of the prompt.

## Adding examples (few-shot)

For classification, examples beat description. Aim for 2 per label, including at least one tricky case per label:

```
Examples:

Text: My card was charged twice for the same order.
Category: billing

Text: I can't reset my password — the email never arrives.
Category: account

Text: I want to pause my subscription for two months.
Category: billing

Text: Please delete all my data.
Category: account

Text: The product is great!
Category: other

Now classify:
Text: {input}
Category:
```

Notes:
- Balance the label counts.
- Randomize the order across labels.
- Include "other" examples so the model learns when not to force a category.

## Handling low confidence

For high-stakes classification, force the model to flag uncertainty:

```
If confident: output the label.
If uncertain: output "uncertain".

Use "uncertain" when the text could reasonably be classified under two or more categories, or doesn't fit any clearly.
```

Then route "uncertain" cases to a human or to a second-pass model.

## Multi-label classification

When a single item can have multiple labels, switch to JSON:

```
Output a JSON array of all applicable labels from: {label set}.
If none apply, output [].

<text>{input}</text>
```

## Hierarchical classification

For label hierarchies (e.g., "billing > refunds > international card"), prompt the top level first, then dispatch to a level-2 prompt. Don't try to enumerate the leaf-level taxonomy in one prompt — too many options degrade accuracy.

## Calibration

LLM classifiers tend to over-predict labels that are well-represented in their training data and the most "vivid" in the prompt. To debug:

- Run the classifier on a balanced set (equal counts per label) and check confusion.
- If one label dominates, look for: (1) imbalanced examples, (2) ambiguous definitions, (3) a label name that's a high-frequency English word.

## When NOT to use an LLM classifier

- The labels are simple keyword matches → use regex. Cheaper, faster, more reliable.
- The label distribution is fixed and you have lots of labeled data → fine-tune a small model. Cheaper inference.
- The classification is a hot path (>100 QPS, latency-sensitive) → consider fine-tuning or distillation.

LLM classifiers shine when:
- The decision needs language understanding (sarcasm, context, intent).
- The label set evolves and you don't want to retrain.
- The dataset is too small for training a discriminative model.
