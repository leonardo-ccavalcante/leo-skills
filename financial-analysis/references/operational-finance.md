# Operational finance — support/CS/ops teams and PMOs

Domain 4: what work costs, how many people it takes, whether an initiative pays,
and where the budget went. Generic and first-principles — the same models fit a
support desk, a CS team, an ops back office, or a PMO; only the driver changes
(ticket, order, case, project). All six calculators live behind one dispatcher
entry: `fa.sh ops <subcommand>`. Every number in your output comes from their
JSON envelopes — never from head math on the user's figures.

## When NOT to use

- **Unit cost from a partial cost pool.** If the pool is "whatever numbers the
  user had handy", the unit cost is garbage with decimal places. Define the pool
  first (see the checklist below), tag every line, and only then divide. The
  script helps — it warns when the pool has no labor line and when it has no
  overhead allocation — but it cannot know what was silently left out.
- **Strict intra-day SLA staffing.** `ops capacity` and `ops headcount` are
  deterministic, average-based models — the script itself stamps every result
  with the warning "deterministic average-based model (Erlang-lite)". They answer
  "how many FTEs does this monthly workload need". They do NOT answer "how many
  agents must be seated at 10:00 to answer 80% of calls in 20 seconds" — arrival
  spikiness and queueing mean average-based sizing understaffs peaks. For
  interval-level SLA staffing, use a real Erlang C calculator and say so in the
  report.
- **Initiative ROI when benefits cannot be expressed as a cash/time series.**
  "Better morale", "strategic optionality", "brand" — if the benefit cannot be
  written as currency per month (even as a tagged assumption with a basis), NPV
  is theater. Present those cases qualitatively next to the quantified core;
  never launder soft benefits into a `monthly_benefit` number to make IRR exist.
- **Cross-domain asks.** Cost per acquired customer is CAC (viability domain);
  support cost as % of ARR feeds SaaS gross margin (saas-metrics domain). Route
  there; this domain is about the cost of operating, not selling.

## Cost pools and allocation

A fully-loaded pool for one team/period contains, at minimum:

1. **Direct labor including employer burden** — gross salaries plus employer
  taxes, benefits, pension. Burden is jurisdiction-specific: follow SKILL.md's
  localization step (ask the country, research the components, tag each).
2. **Tooling and licenses** — helpdesk/PPM software, telephony, seats.
3. **Management share** — the lead/manager time attributable to this team.
4. **Facilities/overhead allocation** — rent, IT, HR/finance support, allocated
  on a stated basis (headcount share, seat count, direct-cost share).

Every allocation choice is an `assumption` with its basis written down
("facilities allocated by headcount share, 12/80 heads"), because a different
defensible basis gives a different unit cost — the reader must be able to see
which choice produced the number. Name pool categories so the script's checks
fire correctly: it detects labor by the substrings "salar"/"labor"/"payroll" and
overhead by "overhead"/"alloc" in category names.

**Fully-loaded vs marginal — match the pool to the question.** "What does a
ticket really cost?" wants fully-loaded (it prices the activity for cost-to-serve
and pricing decisions). "Should we outsource / deflect this volume?" wants
marginal (only the costs that actually disappear at lower volume — overhead
mostly does not). The script's "no overhead allocation — marginal cost only"
warning is your cue to say explicitly which of the two the number is.

## Unit cost — `fa.sh ops unit-cost`

**Pool mode** (point-in-time): inputs `cost_pool` (category → amount map; each
amount may be a bare number or a full tagged dict), `driver_volume` (units the
pool served in the same period — must be > 0 or the script refuses), and
`driver_name` (string; omitted → warns and reports per "unit"). Results:
`pool_total`, `pool_breakdown` (per-category amount and `pct_of_pool`, sorted
descending — read it aloud: the top line is where cost reduction lives), and
`unit_cost`. Period discipline: pool and volume must cover the same window, or
the division is fiction.

```bash
FA=~/.claude/skills/financial-analysis/scripts/fa.sh
$FA ops unit-cost --json --inputs '{
  "driver_name": {"value": "ticket", "status": "user"},
  "driver_volume": {"value": 4800, "status": "user"},
  "cost_pool": {"value": {
    "salaries_and_burden": {"value": 68000, "status": "user"},
    "helpdesk_licenses":   {"value": 4200,  "status": "user"},
    "management_share":    {"value": 9000,  "status": "assumption",
                            "basis": "25% of one lead, per org chart"},
    "overhead_allocation": {"value": 7500,  "status": "assumption",
                            "basis": "facilities by headcount share 12/80"}
  }, "status": "user"}}'
```

**PMO variant**: pool = PM labor (loaded) + PPM tooling + governance overhead
(steering-committee time, reporting); driver = active projects or, better,
project-months (a 6-month project is not one unit of work). State which driver
was chosen — it is an allocation assumption like any other.

**Trend mode** (monthly): `--costs-file` (columns `month,cost_category,amount`)
plus optional `--volume-file` (`month,volume`; requires the costs file).
Results: `unit_cost_trend` table (monthly `pool_total`, `volume`, `unit_cost`,
`mom_change_pct`), `avg_unit_cost`, and `trend_direction`
(rising/falling/flat, last vs first computed month, ±1% deadband). Interpret
direction with mix in mind: unit cost falls when volume rises against fixed
cost — that is scale, not efficiency. Say which one it is, as a hypothesis.

```bash
$FA ops unit-cost --costs-file support_costs.csv --volume-file tickets.csv --json
```

## Cost-to-serve by segment — `fa.sh ops cost-to-serve`

Input: `--file` with columns `segment,cost[,revenue]` (duplicate segment rows
are summed). Results: `cost_to_serve` table (`cost_share_pct`,
`cost_pct_of_revenue`, sorted by cost desc), `total_cost`, `top_segment`,
`top_segment_share_pct`. Without the revenue column the script still ranks cost
concentration but flags that revenue is what turns concentration into
profitability — push for it, because the decision-grade sentence is exactly
"segment X consumes 40% of support cost for 10% of revenue".

Verdict vocabulary applies per segment on cost-vs-revenue proportionality:
- **CRITICAL** — cost share is a large multiple of revenue share on a material
  segment, and no strategic justification is on record.
- **WATCH** — cost share meaningfully above revenue share; deliberate (e.g.
  white-glove onboarding cohort) or drifting? Find out before acting.
- **HEALTHY** — cost roughly tracks revenue across segments.
- **EXCELLENT** — highest-revenue segments are cheapest to serve per revenue
  dollar (self-serve working where it should).

How the segments were cut (plan tier, region, size band) and how shared cost
was attributed to them are allocation assumptions — restate them with the table.

## Capacity and headcount — `fa.sh ops capacity` / `ops headcount`

The formula chain, exactly as the script computes it:

```
workload_hours          = demand_volume_monthly * aht_minutes / 60
effective_hours_per_fte = hours_per_fte_month * (1 - shrinkage_pct) * occupancy_target
required_fte_raw        = workload_hours / effective_hours_per_fte
required_fte_buffered   = required_fte_raw * (1 + service_buffer_pct)
```

Input rules the script enforces: `shrinkage_pct` in [0, 1), `occupancy_target`
in (0, 1], `service_buffer_pct` ≥ 0 (defaults to 0). `hours_per_fte_month`
omitted → the script injects 160 as a tagged assumption and warns — confirm or
override it, since contracted hours vary by country.

**Shrinkage checklist** — paid hours that produce no ticket work: PTO/sick,
public holidays, training, team meetings/1:1s, admin/system time. Commonly
25-35% for support/ops teams (directional practitioner range, as of 2026-08 —
an assumption to tag until measured from this team's own calendar/WFM data).
Skipping shrinkage overstates capacity ~40% and produces a plan that "fits" on
paper while the team drowns.

**Occupancy rationale** — the sustainable fraction of available time spent on
handling work. Target 75-85%; flag anything > 90% sustained as a burnout and
attrition risk in the report, not a win — queues need slack to absorb variance,
and people need recovery time between contacts. This is why the script demands
an explicit `occupancy_target` instead of assuming 100%.

`ops headcount` extends the same chain over a `--demand-file`
(`month,volume`), ceil-ing FTEs per month because you hire whole people, and
pricing the plan with `loaded_monthly_cost_per_fte` (fully-loaded — reuse the
pool logic above). Results: `headcount_plan` table, `peak_fte`, `avg_fte`,
`total_cost`. Read peak vs average: a big gap argues for flex capacity
(contractors, overtime, cross-training) rather than hiring to peak.

```bash
$FA ops headcount --demand-file demand_2026.csv --json --inputs '{
  "aht_minutes":     {"value": 14, "status": "user"},
  "shrinkage_pct":   {"value": 0.30, "status": "assumption",
                      "basis": "25-35% practitioner range; no WFM data yet"},
  "occupancy_target":{"value": 0.85, "status": "user"},
  "service_buffer_pct": {"value": 0.10, "status": "user"},
  "loaded_monthly_cost_per_fte": {"value": 7900, "status": "user"}}'
```

Both commands emit the Erlang-lite warning — carry it into the report verbatim
whenever the user's real question involves intra-day service levels.

## Initiative ROI — `fa.sh ops roi`

Frame every initiative as cashflows: `investment` (t=0 cash out, must be > 0),
then monthly net benefit = benefit − `monthly_cost` (running cost, defaults 0).
Benefits enter as `monthly_benefit` (+ `horizon_months`; omitted → 24 injected
as a tagged assumption) or an explicit `benefit_series` list when ramp-up
matters (deflection rarely lands at full value in month 1). If both are given,
the series wins and the script says so.

Tag discipline is the heart of this model: deflection rates, minutes-saved,
tickets-avoided are `assumption` until measured — the script itself warns
"benefits are assumptions until measured — attach measurement plan" when benefit
inputs carry that tag. Honor it: every business case includes a measurement plan
(the metric, the baseline, who reads it, when) so the assumption has an expiry
date instead of quietly becoming a fact.

Results: `total_net_benefit`, `npv` (needs `discount_rate_annual`, converted to
a monthly rate — the rate itself needs provenance: the company's hurdle rate is
`user`, a guessed 10% is an `assumption`), `irr_monthly` +
`irr_annualized_pct` (skipped with a reason when cashflows never change sign),
and `payback_months` (skipped when it never pays back within the horizon —
relay that sentence; it is the verdict).

Always run the conservative scenario before recommending: `fa.sh scenarios`
with benefit drivers haircut (e.g. 0.5×) and, for the load-bearing driver, a
reversal solve for where NPV crosses 0 — that threshold feeds the
kill-assumptions table. Close with post-launch decision triggers, e.g. "at
month 3, if measured deflection < N% (the reversal value) → stop/rescope".

```bash
$FA ops roi --json --inputs '{
  "investment":       {"value": 60000, "status": "user"},
  "monthly_benefit":  {"value": 5200, "status": "assumption",
                       "basis": "18% deflection est. * 4800 tickets * unit cost from pool run"},
  "monthly_cost":     {"value": 900, "status": "user"},
  "horizon_months":   {"value": 24, "status": "user"},
  "discount_rate_annual": {"value": 0.12, "status": "user"}}'
```

## Budget variance — `fa.sh ops variance`

Input: `--file` with `period,category,budget,actual[,type]`, type ∈
cost|revenue (missing/unknown → treated as cost, with a warning). The script
computes `variance_abs = actual − budget`, `variance_pct` against |budget|, and
classes each line by |variance_pct| — the narrative ladder, calibrated to
reporting effort so material lines get the words:

| Class | Band | Narrative owed |
|---|---|---|
| note | < 5% | one clause |
| line | 5-10% | one sentence |
| paragraph | 10-20% | a paragraph with a cause hypothesis |
| escalate | > 20% | top of the report (also: budget = 0 with actual ≠ 0) |

Favorability follows line type — underspend on a cost line is favorable
(`actual <= budget`), under-delivery on a revenue line is not
(`actual >= budget`); a naive sign read misreads half the lines, which is why
the `type` column exists. But interrogate favorable variances too: underspend
from unfilled headcount is deferred cost plus a service risk, not savings.
Distinguish in-month vs YTD when narrating — one bad month inside an on-track
YTD is timing; a growing YTD gap is trend. Results: `variance_table`,
`total_budget`, `total_actual`, `total_variance_pct`, `worst_line` (largest
unfavorable |variance_pct|, falling back to |variance_abs|) — start the
narrative there. Every variance explanation is an `assumption` until the line
owner confirms it; write "hypothesis:" in front of each cause.

## Benchmarks (as of 2026-08 — directional)

Practitioner ranges from contact-center/ITSM literature (MetricNet, HDI, ICMI
directional), not audited data. Anything quoted from this table without a
fresher `public` source is an `assumption` and gets tagged as one. Absolute cost
per ticket/project varies too much by country, channel, and complexity to
benchmark honestly — benchmark the *structure* instead:

| Metric | CRITICAL | WATCH | HEALTHY | EXCELLENT |
|---|---|---|---|---|
| Shrinkage | > 40% or unmeasured | 35-40% | 25-35% | measured, 25-30% |
| Occupancy (sustained) | > 90% (burnout) or < 60% | 85-90% | 75-85% | 75-85% with buffer |
| Labor share of fully-loaded pool | < 40% (pool likely missing lines) | 40-55% | 55-75% | 55-75%, all lines tagged |
| Initiative payback (ops tooling) | > horizon | 18-24 mo | 9-18 mo | < 9 mo on conservative case |

## Report bodies (extend SKILL.md's skeleton)

**Ops cost review** — after Key numbers: *Pool definition* (lines, tags,
allocation bases; fully-loaded or marginal, and which question that fits);
*Unit cost + trend* (level, direction, scale-vs-efficiency hypothesis);
*Cost-to-serve* (concentration table, per-segment verdicts, the
cost-share-vs-revenue-share sentence).

**Capacity plan** — *Demand and workload* (volume source, AHT provenance);
*Capacity chain* (the four formula lines with each input's tag; shrinkage and
occupancy called out); *Plan* (monthly FTE table, peak vs average, flex
strategy, loaded cost); *Limits* (the Erlang-lite caveat verbatim; when an
Erlang C pass is needed).

**One-page business case** — *The ask* (investment, what it buys, horizon);
*Return* (NPV, IRR, payback — base and conservative side by side); *Benefit
basis and measurement plan* (every benefit line's tag and how/when it gets
measured); *Kill assumptions* (reversal thresholds from the scenarios solver);
*Decision triggers* (pre-committed post-launch checkpoints).
