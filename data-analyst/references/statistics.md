# Statistics for analysts — which tool when

This is a field reference for Phase 3, not a course. The recurring sins it prevents:
p-values without effect sizes, comparisons with shifting denominators, and aggregate
conclusions that die at segment level.

## Which test when

| Question | Default tool | Notes |
|----------|-------------|-------|
| Did a rate change between two periods/groups? | Two-proportion z-test + difference with 95% CI | Report the difference in points AND relative terms; n matters |
| Did a mean change? | Welch's t-test (unequal variances default) | Check skew first; medians + Mann-Whitney for heavy tails |
| Is a trend real or noise? | Compare deviation to historical variance; STL or same-period-last-year for seasonality | A 5% move in a metric with 10% monthly variance is noise |
| Association between two categoricals? | Chi-square + Cramér's V for size | Chi-square alone says "exists", not "matters" |
| Association between two numerics? | Pearson (linear) / Spearman (monotonic) | Always plot first; correlation ≠ driver |
| Multiple drivers at once? | statsmodels OLS/logit with controls | Coefficients are associations; say "associated with", not "causes" |
| Small samples / weird distributions? | Bootstrap the CI | Cheap and honest |

## Effect size over p-value

A p-value answers "could this be chance?" — it says nothing about "does this matter?".
With big data everything is significant. Always report the magnitude (difference, ratio,
Cramér's V, R²) and its confidence interval; use the CI width to communicate certainty.
Practical rule for reports: lead with the effect ("churn rose 2.1pp, 95% CI [1.6, 2.6]"),
mention significance only when the result is *not* clearly significant.

## Multiple comparisons

Testing 20 segments at α=0.05 finds one "significant" segment by luck. When scanning
many dimensions (root-cause decomposition does exactly this), treat scan results as
candidates, not conclusions: confirm the winner on its own (isolation check — remove the
segment, the anomaly should disappear), or apply Benjamini-Hochberg if you must report
several.

## Denominators and mix — the analyst's traps

- **Denominator first.** Before interpreting any rate change, check whether the
  denominator changed. "Conversion dropped" when traffic doubled from a new low-intent
  source is a mix story, not a product story.
- **Simpson's paradox.** Aggregate and segment-level trends can point in opposite
  directions whenever group sizes shift. The segment-level view is usually the true
  behavioral story; the aggregate is what the business experiences. Report both and name
  the mix shift explicitly.
- **Decomposition.** For a rate R = Σ(share_i × rate_i), the change in R splits into a
  *rate effect* (Σ share_i,old × Δrate_i) and a *mix effect* (Σ Δshare_i × rate_i,new).
  Compute this split whenever mix is a candidate explanation — it turns an argument into
  a number.
- **Survivorship.** Every WHERE clause is a chance to silently drop the population that
  matters. Re-read filters when a result surprises you.

## Seasonality and time

- Compare same-period-prior-year before declaring a trend; weekday/weekend and
  month-length effects before declaring a daily anomaly.
- Never mix calendar grains in one comparison (a 4-week February vs a 5-week March).
- For "when did it start?", zoom the grain: monthly → weekly → daily. A step change
  points to an event; a drift points to mix or gradual causes.

## Confidence language for reports

Map evidence to words and keep them honest: strong evidence + validated → "shows /
drove"; consistent but observational → "the data suggests / is associated with";
suggestive, N small or confounded → "early signal / worth testing". Never "proves".
Uncertainty is information: a wide CI that includes "no effect" is a finding, not a
failure.
