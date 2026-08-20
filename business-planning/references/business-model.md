# Business model: canvases, revenue streams, monetization, pricing

Serves the MODULE route (canvas, revenue streams, pricing) and the model sections
of FULL-PLAN. Everything here obeys the skill's evidence rules: every number is
tagged, nothing is computed in prose, and every financial metric comes from a
saved `fa.sh` artifact.

## When NOT to use

- The user is still asking whether the idea should exist at all. That is
  upstream validation: hand back to the office-hours skill and return once the
  answer is yes.
- The question is ICP, market sizing, interviews, or channel choice. Read
  `references/market-gtm.md` instead.
- The user wants LTV, CAC, payback, break-even, projections, or any other
  financial number. This file only defines when to call `fa.sh` and how to save
  the artifact; the computation itself never happens here.
- The user wants a critique of an existing plan's ambition or scope
  (plan-ceo-review) or an audit verdict on soundness (`references/evaluate.md`).
- The user wants slides. Produce the canvas or pricing artifact; deck rendering
  belongs to executive-deck-builder.

## Input checklist

Must have before drafting:

- Product or service description, and the stage (`idea | validating | building |
  revenue`) resolved in Step 1 of the route.
- Target segment. If no ICP exists yet, do `references/market-gtm.md` first;
  a canvas built on "everyone" fails the lint on its own vagueness.
- What the user already knows, tagged: current operations, existing revenue,
  competitive context. Bare claims get tagged `user`; researched claims need
  URL + access date per `references/research.md`.

Needed for the pricing section:

- Competitor pricing pages (official pages only, each captured as `public` with
  `source_url` + `source_date`).
- The user's own cost and usage data where it exists (`user` tag), or explicit
  `assumption` entries with a basis.

Needed for the viability gate (all tagged, saved into
`bp_<slug>/<slug>.bp.json`, validated with `bp.sh validate`):

- `arpa`, `gross_margin_pct` (or `price` + `unit_variable_cost`),
  `monthly_churn_rate`, `sm_spend`, `new_customers`, `fixed_monthly_costs`.
  Any of these may be `unknown`; the gate then reports what it could not
  compute instead of guessing.

## Method

### 1. Choose the canvas

Three lines, one decision:

- **Business Model Canvas**: established businesses, corporate strategy, and
  investor materials that must show how all operating pieces connect.
- **Lean Canvas**: idea or validating stage, speed over completeness; a
  hypothesis-testing sketch, not a strategy document.
- **Startup Canvas**: new products that need strategy and business model kept
  separate, with an explicit defensibility test.

When the user names a canvas, use it. Otherwise pick by the line above and say
why in one sentence. Canvas outputs use the layouts in
`assets/templates/canvases.md`.

### 2. Business Model Canvas: the 9-block guided flow

Work the blocks in this order (segments first, money last), one grouped
question round per side of the canvas rather than nine separate interrogations:

1. **Customer segments**: who exactly, and of what kind (mass, niche,
   segmented, multi-sided). Distinct needs or profitability justify a segment;
   demographics alone do not.
2. **Value propositions**: which problem is solved per segment, and whether the
   value is quantitative (price, speed) or qualitative (design, status).
3. **Customer relationships**: how customers are won and kept (personal,
   self-service, automated, community) and what each costs.
4. **Channels**: how customers learn, buy, receive, and get support; direct vs
   partner. Keep consistent with the GTM channel choice in
   `references/market-gtm.md` if one exists.
5. **Key activities**: what the business must actually do to deliver the value.
6. **Key resources**: the minimum viable set of physical, intellectual, human,
   and financial assets behind those activities.
7. **Key partners**: who supplies or performs what the business will not.
8. **Cost structure**: the few costs that matter, fixed vs variable, and
   whether the model is cost-driven or value-driven.
9. **Revenue streams**: how money arrives, classified with the taxonomy in
   section 5. Every stream named here needs its own driver set.

Close with three checks, in this order:

- **Alignment**: each block supports the others; a premium value proposition
  with a self-service-only relationship block is a finding, not a style choice.
- **Viability gate**: section 8 below. Runs through `fa.sh`, never in prose.
- **Assumptions**: list what the canvas asserts without evidence, each keeping
  its tag. They land in the deliverable's Assumptions & Limitations section,
  whose existence `bp.sh lint` checks.

Known limits of BMC, which is why the chooser exists: no vision, no
defensibility test, no explicit trade-offs, no metrics section, and thin
partners/resources blocks for early-stage products.

### 3. Lean Canvas (alternate)

Nine boxes, filled in riskiest-first order: problem (top three, with current
workarounds), customer segments (early adopters first), unique value
proposition, solution (top three features only), channels, revenue streams,
cost structure, key metrics (activation, retention, revenue, one north-star),
unfair advantage (what cannot be copied or bought).

Treat it as a hypothesis board: every box is a claim to test, and the output
should name the riskiest assumption and the cheapest experiment against it.
Lean Canvas mixes problem with segment and solution with value proposition;
when the user needs strategic separation, move to the Startup Canvas.

### 4. Startup Canvas (alternate)

Two parts, kept distinct. Strategy: vision; market segments defined by problems
and jobs-to-be-done, not demographics; relative cost position (low cost vs
unique value); value proposition per segment as "what before, how, what after,
alternatives"; trade-offs (what you will NOT do); key metrics (north star plus
one metric for this quarter); growth motion (product-led or sales-led) and
preferred channels; capabilities to acquire; and the Can't/Won't test: what
stops competitors from copying the integrated set of choices. Business model:
cost structure and revenue streams, same discipline as BMC blocks 8 and 9.

The Can't/Won't test is the section users skip and reviewers read first. An
answer of "we move fast" is an `assumption` tag, not defensibility.

### 5. Revenue-stream taxonomy

Classify every stream as exactly one of these. The discipline that matters:
**each stream gets its own driver set**, and no artifact may carry a single
blended "revenue" line covering two streams.

| Stream type | Who pays for what | Driver set (each driver tagged) |
|---|---|---|
| recurring | subscription for ongoing access | active subscribers, ARPA, monthly churn, expansion |
| transactional | one-time purchases | orders per period, average order value, repeat rate |
| usage | metered consumption | active accounts, units per account, price per unit |
| licensing | rights to use IP | licenses sold, fee per license, renewal rate |
| marketplace-take-rate | share of transactions between others | GMV (transactions x average value), take rate, active supply and demand |
| services | human time and expertise | billable engagements, rate, utilization, delivery capacity |

Hybrids are normal; model each stream separately and let `fa.sh` do the
summing. The driver sets above are what `bp.sh scenarios` multiplies and what
`fa.sh projection` consumes, so a stream without drivers is a stream the plan
cannot stress-test.

### 6. Monetization strategy

1. Generate three to five candidates from distinct rows of the taxonomy.
   Freemium and tiering are packaging decisions layered onto a stream type, not
   stream types themselves.
2. Evaluate every candidate against seven criteria (adapted from
   codex-startup-business-planner): value alignment, buyer and procurement fit,
   cost coverage, revenue quality, simplicity and predictability, market
   evidence, and reversibility of the first test.
3. Verdict per candidate: `PRIMARY`, `ALTERNATIVE`, `TEST`, or `REJECT`, with
   exactly one PRIMARY. The rationale cites tagged evidence or says
   `assumption` out loud.
4. Attach to each survivor the cheapest experiment that would produce
   willingness-to-pay evidence: founder-led sales conversations, a priced
   landing page, a paid pilot. "People said they liked it" is not that evidence.
5. Any unit-economics comparison between candidates runs through
   `fa.sh unit-economics` once per candidate, each with its own saved artifact.

### 7. Pricing strategy

1. **Value metric first.** Charge on the unit that grows with the customer's
   delivered value and tracks your cost to serve (seats, usage units, projects,
   GMV). A wrong value metric makes every price wrong at some scale.
2. **Packaging.** Two to four tiers, gated on the value metric rather than
   arbitrary feature splits; every paid tier states its target segment and its
   upgrade trigger.
3. **Price anchors.** Collect competitor prices from official pricing pages
   only, each tagged `public` with `source_url` + `source_date`, archived in
   `bp_<slug>/sources.md`. Anchors position your price. **They are never
   willingness-to-pay evidence**: this skill inherits the prohibition against
   treating competitor pricing as WTP. WTP evidence is actual purchases,
   current documented spend on the problem, or a Van Westendorp survey run on
   real respondents (never simulated ones).
4. **Explicit decisions**, each recorded with its tag (adapted from
   codex-startup-business-planner): free plan vs trial; monthly vs annual;
   per-seat vs usage vs flat vs hybrid metric; one-time or lifetime viability
   (a lifetime price against recurring costs is a standing invariant risk);
   limits and upgrade triggers per tier.
5. **Every planned price is an `assumption` until transaction evidence
   exists.** Write the experiment that would upgrade it.

### 8. Viability gate: LTV > 3x CAC

The gate is the check that closes every canvas and pricing artifact:
LTV greater than three times CAC (SaaS viability heuristic, Business Model
Canvas practice; provenance below). It is a screening threshold, not an
empirical law, and this skill never computes it in prose.

The only legitimate procedure:

```bash
FA=~/.claude/skills/financial-analysis/scripts/fa.sh

# Drivers already tagged and saved in the state file
# (arpa, gross_margin_pct or price + unit_variable_cost, monthly_churn_rate,
#  sm_spend, new_customers, fixed_monthly_costs):
"$FA" unit-economics --inputs-file bp_<slug>/<slug>.bp.json --json \
  > bp_<slug>/unit-economics.json
```

`fa.sh` reads the same tagged wrapper format as `.bp.json`, so the one state
file per project stays the single source of inputs. Then:

- Quote `ltv`, `cac`, `ltv_cac_ratio`, and `cac_payback_months` **only** from
  the saved `bp_<slug>/unit-economics.json`, verbatim.
- Gate verdict: pass when the artifact's `ltv_cac_ratio` exceeds 3. Between 1
  and 3, the model earns money but likely not enough to fund growth; below 1,
  every sale destroys value. State which side of the line the artifact shows.
- If the artifact reports the ratio under `not_computed` — or `bp.sh doctor`
  says financial delegation is unavailable — the viability line reads exactly
  that, with the reason, and the artifact's `missing` list becomes the next
  question round. Never plug a default to force a verdict.

### 9. Precision and voice

- The saved `unit-economics.json` keeps every decimal; the artifact's prose
  rounds to what the weakest driver justifies and names the band. When churn is
  an assumption, the finding is "comfortably clear of the 3x screen" or "under
  it", with the range that assumption spans — not a two-decimal ratio presented
  as a measurement (SKILL.md evidence rule 6). The ratio prints the two figures
  it divides, so the reader can do the division without the artifact (rule 7).
- Driver keys (`arpa`, `monthly_churn_rate`, `unit_variable_cost`), envelope
  fields (`not_computed`, `missing`) and file names belong in the driver table
  and the method note. The argument speaks in revenue per customer, churn, and
  cost to serve, and names the tool once (rule 8).

## Benchmarks with provenance

This file ships no market statistics. The only numeric claims it carries are
framework heuristics, labeled as such:

| Claim | Label and origin |
|---|---|
| LTV > 3x CAC as the viability threshold | Framework heuristic, SaaS viability practice within the Business Model Canvas tradition; appears as the economic-viability step of the pm-skills business-model flow. Not an empirical benchmark; compute the ratio only via `fa.sh unit-economics`. |
| Freemium conversion "typically 1 to 5%" | Heuristic stated in pm-skills monetization-strategy without a primary source. If used at all, tag it `assumption` with exactly that basis. |
| Annual discount of 15 to 20% off monthly | Packaging convention stated in pm-skills pricing-strategy without a primary source. An anchor for tier design, never WTP evidence. |

Rules for any other figure in a business-model artifact:

- Market or pricing figures enter only as `public` with `source_url` +
  `source_date` (protocol in `references/research.md`, two independent sources
  for market claims) or as `assumption` with a stated basis.
- Competitor prices are anchors. Label them as anchors in the artifact and
  never present them as willingness-to-pay evidence.
- A `public` tag without a URL is downgraded to `assumption` at runtime and
  fails `bp.sh validate`; do not fight the tooling, cite the source.

Framework attribution (all accessed 2026-08-19):

- Business Model Canvas: Alexander Osterwalder, Strategyzer. Lean Canvas:
  Ash Maurya. Startup Canvas: Pawel Huryn. Flows adapted and condensed from
  pm-skills (MIT), https://github.com/phuryn/pm-skills
- Monetization criteria, explicit pricing decisions, and the
  PRIMARY/ALTERNATIVE/TEST/REJECT verdict set: adapted from
  codex-startup-business-planner (MIT),
  https://github.com/Kappaemme-git/codex-startup-business-planner

## Handoffs

- ICP, market sizing, interviews, channels, qualification:
  `references/market-gtm.md`.
- Scenario stress-test of the chosen model: `references/scenarios.md`, then
  `bp.sh scenarios` (emits `fa.sh`-ready driver files; base multipliers pinned
  at 1.0).
- All financial computation: `fa.sh unit-economics` for the gate,
  `fa.sh projection` for the 36-month view; every output saved under
  `bp_<slug>/` before a single figure is quoted.
- Sourcing any public number: `references/research.md` first, citations
  archived in `bp_<slug>/sources.md`.
- Canvas output layout: `assets/templates/canvases.md`.
- Before delivery: `bp.sh lint bp_<slug>/ --json` must pass; fix violations
  rather than allowlisting them.
