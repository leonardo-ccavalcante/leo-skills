# Designing prompt evaluations

A short field guide for putting numbers on prompt quality.

## Pick the metric before you pick the eval method

Metric choice is downstream of *what good looks like* for your task. Some clarifying questions:

- Is there a single right answer, or many acceptable ones?
- If many, are they evaluable on the same axes (factuality, completeness, style)?
- What's the worst kind of failure? Inaccuracy? Verbosity? Latency? Hallucination?
- What rate of failure is tolerable in production?

Get crisp answers before designing the eval; otherwise you're measuring whatever's easy and missing whatever matters.

## Metric menu by task type

### Closed-set classification

- **Accuracy**: simple but misleading on imbalanced classes.
- **Per-class F1**: surfaces under-represented classes.
- **Confusion matrix**: shows *which* errors. Often the most useful artifact.

### Extraction (structured fields)

- **Field-level precision/recall**: per-field, then averaged. Missing field ≠ wrong field.
- **Schema validity rate**: proportion of outputs that parse correctly.

### Open generation (writing, summarization)

- **LLM-as-judge with rubric**: usually best. Define 2–5 axes (faithfulness, completeness, style, ...) with 1–5 scales.
- **ROUGE/BLEU**: classical lexical-overlap scores. Cheap and reproducible but only measures surface similarity.
- **Human pairwise comparison**: gold standard for subjective quality, but slow and expensive.

### QA with reference answer

- **Exact match**: rigid but unambiguous.
- **Semantic match via LLM-as-judge**: "does the candidate's answer convey the same info as the reference?"

### Multi-step pipelines

- **End-to-end accuracy**: pass/fail at the final step.
- **Per-step accuracy**: where in the chain do failures originate?

Always report end-to-end *and* per-step. End-to-end tells you whether the system works; per-step tells you where to fix.

## Golden set construction

Aim for a set that, if your prompt passes it, you'd ship.

- **Size**: 50–200 for most use cases. Smaller is a smoke test; bigger has diminishing returns until distribution shift becomes a concern.
- **Coverage**: stratify across input types. If real users span B2B and B2C, both go in the set.
- **Edge cases**: include known-tricky inputs. Past bug reports are golden — literally turn them into eval cases.
- **Negatives**: include inputs where the right answer is "decline" or "no info available."
- **Labeling**: ideally two raters per item with a disagreement-resolution process. At minimum, document who labeled and when.
- **Versioning**: lock the set. Date-stamp it. New eval cases go into a v2 set, not into the existing one.

## Held-out test set

Don't iterate against the same set you use for the go/no-go decision. Hold out 20–30% of cases at the start, untouched, and only run them at decision time.

## LLM-as-judge prompt design

A good judge prompt:

- Defines axes explicitly, each with a short rubric.
- Gives examples of high-score and low-score outputs per axis.
- Asks for a structured output (JSON with one field per axis).
- Discourages tie scores ("don't use 3 unless you genuinely can't decide").
- Is run with low temperature for reproducibility.

A bad judge prompt:

- "Is this answer good? Score 1-10." Too subjective; judges drift.
- "Compare A and B." First-position bias unless you randomize order.
- "Be lenient." Lenient judges don't discriminate.

## Statistical hygiene

- **Confidence intervals.** If your golden set is N=50 and prompt A scores 80% vs. B at 84%, that's within noise.
- **Paired comparisons.** Run both prompts on the *same* inputs; compare paired outcomes. Reduces noise vs. independent runs.
- **Multiple seeds for non-deterministic outputs.** If temperature > 0, run each input 3+ times and average.
- **Watch for goodharting.** "Maximize judge score" can produce outputs the judge likes but humans don't. Sanity-check periodically with human review.

## Cost / latency / quality trade-off

Most "improvements" trade one axis for another. Track all three:

| Variant | Pass rate | p50 latency | $/1k calls |
|---|---|---|---|
| Baseline (zero-shot) | 71% | 1.2s | $1.40 |
| + few-shot examples | 78% | 1.4s | $1.60 |
| + CoT trace | 84% | 2.8s | $3.20 |
| + self-consistency N=5 | 89% | 5.1s | $16.00 |

The "best" prompt is the one with the right trade-off for the use case, not the highest pass rate.
