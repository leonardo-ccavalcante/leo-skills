---
name: financial-analysis
description: >
  Interactive financial analysis with strict calculation discipline — all math runs
  in bundled Python scripts, all reasoning and interpretation happens in conversation
  with the user. Four domains: (1) business/startup viability — unit economics, CAC/LTV,
  pricing, multi-year P&L and cash projections, break-even, runway, scenarios;
  (2) existing-company analysis from financial statements — profitability, liquidity,
  solvency and efficiency ratios, margins, DuPont, benchmarking; (3) SaaS and
  recurring-revenue metrics — ARR, MRR, churn, NRR, GRR, cohorts, magic number, burn
  multiple, Rule of 40; (4) operational finance — cost per ticket, cost per project,
  cost-to-serve, capacity sizing, headcount planning, initiative ROI and business
  cases, budget vs actual variance. Use this skill whenever the user asks to analyze
  a business idea, asks "is this viable", mentions unit economics, runway, burn,
  pricing, break-even, SaaS health, churn or retention, ratio analysis, cost per
  ticket, cost-to-serve, capacity or headcount sizing, a business case or ROI of an
  initiative, or budget variance — even if they never say "financial analysis".
  Accepts numbers stated in conversation or CSV/Excel exports.
---

# Financial Analysis

## Core principle

**All calculations happen in Python. All reasoning happens in conversation.**

Never state a number you did not read from script output — not a ratio, not a
percentage, not a "roughly 3x", not mental arithmetic on two numbers the user just
gave you. Derived numbers stated from memory are the single biggest failure mode of
LLM financial analysis: they look plausible, they are frequently wrong, and the
reader cannot tell the difference. The scripts in `scripts/` exist so that every
figure in your output is reproducible arithmetic.

Your job is the part Python cannot do: framing the decision, choosing the right
analysis, sourcing and challenging inputs, interpreting outputs against benchmarks,
and writing a report someone can act on.

Run everything through the dispatcher:

```bash
~/.claude/skills/financial-analysis/scripts/fa.sh <command> --json ...
```

Preflight on first use in a session: `fa.sh selftest` (golden-number tests) and, if
the user brings files, `fa.sh doctor` (checks pandas/openpyxl).

## Step 0 — Memory

Read `MEMORY.md` (in this skill's folder) before starting any analysis. It holds
calibration lessons, the user's preferences, recurring analyses, and process fixes
from past sessions. Apply what's relevant; it exists so the same mistake is never
made twice.

Then write a session marker so the end-of-session retrospective can find this
analysis: create `.fa-session` in the current working directory containing one line —
the analysis name and date. Delete it when the retrospective (Step 7) completes.

## Domain router

| The user is asking about... | Domain | Read | Primary scripts |
|---|---|---|---|
| An idea or startup: "is this viable", pricing, projections, runway, break-even | Viability | `references/viability.md` | `unit-economics`, `projection`, `scenarios` |
| A real company's statements: ratios, margins, financial health, DuPont | Company analysis | `references/company-analysis.md` | `ratios`, `scenarios` |
| ARR/MRR, churn, NRR, cohorts, SaaS health check | SaaS metrics | `references/saas-metrics.md` | `saas`, `unit-economics`, `scenarios` |
| Cost per ticket/project, cost-to-serve, capacity, headcount, business case, budget variance | Operational finance | `references/operational-finance.md` | `ops`, `scenarios` |

Rules:
- Read only the active domain's reference (progressive disclosure). Analyses that
  span domains read both — a SaaS viability check uses `viability.md` and
  `saas-metrics.md`.
- When the domain is ambiguous, ask one question to disambiguate rather than guessing.
- File inputs of any kind: read `references/input-formats.md` before loading, and
  agree the column mapping with the user — never guess what a column means.

## Universal workflow

Every analysis follows seven steps. Depth scales with the ask — a quick sanity check
compresses steps, a full viability study runs all of them — but no step is skipped
silently.

### 1. Frame

Restate the decision this analysis serves ("should you launch this", "is churn the
problem", "is the team sized right", "approve this initiative or not"). Check the
domain reference's **When NOT to use** block before proceeding — running the wrong
framework confidently is worse than asking. If the analysis involves payroll, taxes,
or jurisdiction-specific costs, ask which country applies and follow the
localization step in the domain reference (research components on the web, tag each
one with its source — never assume a country's cost structure).

### 2. Gather inputs, tagged

Request inputs as **one grouped list** (must-have vs nice-to-have), tolerant of
partial answers. Then tag every number:

- `user` — supplied by the user or their data
- `public` — supported by a source (record the URL)
- `assumption` — a visible working hypothesis, with its basis stated
- `unknown` — missing and not safely estimable (value stays null)

A plausible guess is still an `assumption`. Show the user the tagged input table
**before** computing, so they can correct tags and values while it's cheap. For
multi-input analyses, save the tagged inputs as `<analysis-name>.fa.json` in the
working directory (validate with `fa.sh validate <file>`) — this makes the analysis
resumable and auditable.

### 3. Compute

Build the input JSON and run the script with `--json`. Read the envelope:

- `results` — every value carries its formula and the inputs used
- `not_computed` — what couldn't be computed and why (guards, not failures)
- `missing` — what's absent, ranked by priority: **this is your question agenda**
- `status` — `INSUFFICIENT_DATA` means no verdict exists yet; relay that honestly
  ("Cannot compute LTV — churn rate is unknown") instead of routing around it

Then ask for the single highest-priority missing input (one question), or propose a
labeled assumption the user can override, and recompute. Loop until the marginal
input stops changing the verdict.

### 4. Benchmark and interpret

Compare script outputs against the benchmark tables in the domain reference.
Verdicts use the closed vocabulary **CRITICAL / WATCH / HEALTHY / EXCELLENT** —
nothing else. Benchmarks are conditioned on segment and stage: never apply an
Enterprise churn band to an SMB product, or a Scale-stage growth band to a pre-seed
idea. Benchmarks are dated snapshots — cite them as "benchmark as of <date>".

### 5. Stress-test

Run `fa.sh scenarios`:

- **Scenarios** — conservative / base / optimistic defined *only* as driver
  multipliers (base pinned at 1.0). Never accept or invent scenario outputs
  directly; scenarios change inputs, Python recomputes outputs.
- **Reversal thresholds** — for the 2-3 drivers the verdict depends on, solve for
  the value where the verdict flips (the churn rate where LTV:CAC crosses 3, the
  volume where the projection runs out of cash). Build the kill-assumptions table:

| Variable | Current (tag) | Reversal threshold | Impact chain | Data that would settle it |
|---|---|---|---|---|

Order it by which assumption is most likely to change the conclusion — do not
spread effort evenly.

### 6. Report

Use the fixed template below, with the domain reference's body sections. Lead with
Tier 1 metrics (existential: runway, unit-economics sign, retention floor). Never
lead with Tier 4 diagnostics when Tier 1 is off-track. At most **three** priority
issues — more paralyzes action.

### 7. Retrospective (reinforcement loop)

After the report is delivered (or when the user signals the session is done), run
the protocol in `references/retrospective.md`: an internal audit of accuracy,
reliability, and efficiency using `/sat` and `/problem-solving` (with built-in
fallbacks), writing durable lessons to `MEMORY.md`. Then delete the `.fa-session`
marker. This loop is how the skill improves; skipping it wastes the session's
learning.

## Evidence rules

1. **Tags survive synthesis.** Never upgrade an `assumption` or `unknown` into a
   fact during interpretation, no matter how confident the reasoning feels. If the
   verdict depends on an assumption, the report says so.
2. **Unknowns render as "Unknown"** — never blank, never zero, never a silently
   plugged average.
3. **Computed values are `calculation`** — traceable to a formula and inputs, and
   never presented as if they were sourced data.
4. **Prohibitions** (each of these has sunk real analyses):
   - Never invent CAC, churn, conversion rates, market size, or customer counts.
   - Never treat competitor pricing as willingness-to-pay evidence — it is an
     anchor, not proof.
   - Never infer private company metrics from traffic, GitHub stars, downloads, or
     follower counts.
   - Never present LTV as a valuation — it is a simplified operating metric.
   - Never let an optimistic scenario change outputs without changing drivers.
5. **INSUFFICIENT_DATA is a feature.** A refusal to compute, with the exact gaps
   listed, is a correct and useful result.
6. **Benchmarks need provenance**: `public` with a URL, or an explicit
   `assumption`. Industry numbers pulled from memory are assumptions and get
   tagged as such.

## Interaction rules

- **First message of an analysis**: one grouped input request. After that: **one
  focused question at a time**, ordered by the script's `missing[].priority`. Don't
  interrogate — when an input is non-critical, propose a labeled assumption with a
  benchmark anchor and let the user override with a one-line confirm.
- **Max 3 priority issues** per report, ordered by impact.
- **Metric tiering**: Tier 1 existential (runway, contribution sign, retention
  floor) → Tier 2 growth quality (NRR, growth rate, gross margin) → Tier 3
  efficiency (CAC payback, magic number, burn multiple) → Tier 4 diagnostic
  (cohort curvature, mix shifts). Reports lead at the highest tier that's off-track.
- **Variance escalation ladder** for narrating any delta: <5% one clause · 5-10%
  one line · >10% a paragraph with a cause hypothesis · >20% top of the report.
  A variance explanation is itself an `assumption` until confirmed.
- **Pre-committed decision triggers**: close significant analyses with standing
  rules in the form "at <threshold> of <metric>, do <action>", where thresholds
  come from the reversal solver, not intuition. Deciding triggers now beats
  deciding in a crisis.
- **Reversibility bar**: recommendations that are hard to reverse (hiring, pricing
  changes, signed commitments) require `user`/`public` evidence on their load-bearing
  inputs; reversible experiments may run on labeled assumptions.

## Running the scripts

```bash
FA=~/.claude/skills/financial-analysis/scripts/fa.sh

$FA unit-economics --inputs '{"arpa": {"value": 99, "status": "user"},
  "gross_margin_pct": {"value": 0.8, "status": "assumption", "basis": "SaaS typical"},
  "monthly_churn_rate": {"value": null, "status": "unknown"}}' --json

$FA saas --inputs-file acme.fa.json --json          # point metrics
$FA saas --mrr-file mrr_movements.csv --json        # ARR bridge
$FA projection --drivers-file drivers.json --json   # 36-month P&L + cash
$FA ratios --inputs-file fy25.fa.json --prior-inputs-file fy24.fa.json --json
$FA scenarios --model projection --drivers-file drivers.json \
  --reversal monthly_churn_rate --metric ltv_cac_ratio --threshold 3 --json
$FA ops unit-cost --inputs-file pool.fa.json --json
$FA ops variance --file budget_vs_actual.csv --json
$FA validate acme.fa.json
$FA selftest
```

- **Inline JSON** for conversation-stated numbers; **files** for exports (specs in
  `references/input-formats.md`). Always pass explicit tags — bare scalars are
  auto-tagged `user` with a warning.
- **Echo discipline**: paste result values verbatim from script output. If a
  follow-up needs any new derived number — even "what's that per month" — rerun the
  script. No exceptions; this is the rule that keeps the whole system honest.
- **Guards**: scripts return `not_computed` with a reason instead of Infinity or
  defaults. Relay the reason — it is usually the most informative sentence in the
  analysis.
- Exit codes: 0 OK/PARTIAL · 2 INSUFFICIENT_DATA · 3 validation failure · 1 bug
  (report it, don't work around it).

## Report structure

ALWAYS use this skeleton (domain references add body sections):

```markdown
# [Analysis title] — [date]

## Verdict
[1-3 sentences. Closed vocabulary. Tier 1 first. If the verdict rests on an
assumption, name it here.]

## Key numbers
| Metric | Value | Tag | Benchmark band (as of <date>) | Verdict |

## Top issues (max 3)
### 1. [Issue]
What is happening · Why it matters · What to do about it

## Kill assumptions
| Variable | Current (tag) | Reversal threshold | Impact chain | Data needed |

## Decision triggers
- At <threshold> of <metric> → <action>

## Inputs & assumptions
[Full tagged table. Unknowns shown as "Unknown".]

## Method note
[Which scripts ran, with which input files/JSON. Benchmark sources and dates.]
```

## Reference index

- `references/viability.md` — business/startup viability: the projection driver
  model, unit economics, country localization of payroll/taxes, benchmarks.
- `references/company-analysis.md` — statement ratios, DuPont, trend analysis.
- `references/saas-metrics.md` — SaaS formulas, segment/stage benchmark tables,
  the health-check loop.
- `references/operational-finance.md` — cost pools, unit costs, cost-to-serve,
  capacity/headcount, initiative ROI, budget variance.
- `references/input-formats.md` — tagged JSON schema and every CSV/Excel spec.
  Read before loading any file.
- `references/retrospective.md` — the end-of-session reinforcement loop. Read at
  Step 7, every session.
