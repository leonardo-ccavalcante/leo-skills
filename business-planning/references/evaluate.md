# EVALUATE route: readiness score, evidence audit, red-team lenses

Adapted in part from Kappaemme-git/codex-startup-business-planner (MIT,
https://github.com/Kappaemme-git/codex-startup-business-planner, accessed 2026-08-19)
and condensed from phuryn/pm-skills (MIT, https://github.com/phuryn/pm-skills,
accessed 2026-08-19). This file is the prose twin of `scripts/readiness.py`: it
explains the arithmetic, the script performs it. If the two ever disagree, the code wins.

## When NOT to use

- "Should this exist at all?" is upstream validation. Hand to /office-hours.
- "Is this plan ambitious enough?" is an ambition critique, not a soundness audit.
  Hand to /plan-ceo-review.
- Building a plan from scratch is the FULL-PLAN route (`references/full-plan.md`).
- A single artifact (canvas, pricing, sizing) is the MODULE route.
- Financial-statement health on its own (ratios, margins, DuPont) belongs to the
  financial-analysis skill directly (`fa.sh ratios`).
- Premortems, devil's advocacy, and deep adversarial challenge belong to /sat.
  This route runs light red-team lenses only (Method 7) and hands off the rest.

## Input checklist

Must have:
- The thing under audit: a plan document, a described business model, or an org
  structure. Read the existing `bp_<slug>/` state first if the project has one.
- Stage (`idea | validating | building | revenue`) and mode (declared or detected).
- For each of the 8 readiness dimensions: a `score_0_5`, an evidence level
  (`validated | researched | assumption_heavy | unsupported`), and the evidence
  itself in `basis`. Elicit these with the anchors in Method 3. A dimension with
  no evidence at all is `unknown`, not a low score.
- For any economics judgment: tagged inputs sufficient for `fa.sh unit-economics`
  or `fa.sh ratios`, or the honest admission that they are unknown.

Nice to have:
- `sources.md` or a URL list behind every public claim (the audit walks it).
- An org chart or role list when org structure is in scope.

## Method

### 1. The report: the finding leads, the score supports

Order the deliverable by argument, not by pipeline:

1. **The decisive finding** (the universal workflow's hunt step; method in
   `references/decisive-fact.md`) — the fact that most changes the reader's
   decision, in plain language, with its provenance, on the first screen. In an
   audit it is usually the metric the subject's own stated thesis depends on, or
   the disclosure that is missing and what the omission implies. An empty hunt
   opens the report at the same prominence: what you looked for, and the
   cheapest way to settle it.
2. **The verdict** — one line, then the two or three dimensions that produced it,
   each with the evidence that would move it.
3. **The dependency surface** — required, and the decisive finding never absorbs
   it. Name every dependency the verdict rests on, including the ones that
   finding does not touch. Checklist: customer, supplier and channel
   concentration · regulatory · labour and worker classification · key person ·
   platform or single-vendor dependency · litigation · liquidity and financing.
   One line each — the exposure and what would trip it, or "does not apply
   here", and why. A deep single finding over a thin risk surface loses to a
   plainer document that maps the whole surface: measured in blind judging.
4. **Support** — the score and `dimension_breakdown`, the corrected tagged table
   and downgrade log, the saved artifact list.

Support proves the finding; it is not the finding. A report that opens with the
score leads with its weakest sentence — the score compresses the evidence, and
the reader wants the evidence.

Precision, arithmetic, and voice (SKILL.md evidence rules 6 to 8):

- Artifacts keep full precision; prose rounds to what the weakest dimension
  justifies and states the band. The score is exact to one decimal because the
  arithmetic is, but its inputs are five-point judgments — write "mid-40s,
  FRAGILE, and it crosses a band if the pricing evidence holds", not a decimal
  dressed as a measurement.
- The reader rebuilds every headline number from the page: inputs and operation
  beside the result ("transaction 2,677 + ads 1,065 = revenue 3,742"), and for a
  reversal the driver's current value and the value at the flip with its
  direction, never a bare multiplier. Measured reason: in blind judging a
  reviewer rebuilt the rival document's whole financial spine live from its
  printed figures and could rebuild none of this skill's distinctive numbers,
  because they lived only inside artifacts nobody in the room can run. Saved
  artifacts are the backup of the proof, never the proof.
- Dimension identifiers (`unit_economics`), envelope fields (`missing`,
  `not_computed`), multiplier values and file names belong in the tables and the
  method note. The argument says "the per-customer economics", and names the tool
  once.

### 2. The readiness score (spec of `bp.sh readiness`)

Eight dimensions, weights totaling 100 (adapted from the codex donor, MIT):
`problem_evidence` 15 · `icp_specificity` 10 · `reachable_market` 10 ·
`positioning` 15 · `model_pricing` 15 · `gtm` 15 · `unit_economics` 10 ·
`execution` 10.

Input: one tagged entry per dimension in the `.bp.json` inputs, all 8 required for
a full score. The value holds the raw score and the evidence level:

```json
{"inputs": {"problem_evidence": {
  "value": {"score_0_5": 4, "evidence": "researched"},
  "status": "user", "basis": "20 interviews, 6 active workarounds"}}}
```

Arithmetic, performed only by the script:

- Dimension points = (score_0_5 / 5) × weight × evidence multiplier. Multipliers
  are engineering constants, golden-numbered in `selftest`: `validated 1.00 ·
  researched 0.75 · assumption_heavy 0.50 · unsupported 0.25`.
- `readiness_score` = sum of dimension points, computed in exact decimals and
  rounded half-up to one decimal before banding (a raw 69.95 bands as 70.0). No
  manual override exists.
- Verdict banding, read from the rounded score: `HEALTHY` at 70 and above,
  `FRAGILE` from 40 to 69, `UNSUSTAINABLE` below 40.
- Evidence floor: 3 or more dimensions unknown or absent, or every provided
  dimension carrying `unsupported`, gives `INSUFFICIENT_DATA` regardless of the
  arithmetic, exit 2, no numeric score. With 1 or 2 missing the score computes but
  is a lower bound and the script warns; a malformed value fails an invariant
  (exit 3) rather than banding a partial score.
- **The script applies weights and multipliers only. It has no cap.** Score
  ceilings are analyst-side discipline — Method 3.

Output: a `dimension_breakdown` table in `results`, plus `readiness_score` and
`verdict`; absent dimensions appear priority-ranked in `missing`. Run and save:

```bash
bp.sh readiness --inputs-file bp_<slug>/<slug>.bp.json --json > bp_<slug>/readiness.json
```

Quote scores and the verdict only from the saved file — and print the breakdown
so the reader can add it up: one row per dimension with score, weight,
multiplier and points, and a total row where the points column visibly sums to
the reported score. A score nobody can rebuild from the page is an assertion.

### 3. Eliciting dimension scores

The score is a claim about evidence, so each `score_0_5` must trace to evidence the
user actually stated. Three rules:

1. Ask for the evidence first, then propose the score the anchors imply. Never let
   the user (or yourself) pick a flattering number and backfill a rationale.
2. Elicitation ceilings, adapted from the codex donor's evidence caps: without
   direct demand or transaction evidence, `problem_evidence` and `model_pricing`
   do not exceed 3. Without a cited competitor or market source, `positioning`
   does not exceed 2. Without evidence the buyer is reachable in the proposed
   channel, `gtm` does not exceed 2. When CAC or churn is unknown,
   `unit_economics` does not exceed 2.
3. When the honest answer is "we have nothing on this", record the dimension as
   `unknown` rather than guessing a 1 with fabricated basis. The floor exists for
   exactly this case.

**The cap rule.** A ceiling is a judgment you make, not arithmetic the script
performs, so it leaves no trace unless you leave one. Two obligations, and
together they settle the contradiction graders caught in iteration 1 — a row
reading `unit_economics · validated · 1.00` next to a basis reading "CAC and churn
are not disclosed":

1. **Record the cap in `basis`**, as `capped at 2: CAC and churn are not
   disclosed`. That field is the only one that can carry it; otherwise the
   artifact shows a bare 2 and nobody, you included, can tell later whether it was
   measured or capped.
2. **A dimension capped for non-disclosure is never `validated`.** The evidence
   level qualifies the score, and the score claims something about the dimension
   itself — the economics, the positioning, the channel — not about the filing.
   When the thing itself is undisclosed, no measurement of it exists: use
   `researched` when you confirmed the absence in the primary source,
   `assumption_heavy` when the cap rests on inference from secondary coverage.

Cap and multiplier compound, and that is intended: a weak claim, weakly evidenced,
costs twice. Never compensate by raising the raw score. In the report the cap is
the sentence, not a footnote, because the cap is the reason for the score: "unit
economics scores 2 of 5 — the ceiling for a business that does not disclose CAC or
churn — and that 2 rests on confirming the omission in the filing, not on
measuring the economics. One cohort retention table would settle it."

Scoring anchors (what a 1, 3, and 5 look like):

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| `problem_evidence` | founder conviction only | problem visible in interviews or public complaints, nobody has paid | documented paid demand: transactions, pilots, users who switched and said why |
| `icp_specificity` | "everyone", or a demographic | named segment, user vs economic buyer distinguished | narrow segment plus buying trigger, qualification signals, anti-ICP, where they gather |
| `reachable_market` | one top-down industry number | bottom-up chain drafted, key steps still assumptions | `bp.sh market` chain, sourced account counts, each public step with URL and date |
| `positioning` | feature list, no alternative named | competitors and substitutes mapped, statement untested | a differentiated claim tested against buyers, including the do-nothing option |
| `model_pricing` | one guessed price | models compared, tiers hypothesized, competitor anchors cited | pricing backed by transaction or willingness-to-pay evidence |
| `gtm` | channel list, no reason or owner | one primary channel with funnel assumptions and stop conditions | the buyer demonstrably reached there: replies, meetings, conversions on record |
| `unit_economics` | no CAC, churn, or margin inputs | `fa.sh unit-economics` on labeled assumptions, output saved | the same run on the user's measured operating data |
| `execution` | no owners, no dates | 90-day roadmap with milestones, some owners | per-phase objective, metric, decision rule, owner, and past milestones hit |

Competitor pricing is an anchor, never proof of willingness to pay. A
`unit_economics` score above 1 requires a saved `fa.sh` artifact behind it.

Evidence-level assignment: `validated` means the user's own transactions or
measurements of that dimension, or two independent public sources reporting it;
`researched` one solid source not yet cross-checked; `assumption_heavy` labeled
assumptions with a reasoned basis; `unsupported` assertion without basis.

### 4. Verdicts and what each one obligates

The verdict comes from the script and is never overridden. If the user disputes
it, gather new evidence, change the inputs, rerun. Each verdict carries a
reporting obligation — all of it support, sitting under the decisive finding:

| Verdict | The report must contain |
|---|---|
| `HEALTHY` | the weakest dimension anyway, and the assumptions the score leans on |
| `FRAGILE` | the fragile dimensions by name (weighted contribution far below weight), each with the evidence that would repair it |
| `UNSUSTAINABLE` | the fatal economics by name, each traced to a saved `fa.sh` output (contribution at or below zero, LTV:CAC below 1, runway shorter than the validation plan). "The economics feel bad" is not a finding |
| `INSUFFICIENT_DATA` | the evidence agenda: the envelope's `missing` list in priority order, with the cheapest way to obtain each item. No score is reported |

### 5. Evidence-audit protocol

Walk the tagged table. This is the core of any EVALUATE engagement:

1. Assemble the table: `.bp.json` inputs plus every figure the artifact states.
   Run `bp.sh validate` first and fix the exit-3 findings.
2. Every `public` claim: open the `source_url`, confirm the figure appears there,
   record the access date and a tier (`gov_industry | analyst | press | blog`) in
   `sources.md`. A public claim without a URL is an assumption wearing a suit; the
   runtime downgrades it and the validator rejects it.
3. Market-level claims need two independent sources, or an explicit downgrade to
   `assumption` (rules in `references/research.md`).
4. Every `assumption`: challenge the basis. Would the verdict change if it were
   off by 2x? If yes, it belongs in the kill-assumptions table
   (`references/scenarios.md`).
5. Every `user` figure: confirm it is the user's own operating data, not their
   recollection of someone else's claim. Recollections get retagged.
6. Every `unknown`: confirm it is genuinely unavailable rather than unresearched.
   Researchable unknowns join the research queue (`references/research.md`).
7. **Series, not snapshot.** When a source publishes a metric across periods — and
   every public company does — read every period, not the latest. One period is a
   data point; the same metric flat across four periods, against a thesis that
   required it to move, is a finding, and usually *the* finding (Method 1). Track
   the metric the subject's own thesis depends on across the full disclosed
   history, and check whether a growth number is the market's or the company's. A
   latest-period figure quoted alone is an unfinished audit.
8. Orphan sweep: `bp.sh lint` catches currency and percent tokens in the artifact
   with no tagged source behind them.

The audit's output is a corrected tagged table plus a downgrade log (what moved
from public to assumption and why). Score dimensions only on the corrected table.

### 6. Org-structure evaluation

Structural questions only. No headcount ratios, spans of control, or org
benchmarks get invented here; payroll and capacity math go to `fa.sh ops` and the
report quotes the saved output.

- Capability coverage: list the model's key activities and name each owner.
  Activities with no owner are the finding.
- Stage fit: a revenue-stage model with nobody on retention is a gap; an
  idea-stage org with management layers is a different gap.
- Capacity signal: who owns the constraint the plan itself names, and what breaks
  first if volume doubles? Ask it; do not compute an answer.
- Single points of failure: which activities stop when one specific person is out.
- Decision rights: who can change price, scope, or hiring, and whether those are
  the people closest to the evidence.
- Hiring-stage fit: each planned role ties to a capability gap above and fires on
  an evidence trigger ("hire support when tickets pass what the founder can
  answer"), not a calendar date.

Findings feed the `execution` score and the report's risks.

### 7. Red-team lenses (compact)

Condensed from phuryn/pm-skills (MIT). Use at most one or two lenses per
engagement, chosen for the question. A lens finding must change a dimension
score, add a risk, or add a kill-assumption driver; one that changes nothing is
commentary and gets cut. Lens claims follow the same tagging rules.

| Lens | What you rate | Presses on | Reach for it when |
|---|---|---|---|
| Porter's five forces | rivalry, supplier power, buyer power, substitutes, new entrants — high/medium/low, each with its trend | `model_pricing` (rivalry, buyer power), `positioning` (low entry barriers) | the question is "can anyone make money in this market?" |
| PESTLE | political, economic, social, technological, legal, environmental — keep only high impact × likelihood | a risk with a monitoring indicator, or a kill-assumption driver when the factor moves a number | market entry, regulated categories, macro exposure; skip for a local niche |
| SWOT | internal strengths and weaknesses against external opportunities and threats; the value is in the crossings | `positioning`, `execution` | the plan reads well and nobody has asked what breaks it from the inside |
| Ansoff matrix | which quadrant the growth claim sits in: penetration, market development, product development, diversification | `execution`, `gtm` — diversification-grade growth on a penetration-grade budget is the finding | the growth story outruns the team and the money |

Premortem and deep challenge are not run here. Hand them to /sat.

## Benchmarks-with-provenance

This file carries no market benchmarks. The numeric constants in it are:

- Dimension weights, evidence multipliers, and verdict bands: engineering
  constants of this skill, adapted from Kappaemme-git/codex-startup-business-planner
  (MIT, accessed 2026-08-19) and golden-numbered in `bp.sh selftest`. They encode
  a scoring convention, not empirical market data.
- Elicitation ceilings in Method 3: framework heuristics from the same donor's
  evidence-cap design. They are discipline for the analyst, not measurements, and
  the script does not enforce them.

Economics thresholds (LTV:CAC, payback, margin bands) live in the
financial-analysis skill's references and arrive only through saved `fa.sh`
outputs. Any market figure quoted during an evaluation must carry a tag and, when
public, a URL with access date per `references/research.md`.

## Handoffs

- /sat: premortem, devil's advocacy, key-assumptions check, and any deep
  adversarial challenge the user wants. Do not reimplement those here.
- financial-analysis: every economics fact in the verdict. `fa.sh unit-economics`
  or `fa.sh ratios` with `--json`, outputs saved under `bp_<slug>/`, report quotes
  saved values only.
- `references/decisive-fact.md`: Step 4, before the report is ordered.
- `references/scenarios.md`: stress-testing the verdict and building the
  kill-assumptions table with reversal thresholds.
- `references/research.md`: before sourcing any public number during the audit.
- /plan-ceo-review: when the user's real question turns out to be ambition and
  scope rather than soundness.
- `references/full-plan.md`: when the audit concludes the plan needs a rebuild,
  not a patch.
- End of engagement: `bp.sh lint bp_<slug>/` must pass, then
  `bp.sh retro-score bp_<slug>/` and the protocol in `references/retrospective.md`.
