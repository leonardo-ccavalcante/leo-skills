# Chain design patterns

A catalog of prompt-chain shapes. Pick by the shape of the work, not by what sounds clever.

## Linear chain (A → B → C)

The default. Step A produces input for B, B for C.

When to use: clear sequential phases where each phase needs different framing.

```
A: extract structured info from raw text
B: enrich with computed fields (often plain code, not LLM)
C: format for output
```

Failure mode to watch: if any step's output drifts off-format, downstream steps cascade-fail. Use structured outputs (`prompt-output-control`) and validate at boundaries.

## Branching (A → {B, C, D} → merge)

A determines which downstream branches run, or several branches run in parallel and a merge step combines results.

When to use: tasks with parallelizable sub-questions (research, multi-aspect critique, multi-document summarization).

```
A: classify query intent
{B: factual lookup, C: opinion synthesis, D: action plan}: branch by intent
```

Failure mode: merge step gets long context. Mitigate with map-reduce-style intermediate summaries.

## Routing (A → one of {B, C, D})

A classifier picks exactly one downstream prompt. The unchosen ones don't run.

When to use: specialized prompts per intent type — different system prompts, different few-shot examples, sometimes different models.

```
A: route(query) → "billing" | "technical" | "sales"
B-billing, C-technical, D-sales: each with its own specialized prompt
```

Failure mode: misrouting silently sends a billing question to the technical prompt. Add a confidence threshold; route to a fallback when uncertain.

## Critique loop (draft → critique → revise [→ loop])

Two or more agents (or the same model with different personas) iterate on the same artifact.

When to use: writing, code review, design feedback — anywhere "first draft is rarely good enough".

```
A: draft
B: critique with explicit checklist (persona: senior reviewer)
C: revise given critique
[D: critique again, terminate when no major issues]
```

Failure mode: infinite or unproductive loops. Cap iterations at 2–3. Add a termination check ("if the critique has no major issues, output 'DONE'").

## Map-reduce (run B over N items → aggregate with C)

Run the same prompt over a dataset, then synthesize.

When to use: extracting from a corpus, then summarizing.

```
A: each_item → extract(item)  [map, parallelizable]
B: all_extracts → synthesize  [reduce, single call]
```

Failure mode: reduce step exceeds context. Mitigate with hierarchical reduce (reduce in groups, then reduce the reductions) or rolling summary.

## Plan-then-execute (A: plan → B: execute(plan))

A planner produces an explicit plan; an executor (often a different model or persona) carries it out step by step.

When to use: when planning is the hard part and execution is mechanical, or vice versa.

```
A: produce a numbered plan of subtasks
B: for each subtask in plan: solve subtask
[C: assemble subtask outputs]
```

Failure mode: plan looks reasonable but is wrong. Mitigate by adding a "validate plan" step before execution starts.

## Self-consistency on a chain (run the chain N times, vote)

Run the whole chain N times with non-zero temperature; vote on final answers.

When to use: high-stakes final answer, discrete output, you can afford N× cost.

Don't confuse with self-consistency over a *single* CoT prompt (which is in `prompt-reasoning`) — same idea, applied to a multi-step pipeline.

## Anti-pattern: long chains "for safety"

A common mistake is chaining more steps than the problem needs, on the theory that more validation = more reliable. Often the opposite: each step adds a failure mode, latency, and cost. Use chains where they help; trim them to the minimum that works.

A useful gut check: after building a 5-step chain, ask "what does step 3 actually add vs. just doing 1-2-4-5?" If you can't answer crisply, delete step 3.
