# Designing few-shot examples

Few-shot prompting works because models pattern-match. That same property is why bad example sets fail in surprising ways. These notes cover what experienced few-shot users have learned.

## When few-shot beats zero-shot

- Task has a non-obvious output format (custom JSON, particular bullet style, idiosyncratic tone).
- Task uses domain-specific vocabulary the model might gloss over.
- Task has subtle rules you can demonstrate faster than describe.
- Zero-shot is *almost* right and you can't pin down why.

## When few-shot underperforms

- Task is standard and the model already nails it zero-shot — added examples just bloat the prompt.
- You only have one or two examples and they're not representative — the model overfits to their surface features.
- Examples accidentally encode a spurious pattern (e.g., every positive example has a question mark) — the model picks up on the spurious cue rather than the real one.

## Selecting examples

**Cover the input space.** If your real inputs include short and long, formal and informal, easy and edge-case, your examples should too. Five easy cases teach the model that the task is easy.

**Mind the label balance.** For classification with N classes, aim for roughly N/k examples per class. Skewed distributions cause skewed predictions — models pick up on prior frequency and over-predict the majority class.

**Randomize order.** Don't cluster all positives, then all negatives. Mix them. Some patterns (last-example bias) creep in when ordering is monotonic.

**Match the real-input distribution.** If most real inputs will be terse one-liners, don't show only multi-paragraph examples. The model will assume verbose answers are expected.

## Common failure modes

- **Format leakage**: an example accidentally uses a different format than the others. Models often follow the most recent example's format. Audit for consistency before sending.
- **Spurious cues**: every "yes" example mentions a number; every "no" example doesn't. The model learns "presence of number = yes." Spot-check that no surface feature aligns with the label.
- **Demonstration too easy**: examples are all unambiguous; real inputs are ambiguous. The model never sees how to handle the hard cases. Add at least one tricky example with a brief justification baked into the output if needed.
- **Trailing whitespace**: an example output that ends with "\n\n" makes the model add extra newlines. Strip whitespace consistently.

## How many examples?

- 0 examples: only when the model nails it zero-shot. Cheaper, simpler.
- 1–3 examples: best for format clarification. The model learns the shape but stays general.
- 4–8 examples: best for tasks with multiple sub-patterns or edge cases.
- 8+: diminishing returns and the real instruction starts to drown. If you find yourself wanting 12+ examples, fine-tuning may be a better fit.

## A worked example pair

**Task**: tag customer-support messages with `intent` and `urgency`.

**Bad** (3 examples, all easy, format drifts):

```
Message: I can't log in.
intent: account_access; urgency: high

Message: How do I download my invoice?
Intent — billing, urgency = low

Message: My package never arrived and I leave for a trip tomorrow.
{intent: shipping, urgency: high}
```

Problems: format changes line to line, no medium-urgency case, no ambiguous case.

**Better**:

```
Message: I can't log in.
intent: account_access
urgency: high

Message: How do I download my invoice from last month?
intent: billing
urgency: low

Message: The product arrived but the box was crushed. Still works though.
intent: product_quality
urgency: medium

Message: My package never arrived and I leave for a trip tomorrow.
intent: shipping
urgency: high
```

Same format every time, covers all three urgency levels, and includes one ambiguous case (the crushed box) where the rule isn't obvious.
