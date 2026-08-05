# Picking a reasoning technique

The choice is driven by **problem shape** and **failure mode**, not by what sounds fanciest.

## Problem shape questions

**Q1: Does the problem have intermediate steps a human would write down?**
- Yes → CoT family (zero-shot CoT first, few-shot CoT if needed).
- No (it's one-shot judgment, pattern matching, style) → CoT is overhead; use plain prompting.

**Q2: Are there branching paths to explore?**
- Yes (puzzles, planning, "best of N moves") → Tree-of-Thoughts.
- No → stay with CoT.

**Q3: Does the model need information it doesn't have?**
- Knowledge it *might* have but doesn't always surface → Generated Knowledge.
- Knowledge it definitely lacks (recent events, private data) → retrieval-augmented generation (out of scope for this skill).
- Needs a precise computation or live data → ReAct with tools.

**Q4: How costly is being wrong?**
- High (one shot, hard to verify) → self-consistency with 5–20 samples and majority vote.
- Low (cheap to retry, human-in-the-loop) → single CoT pass.

**Q5: Is the answer a discrete value or open prose?**
- Discrete (number, label, short string) → self-consistency works.
- Open prose → vote doesn't apply; use LLM-as-judge (in `prompt-reliability`).

## Failure-mode questions

**"The model gives a fluent but wrong final answer."**
→ Add CoT. The model isn't taking the steps it needs.

**"The model takes the steps but gets the arithmetic wrong."**
→ ReAct + calculator tool, or self-consistency over CoT.

**"The model takes the steps but they're inconsistent across runs."**
→ Self-consistency with N=5+ and majority vote.

**"The model commits to a wrong path early and can't recover."**
→ Tree-of-Thoughts, or decomposition that creates an explicit revision step.

**"The model invents facts."**
→ Not a reasoning problem. See `prompt-reliability` (factuality, grounding, RAG).

**"The model gets each sub-step right but combines them wrong."**
→ Task decomposition + chained calls (`prompt-orchestration`).

## Cost order, roughly

From cheapest to most expensive:

1. Plain prompt (1 call, no extras)
2. Zero-shot CoT (1 call, slightly longer output)
3. Few-shot CoT (1 call, longer prompt and output)
4. Generated Knowledge (2 calls)
5. ReAct (variable, depends on tool calls)
6. Self-consistency over CoT (N calls)
7. Tree-of-Thoughts (often 5–20× CoT)
8. Self-consistency over ToT (rarely worth it; budget-buster)

Start cheap. Escalate only when you've measured that the cheap option falls short.

## Combining techniques

Most combinations are valid; common ones:

- **CoT + self-consistency** — the canonical reliability boost for math/logic.
- **ReAct + self-consistency** — sample multiple agent trajectories.
- **Task decomposition + chained prompts** — break the problem then chain.
- **Generated Knowledge + CoT** — generate facts, reason over them.

Avoid stacking three layers without measuring; each layer multiplies cost and adds failure modes.
