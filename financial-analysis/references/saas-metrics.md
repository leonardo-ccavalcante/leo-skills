# SaaS & Recurring Revenue — Domain Reference

Read this when the user asks about ARR/MRR, churn, retention, NRR, cohorts, or a
"SaaS health check". All numbers come from `fa.sh saas` (and `fa.sh scenarios` for
stress-tests); this file carries the thinking around those numbers.

## Contents

1. [When NOT to use](#when-not-to-use)
2. [The 5-step health-check loop](#the-5-step-health-check-loop)
3. [Formula definitions (as the script computes them)](#formula-definitions)
4. [Benchmark tables](#benchmark-tables)
5. [Metric tiering](#metric-tiering)
6. [Mode 2 — ARR bridge](#mode-2--arr-bridge-from---mrr-file)
7. [Mode 3 — cohort retention triangle](#mode-3--cohort-triangle-from---cohort-file)
8. [Worked reversal example](#worked-reversal-example)
9. [Report body sections](#report-body-sections)

## When NOT to use

Frameworks fail more often from misapplication than miscalculation. Decline or
reframe when:

- **Rule of 40 below ~$1M ARR.** At small scale, growth percentages are dominated
  by base effects (going $8k→$16k MRR is "100% growth") and the metric rewards
  noise. Use MoM growth against the Early-stage band instead.
- **NRR conclusions on <12 months of data.** NRR mixes expansion timing and
  contract anniversaries; a 3-month window catches renewals unevenly and can swing
  20 points on timing alone. Report the monthly figure, but refuse trend verdicts.
- **Blended CAC across wildly different channels.** A blended CAC that averages
  $50 PLG signups with $30k enterprise sales describes nobody. Ask for per-channel
  spend and customer counts and run the metric per channel.
- **Cohort conclusions from cohorts <3 months old.** Young cohorts haven't hit
  their first churn cliff yet; their retention looks flattering by construction.
  Include them in the triangle, exclude them from the verdict.
- **Annualized monthly growth without its caveat.** `(1+m)^12 - 1` assumes twelve
  identical months — the script emits a warning on `rule_of_40` for exactly this
  reason. Always relay that warning; prefer actual YoY growth when the user has it.

## The 5-step health-check loop

**1. Collect** — one grouped request (SKILL.md interaction rules). Must-have:
`mrr_now`, `mrr_prior`, `churned_mrr`, `cash_balance`, `net_burn_monthly`.
Nice-to-have: `expansion_mrr`, `contraction_mrr`, `new_mrr`, `customers_total`,
`customers_start`, `customers_churned`, `customers_new`, `net_new_arr_quarter`,
`sm_spend_prior_quarter`, `gross_margin_pct`, `net_profit_margin_pct`. Be tolerant
of partial answers — the script degrades gracefully and its `missing[]` list
becomes your question agenda. Also ask **segment** (Enterprise / Mid-Market /
SMB-PLG / Consumer) and **stage** (ARR band) up front: without them, step 3 has no
valid benchmark row.

**2. Compute** — mode 1 point metrics:

```bash
FA=~/.claude/skills/financial-analysis/scripts/fa.sh
$FA saas --inputs '{
  "mrr_now":        {"value": 84000, "status": "user"},
  "mrr_prior":      {"value": 80000, "status": "user"},
  "churned_mrr":    {"value": 2400,  "status": "user"},
  "expansion_mrr":  {"value": 1800,  "status": "user"},
  "contraction_mrr":{"value": 400,   "status": "user"},
  "new_mrr":        {"value": 5000,  "status": "user"},
  "customers_total": {"value": 420,  "status": "user"},
  "customers_start": {"value": 410,  "status": "user"},
  "customers_churned": {"value": 12, "status": "user"},
  "gross_margin_pct": {"value": 78, "status": "assumption", "basis": "SaaS typical; confirm from P&L"},
  "cash_balance":    {"value": 900000, "status": "user"},
  "net_burn_monthly":{"value": 65000,  "status": "user"},
  "sm_spend_prior_quarter": {"value": null, "status": "unknown"}
}' --json
```

Notes the code enforces: `mrr_start` defaults to `mrr_prior` only for a
single-month window (`months_between` omitted or 1) — a warning says so; over
longer windows supply `mrr_start` explicitly or churn/NRR are skipped. Growth is
`mom_growth_pct` when `months_between` is 1, `cmgr_pct` (compound monthly rate)
otherwise. Without `expansion_mrr`/`contraction_mrr` you get `nrr_est_pct`
(churn-only, always ≤100) instead of `nrr_pct` — never present the estimate as
full NRR; the whole point of NRR is the expansion the estimate omits.

**3. Benchmark** — use the tables below, conditioned on BOTH segment and stage.
Never apply an Enterprise churn band to an SMB product: 3% monthly logo churn is
an emergency at $50k ACV and unremarkable in PLG. If segment or stage is unclear,
ask — one question beats a wrong verdict.

**4. Prioritize** — at most 3 issues, ordered by tier (see Metric tiering). A
runway problem outranks a magic-number problem regardless of how dramatic the
latter looks.

**5. Report** — SKILL.md skeleton plus the body sections at the end of this file.

## Formula definitions

These restate what `saas_metrics.py` computes, so you can explain any result key.
The script's formula strings are authoritative; never recompute any of these
mentally.

- **ARR bridge identity** (mode 2, per month):
  `ending_mrr = starting_mrr + new + expansion − churned − contraction`. Every
  MRR movement is one of those four buckets; if the reported ending disagrees,
  something unmodeled happened (see mode 2).
- **NRR** (`nrr_pct`) = `(mrr_start + expansion − churned − contraction) / mrr_start`.
  **GRR** (`grr_pct`) drops expansion: `(mrr_start − churned − contraction) / mrr_start`.
  GRR is the floor — it can never exceed 100% and shows what the book does with
  zero upsell. A company with 115% NRR and 75% GRR is filling a leaking bucket
  with expansion from a few accounts; the NRR headline hides concentration risk.
- **Logo vs revenue churn** — `logo_churn_monthly_pct` counts customers,
  `revenue_churn_monthly_pct` counts dollars. Divergence is diagnostic: logo ≫
  revenue churn means you're churning small customers (often fine, maybe even
  healthy pruning); revenue ≫ logo churn means large accounts are leaving — a
  Tier 1 alarm even when logo churn looks calm. The script prefers revenue churn
  for LTV and warns when it falls back to logo churn as a proxy.
- **LTV** = `arpa × gross_margin_fraction / monthly_churn_rate`. Guarded: zero
  churn → `not_computed` ("infinite lifetime"), not a huge number.
- **CAC** = `sm_spend_prior_quarter / customers_new` — the script warns to confirm
  `customers_new` counts the same quarter's acquisitions.
- **Magic number** = `net_new_arr_quarter / sm_spend_prior_quarter` (prior-quarter
  spend, because sales cycles lag).
- **Burn multiple** = `net_burn_monthly × 3 / net_new_arr_quarter` — cash burned
  per dollar of net-new ARR. Skipped when cash-flow positive.
- **Quick ratio** = `(new_mrr + expansion_mrr) / (churned_mrr + contraction_mrr)`.
  Undefined at zero losses — the script says so and notes it's a good sign.
- **Rule of 40** = annualized growth % + `net_profit_margin_pct`, where monthly
  growth is compounded `(1+m)^12 − 1`. The script warns this is aggressive;
  relay the warning and prefer real YoY growth when available.
- **Runway** = `cash_balance / net_burn_monthly` (months).

## Benchmark tables

All bands below are **as of 2026-08, directional** — sourced from OpenView,
Bessemer, SaaS Capital, and Paddle survey data (~2024-2025 vintage). They are
pulled from memory, so in any report they are `assumption`-tagged with this file
as basis; a `public` tag requires a fetched URL.

**Monthly logo churn, by segment** (verdicts: HEALTHY / WATCH / CRITICAL):

| Segment | HEALTHY | WATCH | CRITICAL |
|---|---|---|---|
| Enterprise (ACV > $25k) | <1% | 1-3% | >3% |
| Mid-Market ($5-25k) | <2% | 2-5% | >5% |
| SMB / PLG (<$5k) | <4% | 4-8% | >8% |
| Consumer | <5% | 5-10% | >10% |

**LTV:CAC — a two-sided band.** This is the one ratio where "more" stops being
better: past ~8, the company is likely harvesting instead of growing.

| LTV:CAC | Verdict |
|---|---|
| <1 | CRITICAL — losing money on every customer acquired |
| 1-2 | CRITICAL (poor — acquisition barely returns its cost) |
| 2-3 | WATCH |
| 3-5 | HEALTHY |
| 5-8 | EXCELLENT |
| >8 | WATCH — possibly under-investing in growth |

**CAC payback (months):** >24 CRITICAL · 18-24 WATCH · 12-18 HEALTHY ·
6-12 HEALTHY (good) · <6 EXCELLENT.

**NRR:** <80% CRITICAL · 80-90% CRITICAL (poor) · 90-100% WATCH · 100-110%
HEALTHY · 110-120% EXCELLENT · >120% EXCELLENT (world-class).

**Gross margin (SaaS):** <50% CRITICAL · 50-65% WATCH · 65-75% HEALTHY ·
75-85% EXCELLENT · >85% EXCELLENT (world-class). Context by business type:
software/SaaS 70-85% · marketplaces take-rate dependent · services 30-50% ·
hardware 20-40% — a "SaaS" with 45% gross margin is usually a services business
in disguise; say so.

**MoM MRR growth, by stage:**

| Stage (ARR) | CRITICAL | WATCH | HEALTHY | EXCELLENT |
|---|---|---|---|---|
| Early (<$1M) | <5% | 5-10% | 10-20% | >20% |
| Growth ($1-10M) | <3% | 3-7% | 7-15% | >15% |
| Scale ($10M+) | <1% | 1-3% | 3-7% | >7% |

**Composite/efficiency:** Rule of 40 ≥40 healthy (only meaningful above ~$1M
ARR) · burn multiple >2 problem, <1 excellent · quick ratio target >4 for
high-growth companies.

## Metric tiering

Order every report by the highest off-track tier — never lead with a Tier 4
diagnostic (an interesting cohort curve) when a Tier 1 metric (runway) is red,
because the reader will act on the first thing you show them.

- **Tier 1 — existential:** `runway_months`, `grr_pct` (the retention floor),
  contribution sign (is `arpa × gross margin` positive).
- **Tier 2 — growth quality:** `nrr_pct`, MoM growth, gross margin.
- **Tier 3 — efficiency:** `cac_payback_months`, `magic_number`, `burn_multiple`,
  `quick_ratio`.
- **Tier 4 — diagnostic:** cohort curvature, logo-vs-revenue churn divergence,
  segment mix.

**Runway decision-trigger ladder** (CFO practice — propose these as pre-committed
triggers whenever runway is a live issue): 12 months → review discretionary spend
and start the fundraise · 9 → hiring freeze · 6 → cut ~20% of burn if no term
sheet · 4 → deep cuts, all options on the table · 3 → emergency plan.

## Mode 2 — ARR bridge from --mrr-file

```bash
$FA saas --mrr-file mrr_movements.csv --json
```

CSV/Excel columns (spec also in `references/input-formats.md`): required
`month, new_mrr, expansion_mrr, contraction_mrr, churned_mrr`; optional `mrr_end`.
Anchoring rules the script enforces: the chain needs a base — pass
`--starting-mrr` or put `mrr_end` on the first row (the script backs the base out
of it). With neither, it refuses rather than guess an anchor every later month
would inherit. When a month's reported `mrr_end` disagrees with the computed
bridge, the reported figure wins (reality over model) and the untied residual is
warned — chase that warning: it means unmodeled MRR movement. Blank movement
cells become 0 with a warning; confirm blanks really mean zero. With ≥13 months
you also get `ltm_nrr_pct`/`ltm_grr_pct` — the trailing-12 figures that make NRR
verdicts legitimate (see When NOT to use). File modes are mutually exclusive with
each other and with `--inputs`.

## Mode 3 — cohort triangle from --cohort-file

```bash
$FA saas --cohort-file cohorts.csv --json
```

Columns: `cohort_month, months_since_start, customers` (an `mrr` column is
accepted but retention here is customer-based). Output: `cohort_triangle` (each
row a cohort, cells % of its month-0 count) plus `avg_retention_m1/m3/m6/m12_pct`
where data reaches that far.

How to READ a triangle: the shape matters more than any single cell. A curve that
**flattens** after the early drop is the strongest quantitative product-market-fit
signal — some set of users has durable need. The level **where it plateaus** is
the retention floor: long-run revenue is roughly `plateau % × cohort size × ARPA`,
so a curve flattening at 40% and one at 15% are different businesses even with
identical month-1 churn. A curve still sloping down at month 12 means no floor
found yet — LTV built on current churn is optimistic. Compare recent cohorts to
old ones down the diagonal: newer cohorts retaining better is product improvement;
worse is degrading acquisition quality or fit.

## Worked reversal example

"At what churned MRR does LTV:CAC fall through 3?" Churn rate is computed, not an
input, so the reversal driver is `churned_mrr` (with `mrr_start` fixed, rate and
dollars are proportional). Uses the same tagged inputs file as mode 1 — which must
include the CAC inputs (`sm_spend_prior_quarter`, `customers_new`) so `ltv_cac`
computes at base:

```bash
$FA scenarios --model saas --inputs-file acme.fa.json \
  --reversal churned_mrr --metric ltv_cac --threshold 3 --direction below --json
```

Read from the result: `base_ltv_cac` (current value), `reversal_value` (churned
MRR at the crossing, absolute value for flat models), `headroom_pct` (distance
from today). If the metric never crosses in the searched range, the script says
so — that non-crossing is itself a finding (or widen `--lo`/`--hi`). The
reversal value converts directly into a kill-assumptions row and a decision
trigger ("at $X churned MRR / Y% revenue churn → action"). The same pattern
solves growth ("at what mrr_now does rule_of_40 cross 40") or burn ("at what
net_burn_monthly does runway_months cross 6").

## Report body sections

Extend the SKILL.md skeleton, in this order:

1. **ARR bridge table** (when mode 2 ran) — paste the `arr_bridge` rows verbatim;
   bold the months whose bridge didn't tie.
2. **Metric dashboard** — every computed metric: value · tag · benchmark band
   (with segment/stage row named, "as of 2026-08, directional") · verdict from
   the closed vocabulary. List `not_computed` items with their script-given
   reasons — those reasons are findings, not apologies.
3. **Top issues (max 3)** — tier-ordered, each with what is happening · why it
   matters · what to do.
4. **Kill assumptions** — reversal-solver thresholds, ordered by likelihood of
   flipping the verdict.
5. **Decision triggers** — "at <threshold> of <metric> → <action>"; include the
   runway ladder whenever runway < 15 months.
