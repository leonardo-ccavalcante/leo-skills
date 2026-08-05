---
name: prompt-reasoning
description: Techniques that elicit deeper reasoning from an LLM — Chain-of-Thought (CoT), zero-shot CoT, self-consistency, Tree-of-Thoughts (ToT), ReAct, Generated Knowledge, Automatic Prompt Engineer (APE), and task decomposition. Use whenever the user wants the model to "think step by step", reason through math or logic, solve multi-step problems, plan before acting, or shows a prompt that gets the wrong answer because the model jumped too fast. Trigger on phrases like "chain of thought", "step by step", "reasoning", "math problem", "logic puzzle", "the model rushes", "complex reasoning", "tree of thoughts", "ReAct", "self-consistency", "plan then act". Do not trigger for simple lookups or classification — those go to prompt-foundations or prompt-task-patterns.
---

# Prompt Reasoning Techniques

When a model gets the wrong answer on a problem that requires more than one mental step, the fix is almost never "tell it harder" — it's to make the reasoning visible and verifiable. This skill is the catalog of techniques for doing that.

## When this skill is the right call

- Math, logic, multi-hop questions, planning tasks.
- The model keeps giving fluent but wrong answers ("rushes to a conclusion").
- The user mentions CoT, ToT, ReAct, self-consistency, or decomposition by name.
- The user wants the model to plan, then act (especially with tools).

Not the right skill if:
- The task is a simple one-step lookup → `prompt-foundations`.
- The user wants a specific output schema → `prompt-output-control`.
- The user wants reliability/factuality across many runs → `prompt-reliability` (which builds on self-consistency).

## The technique map

```
Reasoning techniques
├── Single-pass
│   ├── Chain-of-Thought (CoT, few-shot)         — show reasoning examples
│   ├── Zero-shot CoT                            — "Let's think step by step"
│   └── Generated Knowledge                      — generate facts, then answer
├── Multi-pass / sampling
│   ├── Self-consistency                         — sample N reasoning paths, vote
│   └── Automatic Prompt Engineer (APE)          — model proposes better prompts
├── Search-structured
│   └── Tree-of-Thoughts (ToT)                   — branch, evaluate, prune
├── Tool-augmented
│   └── ReAct                                    — interleave reasoning + actions
└── Pre-prompt
    └── Task decomposition                       — split before solving
```

Pick by problem shape (see `references/picking-a-technique.md` for the decision tree).

## Chain-of-Thought (CoT)

The original. Show the model 2–8 examples where the answer comes *after* a written-out reasoning trace. The model imitates the trace style and produces its own intermediate steps for new inputs.

```
Q: Roger has 5 tennis balls. He buys 2 cans of 3 each. How many does he have?
A: Roger started with 5. 2 cans of 3 each is 6. 5 + 6 = 11. The answer is 11.

Q: The cafeteria had 23 apples. They used 20 for lunch and bought 6 more. How many do they have?
A:
```

CoT helps most on arithmetic, multi-hop QA, symbolic reasoning. It helps least on tasks the model already solves zero-shot (added overhead) or tasks that don't decompose into steps (style/tone tasks).

## Zero-shot CoT

Just append "Let's think step by step." (or "Let's work this out step by step to be sure we have the right answer.") to the prompt. The model produces a reasoning trace without any examples. Cheaper than few-shot CoT; less reliable on hardest problems but a solid default.

```
A juggler can juggle 16 balls. Half are golf balls and half of the golf balls are blue.
How many blue golf balls are there?

Let's think step by step.
```

Use zero-shot CoT as your first move; reach for few-shot CoT only if it's not enough.

## Self-consistency

Sample N reasoning paths (typically 5–20) with non-zero temperature, then take the majority vote over final answers. The intuition: correct reasoning paths agree more often than incorrect ones — they converge on the same answer through different routes.

Use when:
- The cost of being wrong is high enough to justify N× more calls.
- The answer space is small (numbers, short labels) so voting works.

Don't use when the answer is open-ended prose — voting doesn't make sense across paragraph-length outputs. For open-ended outputs, consider an LLM-as-judge to pick the best of N (covered in `prompt-reliability`).

## Generated Knowledge

Two-stage. First prompt the model to write down the facts it would use. Then feed those facts back in as context and ask the question.

```
Stage 1: "List the key facts about how a turbine engine generates thrust."
Stage 2: "Given these facts: <stage 1 output> — answer: would a turbine engine work in vacuum? Why?"
```

Works best when the model has the knowledge but doesn't always retrieve it — generating it up front forces retrieval into the reasoning context. Less useful when the model lacks the knowledge entirely (then you need retrieval-augmented generation, not generated knowledge).

## Tree-of-Thoughts (ToT)

For problems with branching solution paths (puzzles, planning, search). Instead of one linear reasoning chain, generate K candidate next-thoughts at each step, evaluate them (often by asking the model to score each), and keep only the most promising. Continue until a leaf is reached.

ToT is heavier than CoT — typically 5–20× the tokens. Worth it for problems where a single chain frequently dead-ends (Game of 24, crosswords, route planning).

A simple ToT prompt skeleton:

```
Solve this puzzle: <puzzle>

Approach:
1. Propose 3 different first moves.
2. For each, evaluate whether it can lead to a solution. Eliminate dead ends.
3. For the surviving moves, propose 3 follow-ups. Evaluate again.
4. Continue until you reach a solution or all branches are exhausted.
5. Output the final solution path.
```

## ReAct (Reason + Act)

Interleave reasoning with tool calls. The model alternates between "Thought:" steps (planning what to do) and "Action:" steps (calling a tool: search, calculator, code execution). After each action, "Observation:" steps record what came back, and the loop continues.

```
Thought: I need to find when X was born.
Action: search("when was X born")
Observation: X was born in 1947.
Thought: Now I need the year Y died.
Action: search("when did Y die")
Observation: Y died in 1985.
Thought: 1985 - 1947 = 38. X was 38 when Y died.
```

Use ReAct when:
- The task needs external information the model doesn't have.
- The task needs deterministic computation (don't make the model do long arithmetic — call a calculator).
- The model needs to verify a fact before continuing.

ReAct requires a harness that actually runs the actions and feeds back observations. Don't write ReAct prompts that pretend to call tools — that's just CoT with extra steps.

## Automatic Prompt Engineer (APE)

Have an LLM generate candidate prompts and an LLM-as-judge score them on a small eval set. Pick the highest-scoring one. The Kojima et al. result that "Let's work this out in a step by step way to be sure we have the right answer" beats hand-written zero-shot CoT prompts is the canonical example.

This is an optimization technique, not something you'd hand-run for one task. Practical use lives in `prompt-reliability` (which covers eval-driven prompt iteration in depth).

## Task decomposition

Before solving, split. Either:

- **Static decomposition**: you, the prompt-writer, list the subtasks up front and prompt the model on each in turn.
- **Dynamic decomposition**: ask the model to list the subtasks, then have it solve each.

Decomposition helps when the task has clearly separable subgoals (write outline → draft each section → assemble; parse → analyze → summarize). It hurts when the subtasks are interdependent and need to be reasoned about jointly — then forcing them apart loses information.

If you're chaining the subtasks across separate LLM calls, that's prompt-orchestration territory.

## Picking the right technique — short version

| Problem | First try | Then try |
|---|---|---|
| Single arithmetic / one-shot logic | Zero-shot CoT | Few-shot CoT |
| Multi-step word problem | Few-shot CoT | Self-consistency |
| Search / planning with branches | CoT | Tree-of-Thoughts |
| Needs external facts or tools | ReAct | ReAct + self-consistency |
| Model knows but forgets | Generated Knowledge | RAG (out of scope) |
| Composite task, separable | Task decomposition | Prompt chaining (see `prompt-orchestration`) |
| You don't know yet | Zero-shot CoT, observe | Pick based on failure mode |

## A worked example

User has a customer-support classifier that confuses "billing" and "account_access" when the email talks about not being able to access a payment receipt. Zero-shot prompt classifies wrong.

**Naive fix**: add "Be more careful." Doesn't help.

**Zero-shot CoT**: "Classify this email. Before answering, think step by step about whether the customer's primary issue is *gaining access* to something or *fixing a charge or invoice*." → often enough.

**Few-shot CoT** if zero-shot still fails: include 3 examples with traces like "The customer mentions a receipt, but their underlying problem is that they can't *find* the receipt. That's access. Category: account_access."

**Self-consistency** if accuracy still matters: sample 5 reasoning paths at temperature 0.7, take the majority label.

Stop escalating when accuracy is good enough — each step costs more tokens and latency.

## Reference material

- `references/picking-a-technique.md` — decision tree by problem shape and failure mode.
- `references/cot-recipes.md` — drop-in CoT, zero-shot CoT, and few-shot CoT templates with examples.
- `references/react-template.md` — ReAct prompt skeleton with observations on common failure modes.

## Sources distilled

This skill condenses material from the DAIR.AI Prompt Engineering Guide (advanced usage — CoT, zero-shot CoT, self-consistency, generated knowledge, APE), the DAIR.AI prompts catalog (reasoning, mathematics), and NirDiamant's Prompt Engineering techniques (CoT, self-consistency, task decomposition). ToT and ReAct are summarized from the original Yao et al. papers.
