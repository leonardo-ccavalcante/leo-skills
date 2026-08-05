# Prompt review — one-page checklist

Run through these when reviewing or rewriting a prompt. Stop at the first hit.

## Instruction
- [ ] One task per prompt (or clearly numbered if multiple).
- [ ] The instruction is at the top or bottom — not buried in the middle.
- [ ] Verbs are specific ("classify", "rewrite to 80 words", "extract"), not vague ("help with", "look at").

## Input
- [ ] User-supplied content is wrapped in delimiters (tags, headers, code fences).
- [ ] The prompt distinguishes context (background) from input (this case).

## Examples (if used)
- [ ] At least 2, no more than ~8 unless you have a reason.
- [ ] Cover edge cases, not just easy positives.
- [ ] Label-balanced and order-randomized for classification.
- [ ] Format identical to what you want for the real answer.

## Output format
- [ ] The desired format is described or shown literally.
- [ ] Length, tone, audience are specified if they matter.
- [ ] If you want structured output (JSON/YAML), an example schema is included.

## Negatives & constraints
- [ ] Negative instructions ("don't do X") are rephrased as positives where possible.
- [ ] Hard constraints (must/never) are reserved for genuine non-negotiables.

## Length
- [ ] No redundant restatements of the same rule.
- [ ] Sentences earn their place — anything not pulling weight is cut.
- [ ] If the prompt has three distinct phases ("analyze, critique, rewrite"), consider a chain (see `prompt-orchestration`).

## Persona (if used)
- [ ] Persona is justified — the task is judgment-laden enough to benefit.
- [ ] Persona doesn't contradict any other instruction.

If you ran the checklist and the prompt still under-performs, the next stops are:
- Reasoning techniques (`prompt-reasoning`) — for tasks needing multi-step logic.
- Output control (`prompt-output-control`) — for tasks where the format keeps drifting.
- Reliability (`prompt-reliability`) — for tasks where the answer is hallucinated or biased.
