---
name: prompt-reliability
description: Make prompts trustworthy at scale — evaluation methods (golden sets, LLM-as-judge, A/B), prompt optimization, hallucination and factuality mitigation, bias reduction, calibration, and grounding strategies (RAG framing, citation prompts). Use whenever the user wants to test, measure, or improve a prompt's reliability across many inputs; whenever they're worried about hallucinations, bias, or inconsistency; whenever they're comparing two prompt versions; whenever they want the model to refuse confidently or say "I don't know"; or whenever they need to ground answers in source material. Trigger on phrases like "evaluate prompt", "test prompt", "golden set", "hallucination", "fact-check", "factuality", "the model invents", "the model is biased", "consistency", "self-consistency for reliability", "LLM as judge", "A/B test prompt", "ground truth", "citation", "I don't know". Do not trigger for prompt injection / adversarial attacks (use prompt-security) or for in-prompt reasoning techniques (use prompt-reasoning).
---

# Prompt Reliability

A prompt that works on three hand-picked examples is not the same as a prompt that works on a thousand real inputs. This skill is about closing that gap. Three threads run through it:

1. **Evaluation** — how to measure whether a prompt is good.
2. **Optimization** — how to iterate on prompts using those measurements.
3. **Failure mitigation** — reducing hallucinations, bias, and inconsistency.

## When this skill is the right call

- The user wants to evaluate or A/B test a prompt.
- The user is building a golden set or held-out test set.
- The user mentions hallucinations, factuality, grounding, citations.
- The user is concerned about bias in outputs (label imbalance, demographic, recency).
- The user wants the model to say "I don't know" instead of guessing.
- The user is iterating with an LLM-as-judge or human review loop.

Not the right call if:
- The user wants to defend against prompt injection or jailbreaks → `prompt-security`.
- The user wants to make the model reason better → `prompt-reasoning`.
- The user wants better output format → `prompt-output-control`.

## Evaluation — three levels

**Level 1: vibes / spot-check.** Run the prompt on 3–5 hand-picked inputs and read the outputs. Fine for early prototyping; useless past that.

**Level 2: golden set.** Curate a fixed set of 20–200 inputs with known expected outputs. Run the prompt over the set automatically; compare outputs to expected; track pass rate. The cheapest way to detect regressions when you tweak the prompt.

**Level 3: live evaluation.** Sample real production traffic, evaluate continuously (often with LLM-as-judge or human review). Catches drift, distribution shift, and rare failure modes the golden set missed.

Most teams should be at Level 2 within a week of putting a prompt in front of users.

## Building a golden set

A golden set is your prompt's regression-test suite. Properties of a good one:

- **Covers the input distribution.** Include common cases AND tail cases. If 80% of real inputs are short and English, your set should be too — plus enough rare cases to keep you honest.
- **Includes hard cases.** A golden set of only easy inputs flatters every prompt. Add adversarial inputs, ambiguous inputs, edge-of-policy inputs.
- **Labeled by humans, when possible.** For subjective outputs, two-rater agreement is a useful signal. If only one human labels, document who and when.
- **Versioned.** Lock the set. Don't keep "improving" it during prompt iteration — that's how you accidentally overfit.
- **Big enough to be statistically useful.** 20 inputs is a smoke test; 100+ is a real benchmark.

## Choosing an evaluation method per task

| Task type | Eval method |
|---|---|
| Classification (closed set) | Accuracy, F1, confusion matrix |
| Extraction (structured) | Field-level precision/recall |
| Summarization | LLM-as-judge on faithfulness + completeness; ROUGE if a reference exists |
| Open generation (writing) | LLM-as-judge with rubric; human review on a sample |
| QA with ground truth | Exact-match or LLM-as-judge for semantic match |
| Multi-step pipelines | Per-step accuracy + end-to-end accuracy |

LLM-as-judge note: use a different model from the one being tested when possible. Same-model judges have correlated failure modes.

## LLM-as-judge — practical pattern

```
You are evaluating the quality of an answer. Be strict and honest.

Question: {question}
Reference answer: {ground_truth}
Candidate answer: {candidate}

Score the candidate on:
- Faithfulness (1-5): does it stay grounded in the reference? Hallucinations lose points.
- Completeness (1-5): does it cover the same key points?
- Style (1-5): clarity, conciseness, tone.

Return JSON: {"faithfulness": N, "completeness": N, "style": N, "notes": "..."}
```

Pitfalls:
- Position bias: judges tend to prefer the first option in pairwise comparisons. Randomize order.
- Length bias: judges over-reward longer answers. Pin the rubric to specific qualities, not "thoroughness".
- Self-preference: a judge prefers its own model family. Use a different model when feasible.

## Prompt optimization — the loop

1. Pick a metric (accuracy, judge score, latency, cost — usually a weighted combo).
2. Run the current prompt on the golden set; record baseline.
3. Hypothesize an improvement; change the prompt.
4. Re-run on the same golden set; compare to baseline.
5. If better and you trust the comparison, keep the change. Else, revert.

A few hygiene rules:
- **Change one thing at a time** when possible. Otherwise you don't know which change moved the needle.
- **Use a held-out test set** for the final go/no-go decision, separate from the iteration set. Otherwise you overfit to the iteration set.
- **Watch for regression on tail cases.** A change can lift the average and break a critical edge case.

Automatic Prompt Engineer (APE) approaches use an LLM to generate candidate prompts and another to evaluate. Useful when manual iteration plateaus.

## Hallucination and factuality

Models hallucinate (produce confident but false statements) most when:
- The model doesn't have the knowledge but the prompt pushes for an answer.
- The prompt rewards confident-sounding outputs.
- The retrieval context is missing or incorrect.

Mitigations, in rough order of effectiveness:

**1. Ground in retrieved context (RAG).** Give the model the relevant passage(s) and instruct it to answer only from them.

```
Answer the question using only the information in <context>...</context>. If the context doesn't contain the answer, output: "Not in provided context."
```

**2. Explicit "I don't know" license.** Tell the model it's OK to refuse.

```
If you're not sure, say "I'm not sure" instead of guessing. Confidently wrong answers are worse than honest uncertainty.
```

**3. Cite-as-you-go.** Require citations for factual claims.

```
For each factual claim, cite the source passage in brackets like [source-id-3]. Claims without citations are not allowed.
```

**4. Self-check pass.** After answering, ask the model to fact-check its own answer against the context. Cheap second pass.

**5. Lower temperature for factual tasks.** High temperature increases diversity, which also increases hallucination rate. For factual extraction, temperature near 0 is usually best.

Notes:
- RAG quality is more important than prompt quality for factual tasks. A bad retrieval gives the model the wrong context to hallucinate from.
- Self-reported confidence is weak signal. Don't trust the model's own claim that it's 90% sure.

## Bias reduction

Sources of bias in prompted outputs:

- **Label imbalance in few-shot examples.** 4 positive + 1 negative example biases toward positive predictions. Balance.
- **Order effects in few-shot.** Models pick up on the most-recent label. Randomize.
- **Anchoring from input phrasing.** "Is this clearly negative?" biases the model toward "yes". Use neutral phrasings.
- **Demographic bias.** Tasks involving names, locations, professions can produce stereotyped outputs. Mitigations: explicit instructions to ignore protected attributes, audit outputs across demographic slices, fine-tuning when high-stakes.
- **Recency / training cutoff bias.** Models over-rely on facts from their training distribution. Mitigate by retrieving current sources and grounding.

## Calibration

A well-calibrated model says "70% confident" only when it's right 70% of the time. Most prompt-elicited confidence is poorly calibrated — models tend to overconfidence.

Two practical patterns:

**Pattern: ordinal labels instead of probabilities.** Replace "confidence 0-1" with "very confident / somewhat confident / uncertain". Categorical bands are more reliably interpretable.

**Pattern: verifier model.** Train (or prompt) a separate model to assess whether the primary answer is correct. The verifier's signal is often better-calibrated than the primary model's own confidence.

For high-stakes decisions, fall back to humans on low-confidence outputs.

## A worked example

User has a summarization prompt for legal documents. Sometimes it invents clauses that aren't in the document.

**Diagnosis**: classic hallucination on grounded task.

**Fix stack**:

1. **Ground harder.** "Summarize using only information in <doc>...</doc>. Quote the exact text for each key clause you mention."
2. **License refusal.** "If a topic the summary needs isn't in the document, say 'Not specified in document' for that topic."
3. **Self-check.** Second LLM call: "Here is the summary. Here is the source document. For each claim in the summary, mark it as SUPPORTED, CONTRADICTED, or NOT_IN_SOURCE."
4. **Eval.** Build a golden set of 50 legal docs with expert-written summaries; measure faithfulness with LLM-as-judge.
5. **Track.** When you tweak the prompt later, re-run the golden set and check the faithfulness delta.

Stop at the first level that meets the bar.

## Reference material

- `references/eval-design.md` — how to design a golden set and pick metrics for different task types.
- `references/factuality-checklist.md` — pre-launch checklist for hallucination risk.

## Sources distilled

This skill condenses material from the DAIR.AI Prompt Engineering Guide (reliability), the DAIR.AI prompts catalog (evaluation, truthfulness), and NirDiamant's Prompt Engineering techniques (evaluating prompt effectiveness, prompt optimization). Self-consistency as a technique lives in `prompt-reasoning`; here it's framed as a reliability tool.
