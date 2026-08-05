# Drop-in CoT recipes

Copy-paste templates for the three CoT variants. Swap the placeholders for your task.

## Zero-shot CoT (cheapest, try first)

```
{task_instruction}

{input_data}

Let's think step by step.
```

Variants that empirically work well on hard problems:
- "Let's work this out in a step by step way to be sure we have the right answer."
- "Take a deep breath and work through this problem step by step."
- "Before answering, walk through your reasoning."

Use one. They have similar effect; just pick the one that fits your tone.

## Few-shot CoT

```
{task_instruction}

Example 1:
Input: {ex1_input}
Reasoning: {ex1_trace}
Answer: {ex1_answer}

Example 2:
Input: {ex2_input}
Reasoning: {ex2_trace}
Answer: {ex2_answer}

Example 3:
Input: {ex3_input}
Reasoning: {ex3_trace}
Answer: {ex3_answer}

Now solve:
Input: {real_input}
```

The example traces are the actual signal. Make them:
- Plausibly written by a careful human (not robotic).
- Long enough to capture the genuine steps, short enough to scan.
- Honest about where intuition is involved ("the 7 is the trickiest; here's why...").
- Consistent in style across examples.

If you can't write good traces, fall back to zero-shot CoT.

## CoT with self-consistency

Wrap any CoT prompt in N independent samples:

```python
# pseudocode
answers = []
for _ in range(N):
    response = llm.generate(cot_prompt, temperature=0.7)
    answer = extract_final_answer(response)
    answers.append(answer)

final = most_common(answers)
```

Notes:
- Temperature matters. 0 gives identical paths (no diversity); typical range is 0.5–0.8.
- N=5 is the cheap-but-useful default; N=20 is the diminishing-returns ceiling for most tasks.
- Only useful for discrete answers. For prose, use LLM-as-judge instead (see `prompt-reliability`).
- `extract_final_answer` is its own headache — design the prompt to make extraction unambiguous (e.g., "End with: 'Final answer: X'").

## Output-format note

For all three variants, decide whether you want the reasoning in the output or just the final answer:

- **Reasoning visible**: best for debugging, evaluation, user trust. Costs tokens.
- **Reasoning hidden**: cheaper to display, but you lose the audit trail. Often implemented as "think internally, then output only the final answer in JSON" — but the model still produces the reasoning in its output, so this is mostly a display concern.

For production systems, "reasoning visible in logs, answer extracted for the user" is the common pattern.
