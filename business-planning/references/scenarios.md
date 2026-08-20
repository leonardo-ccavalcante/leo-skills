# Scenarios: the locked trio and the fa.sh handoff

The 3-scenario lock is adapted from Kappaemme-git/codex-startup-business-planner
(MIT, https://github.com/Kappaemme-git/codex-startup-business-planner, accessed
2026-08-19). Design rule: scenarios change inputs, never outputs. A scenario that
changes outcomes without changing drivers is unrepresentable on purpose; that is
what kills the hockey-stick-by-assertion failure mode.

## When NOT to use

- Scenario outcomes (revenue, cash, runway under each case) are never written
  here. `fa.sh` computes them. If someone narrates an outcome, this file's answer
  is "run the recipe".
- One-driver what-ifs and reversal solving go straight to `fa.sh scenarios`
  (sensitivity and reversal modes); no bp.sh step is needed.
- More than three scenarios, renamed scenarios, or a "stretch case" are not
  supported by design. `bp.sh scenarios` exits 3 on a missing or extra scenario.
- Narrative futures thinking (alternative futures, premortem) belongs to /sat.

## Input checklist

- A validated state file `bp_<slug>/<slug>.bp.json` containing the base drivers,
  each Tagged with status and basis.
- The 3 to 6 drivers the verdict depends on (selection guidance below).
- Multiplier sets for exactly `conservative`, `base`, `optimistic`. Every `base`
  multiplier is 1.0; the script rejects anything else (exit 3).
- fa.sh available: `bp.sh doctor` must report financial delegation available.
- `bp_<slug>/scenarios/` directory to save every emitted and computed file.

## Method

### The locked trio

Scenarios are driver multipliers, nothing more. `conservative` and `optimistic`
scale the base drivers; `base` is pinned at 1.0 everywhere and the script
enforces the pin. Multiplier values are assumptions: tag them, give each a basis
("conservative halves the conversion assumption because no funnel data exists"),
and never present one as researched without a source.

### Driver selection

Pick the 3 to 6 drivers the verdict actually depends on: the ones that appear in
the kill-assumptions table, carry `assumption` tags with wide uncertainty, or sit
upstream of the fatal metric (runway, break-even, LTV:CAC). Scaling a dozen
drivers hides which one matters. For fa.sh projection compatibility, name drivers
by the projection families `price`, `volume`, `unit_variable_cost`, `opex`,
`payroll`, or by a scalar top-level driver such as `tax_rate_pct`.

### The handoff recipe (exact)

```bash
# 1. Build the multiplier table and the fa.sh-ready driver objects.
bp.sh scenarios --inputs-file bp_<slug>/<slug>.bp.json --json \
  > bp_<slug>/scenarios/scenario-table.json

# 2. Save each entry of results.driver_files from that output to
#    bp_<slug>/scenarios/drivers-conservative.json
#    bp_<slug>/scenarios/drivers-base.json
#    bp_<slug>/scenarios/drivers-optimistic.json

# 3. Recompute outcomes with fa.sh, one projection per scenario.
for s in conservative base optimistic; do
  fa.sh projection --drivers-file "bp_<slug>/scenarios/drivers-$s.json" --json \
    > "bp_<slug>/scenarios/projection-$s.json"
done
```

`bp.sh scenarios` computes no outcomes; it echoes the assumption table (driver ×
scenario, tags included) and emits the three driver files. Outcomes exist only
after step 3. Horizon discipline: `fa.sh projection` runs 36 months by default,
so `ending_cash` and every reversal threshold describe month 36 unless you
checked the length of `results.monthly` — state the horizon next to every cash
figure, and label each reversal with its cash convention (real starting cash vs
the cash-0 self-financing convention). Outcome figures (`runway_months`,
`ending_cash`, `zero_cash_month`, `breakeven_month`) are quoted verbatim from
the saved projection JSONs, naming the file each one came from.

Input shape (two tagged inputs in the state file; the code is the authority):
`base_drivers` holds the raw projection driver object exactly as `fa.sh
projection` expects it (activities, opex_lines, payroll, starting_cash, and so
on); `multipliers` holds an object with exactly the keys `conservative`, `base`,
`optimistic`, each mapping a driver family (`price`, `volume`,
`unit_variable_cost`, `opex`, `payroll`) or a scalar top-level key (such as
`tax_rate_pct`) to a positive number. A scenario that omits a driver leaves it
at 1.0, and the assumption table shows the resolved 1.0 so the omission stays
visible.

### Kill-assumptions table and reversal thresholds

For each verdict-driving assumption, solve for the value where the verdict flips,
then record what evidence would settle it. Reversals run in fa.sh:

```bash
# Projection drivers: the answer is a MULTIPLIER on the driver (default search 0.05 to 5.0).
fa.sh scenarios --model projection --drivers-file bp_<slug>/scenarios/drivers-base.json \
  --reversal volume --metric ending_cash --threshold 0 --json \
  > bp_<slug>/scenarios/reversal-volume.json

# Flat models (unit-economics, saas, ops-*): the answer is an ABSOLUTE driver value.
fa.sh scenarios --model unit-economics --inputs-file bp_<slug>/<slug>.fa.json \
  --reversal monthly_churn_rate --metric ltv_cac_ratio --threshold 3 --json \
  > bp_<slug>/scenarios/reversal-churn.json
```

Table format (frozen columns):

| Variable | Current (tag) | Reversal threshold | Impact chain | Data that would settle it |
|---|---|---|---|---|
| monthly_churn_rate | <value> (assumption: <basis>) | <reversal_value from reversal-churn.json> | churn → LTV → LTV:CAC → verdict | 90 days of cohort retention |
| volume | <value> (assumption: <basis>) | <reversal_value, a multiplier, from reversal-volume.json> | volume → revenue → cash → runway | 4 weeks of real signup data |

Fill every cell from tagged inputs and saved reversal JSONs; the placeholders
above show shape, not values. When `fa.sh` reports that the metric never crosses
the threshold in the searched range, record that as the finding: the verdict does
not flip on this driver within plausible bounds.

### Precision and voice

Verbatim quoting and rounded prose are not in conflict (SKILL.md evidence rules
6 to 8): the tables carry the exact values, the sentences carry the meaning.

- Driver files and the kill-assumptions table keep exact driver names and full
  precision — they are machine inputs and must match what `fa.sh` expects.
- Around them, round to what the multipliers justify, state the band, and
  convert the multiplier into the driver's own value and direction: 0.68 on a
  base of 1,200 a month reads as "the plan breaks below about 820 a month",
  with the exact figure left in the table. Three-decimal outcomes off
  assumption-tagged multipliers advertise precision no multiplier has.
- `volume`, `ending_cash`, `zero_cash_month`, `not_computed` and file names stay
  in the tables and the method note; the argument speaks in units sold, months
  of cash, and the month the money runs out.

## Benchmarks-with-provenance

No multiplier benchmarks exist and none are given here. There is no researched
"correct" conservative haircut; each multiplier is an assumption tagged with its
basis. The base-pinned-at-1.0 invariant and the exact-trio rule are design
constants adapted from the codex donor (MIT, accessed 2026-08-19), enforced by
`bp.sh selftest` golden tests and by exit-3 behavior at runtime.

## Handoffs

- financial-analysis owns every outcome: `fa.sh projection` for the per-scenario
  P&L and cash, `fa.sh scenarios` for sensitivity sweeps and reversal solving.
  All calls use `--json`; all outputs are saved under `bp_<slug>/scenarios/`.
- `references/evaluate.md`: the readiness verdict the stress test challenges, and
  the evidence-audit protocol for the assumptions the table exposes.
- /sat: premortem and structured challenge once the mechanical stress test shows
  where the plan is soft.
- `references/full-plan.md`: scenario results land in the plan's risk and
  financials sections; kill-assumption evidence items feed the 90-day roadmap.
