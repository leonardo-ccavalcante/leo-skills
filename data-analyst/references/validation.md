# Phase 4 — CHALLENGE: the validation pass

Distilled from the CIA Structured Analytic Techniques (see the `sat` skill for the full
12 techniques) and ai-analyst's triangulation / semantic-validation / guardrails skills.
This phase exists because the most dangerous analysis is the one that confirms what
everyone already believed, delivered with confident numbers. Nothing leaves Phase 4
unchallenged.

## 1. Key Assumptions Check (KAC)

List every assumption the headline conclusion rests on — data assumptions ("`churned`
means voluntary churn"), method assumptions ("monthly grain is fine"), and business
assumptions ("channel mix is controllable"). Label each:

- `[CONFIRMED]` — verified in the data or by the user
- `[LIKELY]` — reasonable, not verified
- `[UNSURE]` — could be wrong and would change the conclusion

A KAC with no fragile assumptions didn't dig hard enough — do it again. Every `[UNSURE]`
assumption under a headline finding becomes a caveat in the report; if the conclusion
flips when an `[UNSURE]` assumption flips, say so explicitly.

## 2. Competing explanations (ACH-lite)

For the headline finding, build a small hypothesis-vs-evidence table with at least these
rivals — they cover the ways metrics lie:

| Rival | The trap it catches |
|-------|---------------------|
| Real effect | (what you're claiming) |
| Mix shift | Composition changed, not behavior — new cohort/channel/segment diluted the aggregate |
| Seasonality / external | Same period last year did the same thing |
| Data artifact | Tracking outage, duplicates, definition change, timezone, backfill |

Score each rival against each piece of evidence: Consistent / Inconsistent / Neutral.
The winner is the hypothesis with the *least inconsistent* evidence — disconfirmation,
not accumulation of support. If two rivals survive, the report presents both with the
evidence that would separate them.

## 3. Triangulation — four checks, in order

1. **Segment-first (Simpson's paradox).** Does the aggregate finding hold within each
   major segment? If the aggregate moves one way and every segment moves the other,
   the story is mix, not behavior — and the correct headline changes completely.
2. **Internal consistency.** Percentages sum to ~100%; segment totals equal the
   aggregate; funnel steps decrease monotonically; rates stay in [0,1]; the denominator
   was stable over the comparison window (if it wasn't, rates are not comparable).
   Also: survivorship check — did any filter silently drop part of the population?
3. **Cross-reference.** Recompute the headline number through a genuinely independent
   path: a second table that should agree (orders vs payments), or SQL where the
   original was pandas. Agreement within 0.1% or explain the gap.
4. **Plausibility.** Order-of-magnitude sanity against known benchmarks (monthly churn
   3-8% for subscriptions, e-commerce conversion 1-4%, etc.). A number outside the
   plausible range isn't necessarily wrong — but it needs a named reason.

## 4. Devil's advocacy

Write one honest paragraph attacking your own conclusion — the strongest case that it's
wrong, not a strawman. The typical failure is conceding too easily; hold the role. If
the attack finds a real crack, return to Phase 3. If it doesn't, the paragraph (or its
conclusion) goes in the report as "what would change this conclusion".

## 5. Mechanical tie-out — findings.json + validate_findings.py

Register every headline claim in `findings.json`:

```json
{
  "dataset": {"files": {"subs": "data/subscriptions.csv"}},
  "claims": [
    {
      "id": "F3",
      "claim": "Partner-channel monthly churn averaged 8.1% in 2026-Q2",
      "value": 0.081,
      "tolerance_pct": 0.5,
      "recompute": {
        "file": "subs",
        "pandas": "df[(df.month>='2026-04')&(df.channel=='partner')].churned.mean()",
        "sql": "SELECT AVG(churned) FROM subs WHERE month>='2026-04' AND channel='partner'"
      }
    }
  ]
}
```

Then run `validate_findings.py findings.json`. It executes the pandas expression and the
SQL through DuckDB — two independent code paths — and compares both against your claimed
value. Security note: findings.json is executable code (the expressions run via eval);
only validate files authored in your own analysis session — never a findings.json from
an untrusted source. Output severities:

- **PASS** — both paths ran and agree with each other and with the claim (within
  tolerance)
- **WARNING** — only one path could run (no SQL given, duckdb missing) but it agrees
  with the claim
- **BLOCKER** — the recomputed value contradicts the claim, the two paths contradict
  each other, or a recompute failed to execute. A number in the report is not
  trustworthy: fix the claim or the analysis before Phase 5.

## 6. Guardrail check (feeds Phase 5)

Pair the headline metric with the metric it could silently degrade (conversion ↔ AOV,
ticket deflection ↔ CSAT, churn ↔ acquisition cost), computed over the same period and
in the same units. Verdict: **CLEAR** (guardrail flat or improving), **TRADE-OFF**
(<10% relative degradation — report the net), **DEGRADED** (>10% — the "win" headline is
not allowed; report both sides and the net impact).

## Closing the phase

The report's validation section states, in two or three sentences: which checks ran,
what changed as a result (a finding demoted, a caveat added, a number corrected), and
what information would resolve the remaining uncertainty. If validation changed nothing
at all, say so — and treat it as a yellow flag that the pass may have been ritual.
