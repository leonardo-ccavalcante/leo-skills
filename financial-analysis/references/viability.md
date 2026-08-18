# Domain 1 — Business / Startup Viability

Answers one decision: **should this business be started, continued, or changed** —
via unit economics (does one customer make money?), a monthly P&L + cash projection
(does the whole thing survive?), and stress tests (what kills it first?).

## When NOT to use

- **DCF or valuation for a pre-revenue idea.** A discount rate applied to invented
  cash flows produces precision theater, not a valuation. Viability answers "does
  the machine work", never "what is it worth".
- **Top-down TAM as demand evidence.** "1% of a $10B market" is not a volume input —
  it smuggles the entire demand question into an unexamined multiplier. Volumes come
  bottoms-up: channel → conversion → customers, each step tagged. If no bottoms-up
  path exists, `volume_start` is an `assumption` and the report says the verdict
  rests on it.
- **Projections beyond 3 years for something not yet launched.** Compounding errors
  dominate signal past ~36 months pre-launch; the default horizon exists for a
  reason. Longer horizons are for businesses with operating history.
- **Competitor pricing as willingness-to-pay.** It is an anchor for the `price`
  driver (tag it `public` with the URL), never proof anyone will pay it. Only user
  conversations, pre-orders, or actual sales upgrade price to evidence.

## Input checklist (request as ONE grouped list, then tag)

**Must-have** — without these the scripts return `INSUFFICIENT_DATA`, correctly:

| Ask the user for | Maps to (exact driver name) | Script |
|---|---|---|
| Price per unit/subscription | `activities[].price` | projection |
| Starting volume + monthly growth (bottoms-up) | `activities[].volume_start`, `activities[].volume_growth_pct_monthly` (percent: 10 = 10%) — or explicit `activities[].volumes` list | projection |
| Variable cost per unit | `activities[].unit_variable_cost` (missing → assumed 0, warned) | projection |
| Cash in the bank today | `starting_cash` (without it the whole cash track — runway, zero-cash month — is skipped) | projection |
| Fixed monthly costs, itemized | `opex_lines[]` (`monthly_amount`, `start_month`, `annual_growth_pct`) | projection |
| Team plan | `payroll[]` (`role`, `monthly_gross`, `count`, `start_month`, `employer_burden_pct`) | projection |
| Revenue per customer per month | `arpa` | unit-economics |
| Monthly churn (0-1 fraction: 3% = 0.03) | `monthly_churn_rate` | unit-economics |
| Sales+marketing spend and customers acquired, same period | `sm_spend`, `new_customers` | unit-economics |

**Nice-to-have** — propose labeled assumptions rather than interrogating:

| Input | Driver name | If absent |
|---|---|---|
| Gross margin (0-1 fraction) | `gross_margin_pct` | needed for LTV/payback; propose from the margin table below, tagged `assumption` |
| Corporate tax rate | `tax_rate_pct` | assumed 0 with a recorded gap — net income and cash **overstated**; see localization step |
| Payment lags | `dso_days`, `dpo_days` | assumed 0; cash shifts by round(days/30) months |
| One-off purchases, loans, funding rounds | `capex[]`, `loans[]`, `funding[]` | omitted = none |
| Horizon | `months` | default 36, capped 120 |
| Fixed costs (flat model) | `fixed_monthly_costs` | breakeven_customers not computed |

Unit conventions differ by design — relay them exactly: `gross_margin_pct` and
`monthly_churn_rate` are **0-1 fractions**; `volume_growth_pct_monthly` and
`annual_growth_pct` are **percents** (10 = 10%). The scripts warn on the common
mistakes but a silent 80x error is still possible with plausible-looking values.
Every scalar in the projection driver file may be tagged
`{"value": ..., "status": ..., "basis": ...}` — tag them, so provenance survives
into the envelope's echo.

## The model chain

1. **`fa.sh unit-economics`** — the economics core: does one customer make money?
   Computes `cac`, `contribution_per_customer_monthly`, `contribution_margin_ratio`,
   `ltv`, `ltv_cac_ratio`, `cac_payback_months`, `breakeven_customers`, and (on the
   per-unit path with `price` + `unit_variable_cost`) `breakeven_units` /
   `breakeven_revenue`. The gross-margin path and per-unit path are deliberately
   separate so you can always say which margin assumption a headline number rests on.
   If LTV:CAC is below ~1 here, the projection mostly tells you *when* the business
   dies, not *whether* — fix the unit before projecting the machine.
2. **`fa.sh projection`** — the P&L + cash cascade over the horizon: revenue →
   variable costs → gross margin → opex → payroll → EBITDA → depreciation → EBIT →
   interest → tax (on positive pre-tax only) → net income; plus `breakeven_month`,
   `ending_cash`, `min_cash`, `min_cash_month`, `zero_cash_month`, `runway_months`,
   and `monthly` / `annual_summary` tables.
3. **`fa.sh scenarios`** — stress: named scenarios, sensitivity sweeps, and reversal
   thresholds over either model. Nothing is a verdict until it survives this step.

**The two-track design, and why it matters.** The projection computes an accrual
P&L and a cash track **independently**, tied by invariants. Startups do not die of
negative net income — they die when `cash[m] < 0`. A business can be profitable on
paper and dead in practice because customers pay in 60 days (`dso_days`) while
payroll leaves the account monthly, or because capex hits cash at once while the P&L
spreads it over 36 months. Read the verdict off the cash track: `zero_cash_month`
and `min_cash` are Tier 1; `breakeven_month` (EBITDA-based) is the accrual echo.
`runway_months` = ending cash ÷ **trailing-6-month average net burn** — a smoothed
recent burn, deliberately not the first-month burn (too early) or a single last
month (too noisy). It is a guard-railed number: it is skipped when the trailing
window is cash-flow positive or cash is already gone, and the skip reason is the
finding — relay it verbatim.

## LOCALIZE PAYROLL & TAXES (mandatory when payroll or tax matters)

`projection.py` takes only two generic knobs — `employer_burden_pct` per payroll
line and a single `tax_rate_pct` — **by design**: employer costs and corporate tax
are country-specific, and a hardcoded default would silently be a country choice.
Both are 0-1 fractions (values > 1.5 / > 1 are read as percent and normalized, with
a warning). Procedure:

1. **Ask which country (and regime) applies.** Never assume one — not from
   currency, language, or prior sessions.
2. **Research on the web** (WebSearch) that country's employer burden components
   (social security, pension, mandatory insurance, 13th salary or equivalents) and
   corporate tax basics (headline rate, small-business or startup regimes).
3. **Build the percentages WITH the user**, component by component, summing to one
   `employer_burden_pct` and one `tax_rate_pct`. Show the component table before
   computing.
4. **Tag each component** `public` with its URL, or `assumption` with its basis.
   A burden built from a memory of "Brazil is roughly 70%" is an `assumption`
   until a source backs it.

Why this rigor: burden commonly ranges ~10% to ~80%+ across countries — on a
payroll-heavy plan that single driver can move break-even by a year.

## Benchmark anchors (as of 2026-08 — directional; OpenView / Bessemer / SaaS Capital / Paddle, ~2024-25 data. Any band cited from memory in a report is an `assumption` and gets tagged as such)

**LTV:CAC — two-sided, this matters:**

| LTV:CAC | Verdict |
|---|---|
| <1 | CRITICAL — losing money on every customer acquired |
| 1-2 | CRITICAL (poor — acquisition barely recovers itself) |
| 2-3 | WATCH |
| 3-5 | HEALTHY |
| 5-8 | EXCELLENT |
| >8 | WATCH — again: possibly under-investing in growth, not a triumph |

**CAC payback (`cac_payback_months`):** >24 CRITICAL · 18-24 WATCH · 12-18 HEALTHY
· 6-12 GOOD · <6 EXCELLENT. Payback is the more honest early-stage metric — it
needs no lifetime assumption.

**Gross margin by business type** (sanity-check any proposed `gross_margin_pct`):
Software/SaaS 70-85% · marketplaces take-rate dependent (benchmark on net revenue)
· services 30-50% · hardware 20-40%. SaaS bands: <50% CRITICAL · 50-65 WATCH ·
65-75 HEALTHY · 75-85 EXCELLENT · >85 world-class.

**Early-stage caveats.** With months of history, churn is noise (one lost logo out
of ten = 10% "churn") and LTV = contribution/churn extrapolates a lifetime from it —
the script's own warning says LTV excludes discounting, expansion, and cohort
variation; repeat that caveat in the report. Pre-launch, CAC from a small paid test
is a ceiling estimate, not steady-state. Lean on contribution sign, break-even
counts, and payback; treat LTV:CAC as directional until ~12 months of cohort data
exist. Churn/NRR/growth-stage bands live in `saas-metrics.md` — read it alongside
this file for any SaaS viability check.

## Scenario discipline

Scenarios are **driver multipliers only** — base pinned at 1.0 everywhere; the
script rejects anything else, because a scenario that changes outputs without
changing drivers is a hockey stick by assertion. For projection, multipliers target
the families `price`, `volume`, `unit_variable_cost`, `opex`, `payroll` (applied
across all matching lines) or any scalar top-level driver by name (e.g.
`tax_rate_pct`, `dso_days`). Keep conservative honest: worse volume AND worse
costs, not just a softer growth rate.

```bash
FA=~/.claude/skills/financial-analysis/scripts/fa.sh

# scenarios.json:
# {"base": {},
#  "conservative": {"volume": 0.7, "opex": 1.15, "payroll": 1.1},
#  "optimistic":   {"volume": 1.3, "price": 1.1}}
$FA scenarios --model projection --drivers-file idea-drivers.json \
  --scenarios-file scenarios.json --json
# -> table "scenario_comparison": one row per scenario, every metric recomputed

# Reversal: at what volume multiplier does cash go negative within the horizon?
$FA scenarios --model projection --drivers-file idea-drivers.json \
  --reversal volume --metric min_cash --threshold 0 --direction below --json
# -> base_min_cash, reversal_value (a MULTIPLIER for projection: 0.82 = "volume
#    18% below plan kills it"), headroom_pct — these feed kill-assumptions rows

# Reversal on the flat model solves an ABSOLUTE value instead:
$FA scenarios --model unit-economics \
  --inputs-file idea.fa.json \
  --reversal monthly_churn_rate --metric ltv_cac_ratio --threshold 3 --json
# -> reversal_value = the churn rate where LTV:CAC crosses 3
```

"Metric does not cross the threshold in [lo, hi]" is a finding, not a failure —
it means the verdict does not flip inside a plausible range. Report it as such.

Worked unit-economics run with realistic tagged inputs:

```bash
$FA unit-economics --inputs '{
  "arpa": {"value": 79, "status": "user"},
  "gross_margin_pct": {"value": 0.78, "status": "assumption",
                       "basis": "SaaS typical 70-85%, pending COGS detail"},
  "monthly_churn_rate": {"value": 0.04, "status": "assumption",
                         "basis": "SMB band midpoint; no cohort data yet"},
  "sm_spend": {"value": 6000, "status": "user"},
  "new_customers": {"value": 25, "status": "user"},
  "fixed_monthly_costs": {"value": 14000, "status": "user"}}' --json

$FA projection --drivers-file idea-drivers.json --json   # 36-month default
```

## Viability report body (extends SKILL.md's skeleton)

Between **Key numbers** and **Top issues**, add:

- **3-year summary** — the `annual_summary` table verbatim (revenue, gross margin,
  EBITDA, net income, ending cash per year), values pasted from script output.
- **Break-even and cash floor** — `breakeven_month`, `min_cash` @ `min_cash_month`,
  `zero_cash_month` (or "not within horizon"), `runway_months` — each with its tag
  trail. If `breakeven_month` was guarded out ("not reached within horizon"), that
  sentence leads.
- **Runway per scenario** — one row per scenario from `scenario_comparison`:
  runway_months, zero_cash_month, ending_cash. The conservative row is the
  planning number; the optimistic row is never the headline.
- **Kill assumptions** — reversal outputs, ordered by lowest `headroom_pct`
  (closest to flipping first), per SKILL.md's table format.
- **Decision triggers** — pair reversal-derived triggers with the standing runway
  ladder (standard CFO practice; adapt thresholds to the user's fundraising
  reality): 12mo runway → review discretionary spend + start fundraise · 9mo →
  hiring freeze · 6mo → cut ~20% of costs if no term sheet · 4mo → deep cuts, all
  options on the table · 3mo → emergency plan. Committing to the ladder now beats
  negotiating with yourself at month 4.

Method note must name: which scripts ran, the driver/input files used, the
localization sources (country, URLs), and this benchmark block's date.
