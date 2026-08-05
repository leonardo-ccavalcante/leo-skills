# ReAct prompt template

ReAct (Reason + Act) interleaves "Thought:", "Action:", "Observation:" loops. The model writes the Thought and Action; your harness runs the Action and writes the Observation back into the prompt before the next turn.

## Template

```
You are an agent solving a task by reasoning and using tools.

Available actions:
- search(query): web search, returns top results
- calc(expression): evaluates a math expression
- finish(answer): submit the final answer

Format your turn as:
Thought: <one or two sentences about what to do next>
Action: <one action call>

After each action you'll see:
Observation: <result of the action>

Continue this loop until you call finish().

Task: {task}
```

The harness:
1. Sends this prompt + the task.
2. Parses the model's `Action:` line, executes it, returns the result.
3. Appends `Observation: <result>\n` to the conversation and re-prompts.
4. Stops when `Action: finish(answer)` is parsed.

## Common failure modes

**Model hallucinates observations.** If you don't actually run the action and feed back the real result, the model will invent plausible-sounding ones. This is the #1 ReAct bug. Verify your loop is real.

**Model loops without progress.** Same Thought, same Action, same Observation. Detect with a max-step cap (say, 10) and either fail or break out to a different prompt.

**Model returns malformed actions.** Output drifts from `search("q")` to `Search: q` to `I'll search for q`. Mitigate with few-shot examples in the prompt showing the exact format, and a parser that's strict.

**Thoughts get verbose.** Constrain with "Keep thoughts to one or two sentences."

**Tool errors stall the loop.** If a tool throws, return an Observation like `Error: timeout` and let the model decide whether to retry, try a different action, or finish with partial info.

## Self-consistency over ReAct

Sample N independent agent trajectories; pick the most common final answer. Costs N× but improves reliability on tasks where the agent occasionally takes wrong turns.

## When NOT to use ReAct

- Single-turn tasks that don't need tools — just use CoT.
- Tasks where the tool surface is too big and the model gets lost — pre-decompose with task decomposition first, then ReAct on each subtask.
- High-stakes actions that shouldn't be model-driven (deletes, payments) — keep those gated behind explicit human approval, not in the action loop.
