# FULL-PLAN route: the 13-part business plan

Adapted and condensed from founder-os by Vinicius Carvalho
(github.com/vinicius91carvalho/founder-os, MIT: 13-part spec, stage detection,
smart-skip logic, pitch outline) and codex-startup-business-planner
(github.com/Kappaemme-git/codex-startup-business-planner, MIT: evidence
statuses, sizing discipline, contradiction checks). The depth ladder is a
complexity-ladder concept inspired by FISY (fisy.fr), no content reproduced.

## When NOT to use

- The user is still asking "should this exist at all?". Hand back to
  /office-hours; this route starts once the answer is yes.
- The user wants one artifact (a canvas, pricing, sizing, GTM, roadmap). That
  is the MODULE route; read only the matching reference file.
- The user wants an audit of an existing plan or model. That is EVALUATE
  (`references/evaluate.md`).
- The user wants slides rendered. This route produces a text outline only;
  rendering belongs to /executive-deck-builder.
- The user wants a product spec (/to-prd) or a new-job plan (/90-dias).
- Any financial computation. This route assembles drivers and delegates to
  fa.sh; it never computes LTV, CAC, P&L, cash, runway, or scenario outcomes.

## Input checklist

Request as ONE grouped list, then tag everything (see SKILL.md step 2).

Must-have before drafting any part:

| Input | Why |
|---|---|
| The decision this plan serves (raise, launch, internal alignment) | Sets audience, tone, and which parts carry weight |
| What the user already has (interviews, users, revenue, pricing, team) | Drives stage detection below |
| Industry, geography, currency, language of the deliverable | Research scope and localization; deliverable mirrors request language |
| Target customer as the user currently sees it | Seed for Parts 3 to 5; refined against evidence |
| The financial driver set for Part 10 | See the driver checklist in Method; missing drivers become `unknown`, not guesses |

Nice-to-have (propose labeled assumptions instead of interrogating): pricing
anchors, hiring and funding intentions, depth preference. Save every tagged
input to `bp_<slug>/<slug>.bp.json` and run `bp.sh validate` before computing.

## Method

### Step 1: detect stage from what the user already has

Classify into the closed set `idea | validating | building | revenue` using the
signal matrix. Score each column; most matching signals wins. On a tie, pick the
earlier stage: safer to validate before advancing (rule adapted from founder-os).

| Signal | idea | validating | building | revenue |
|---|---|---|---|---|
| Customer conversations about the problem | none | some, or scheduled | many, informing the build | ongoing with paying users |
| Problem framing | opinion ("I think", "people would") | evidence quoted (interviews, waitlist, complaints) | evidence plus usage data | operating metrics |
| Product | none, or sketch | none or prototype | MVP live or launching | in market, iterating |
| Customers | none | early testers at most | first users or pilots, unpaid or anecdotal | paying customers |
| Numbers the user can supply | almost none | validation counts (interviews, signups, LOIs) | usage, conversion, early CAC tests | MRR, churn, CAC actuals |

Record the detected stage in `.bp.json` meta and in the artifact frontmatter.
If the user disagrees with the detection, say which signal drove it, defer to
them, and record the override as a decision record.

### Step 2: apply the smart-skip matrix

Not every stage needs every part at full depth. `full` develops the part
completely; `compress` is a short, honest version (one to three paragraphs);
`skip*` omits it only after confirming with the user and recording a decision
record. Never skip silently (founder-os rule): the user may have unseen gaps.

| Part | idea | validating | building | revenue |
|---|---|---|---|---|
| 1 One-page summary | full | full | full | full |
| 2 Executive summary | full | full | full | full |
| 3 Company and product | compress: concept and roadmap hypothesis | compress: MVP scope plus validation plan | full | full |
| 4 Market analysis | full (chain may truncate on `unknown`; that is honest) | full | full | full |
| 5 Competition and positioning | full | full | full | full |
| 6 Business model and pricing | compress: hypothesis tiers, all prices tagged `assumption` | full, prices still hypotheses | full | full, with actuals |
| 7 Go-to-market | compress: first channel hypothesis and test plan | compress: channel test plan with stop conditions | full | full |
| 8 Operations and team | compress: founders only | compress | full | full |
| 9 Customer success | skip*: one planned-approach paragraph | compress | compress | full, with churn actuals |
| 10 Financial plan | full via fa.sh, pre-revenue substitutions apply | same | full | full |
| 11 Funding requirements | compress, or skip* when bootstrapping | same | full when raising | full when raising |
| 12 Risk analysis | full | full | full | full |
| 13 Assumptions & Limitations | full, never skipped | full | full | full |

### Step 3: pick a depth on the ladder

Depth is orthogonal to stage: stage says what evidence exists, depth says how
far each part is developed. Complexity-ladder concept inspired by FISY
(fisy.fr), no content reproduced. Default to `essential`; confirm the choice
with the user when the request is ambiguous.

| Depth | What it means | Financial delegation |
|---|---|---|
| `starter` | Parts 1, 2, 3, 4, 6, 10, 13 only; other parts get one paragraph each. For a first pass or a bootstrapped side project. | `fa.sh unit-economics` only |
| `essential` | All 13 parts at working depth per the smart-skip matrix. The default. | `unit-economics` plus `projection` (36 months) |
| `innovation` | Everything in essential, plus scenario stress tests with reversal thresholds, funding detail, and the 10-slide pitch outline. Investor-grade. | adds `fa.sh scenarios` (comparison and reversal) |

### Step 4: pre-revenue substitutions

Apply at `idea` and `validating` stages, and at `building` when there is no
revenue yet. Adapted from codex-startup-business-planner's pre-revenue mode.

- Every traction section (the traction line in Part 1, the paragraph in Part 2,
  metrics in Parts 6 and 7) becomes a validation-evidence section: interview
  count and key patterns, waitlist signups, LOIs, pilot commitments, search or
  complaint-volume signals. Each item tagged.
- Forward numbers (starting volume, growth, churn, price) are assumption-tagged
  scenario drivers, never forecasts of fact. They enter the plan only through
  the scenario table, and the conservative scenario is the planning case.
- A CAC from a small paid test is a ceiling estimate, not steady state; LTV:CAC
  is directional until real cohort data exists (see
  `financial-analysis/references/viability.md`, which this route defers to).
- No DCF, no valuation for a pre-revenue idea: a discount rate applied to
  invented cash flows is precision theater.

### Drafting order: the decisive fact leads

**The 13-part list below is a COVERAGE CHECKLIST, verified against the finished
draft. It is not the order you write in.** Drafting order is argument order:

1. The decisive fact opens the document — first screen, plain language, with its
   provenance (hunt step in SKILL.md, method in `references/decisive-fact.md`;
   the skeleton carries an unnumbered `## The decisive fact` section between the
   title and Part 1). Never skipped, at any stage or depth. An empty hunt goes
   in the same place: what you looked for, why, and how to settle it cheapest.
2. Then the argument that fact forces, in whatever order carries it.
3. Then Part 12's dependency surface — required, and the decisive fact never
   absorbs it.
4. Then the support: the tagged inputs table, the quoted artifact values, the
   frontmatter counts, Part 13. Support proves the argument; it never opens it.

Parts 1 and 2 are still written last — but written to open with the decisive
fact, not with a company description. Before delivery, walk the 13 parts as a
checklist: each present at its matrix depth, or skipped as a recorded decision.

Precision, arithmetic, and voice in every part (SKILL.md evidence rules 6 to 8):

- Tables and pasted artifact blocks keep full precision; that is echo
  discipline. The sentences around them round to what the weakest driver
  justifies and state the band — the `annual_summary` rows stay verbatim in the
  table, while the paragraph says which year matters and how much of it rests on
  an assumption, without repeating six significant figures.
- Every headline figure is rebuildable from this document alone: print the
  inputs and the operation beside the result — "transaction 2,677 + ads 1,065 =
  revenue 3,742", not "revenue 3,742 (see saved output)". Measured reason: in
  blind judging a reviewer rebuilt the rival document's entire financial spine
  live from its printed figures and could rebuild none of this skill's
  distinctive numbers, because they lived only inside artifacts nobody in the
  room can run. The saved artifact is the backup of the proof, never the proof.
- Driver identifiers (`unit_variable_cost`), envelope fields (`not_computed`,
  `missing`), guard strings and file names belong in the Part 10 driver table,
  the Part 13 relay, and the method note. The prose speaks in prices, costs,
  customers, and months, and names the tool once.

### The 13 parts

Structure adapted from founder-os (MIT). Its marketing-and-sales part is
folded into Part 7 and its legal part into Parts 8 and 12; Part 13 here is
Assumptions & Limitations, which the lint enforces. Every number in every
part carries a tag; every financial figure quotes a saved fa.sh artifact.

1. **One-page summary.** The whole thesis in under 500 words, opening on the
   decisive fact and what it implies: problem, solution, market (bottom-up),
   traction or validation evidence, model, team, and the ask (when raising).
   Written last with Part 2. Every figure repeats identically in its source part.
2. **Executive summary.** At most 800 words, standalone: problem and why now,
   what the company does, market size, evidence so far, how it makes money,
   how it acquires customers, why this team, the key numbers, the ask.
3. **Company and product.** The problem in customer language with quantified
   pain and current workarounds; the solution as outcomes, not features; the
   roadmap phased and honest about what exists today versus planned.
4. **Market analysis.** Bottom-up TAM/SAM/SOM from `bp.sh market` only: an
   ordered chain of tagged steps, cumulative product, each step cited or
   labeled. Top-down "x% of the $NB market" is rejected by the script
   (exit 3). Plus market trends and a why-now argument, each claim sourced
   per `references/research.md`. Method detail: `references/market-gtm.md`.
5. **Competition and positioning.** Direct, indirect, and do-nothing
   alternatives; per competitor: pricing (tagged `public` with URL, an anchor
   only), strengths, weaknesses, why we win. A positioning statement and the
   moat, stated structurally. "We have no competitors" is a finding to
   challenge, not to transcribe.
6. **Business model and pricing.** Revenue model choice with alternatives
   considered, tiers with upgrade triggers, free-versus-trial and
   monthly-versus-annual decisions made explicit. Prices are hypotheses until
   transaction evidence exists. Method detail: `references/business-model.md`.
7. **Go-to-market.** Phased playbook: first channel chosen because the buyer
   is demonstrably reachable there, first-100-customers plan, sales
   methodology, funnel assumptions tagged with stop conditions that can force
   a channel change. Method detail: `references/market-gtm.md`.
8. **Operations and team.** Who is on the team and why they fit this problem,
   org and hiring plan tied to milestones, governance and legal or entity
   notes where they matter. Hiring costs must match the Part 10 payroll
   drivers.
9. **Customer success.** Onboarding to first value, health signals, churn
   segmentation and prevention, expansion. The churn number used here is the
   same tagged input Part 10 delegates to fa.sh.
10. **Financial plan.** A driver checklist and delegation recipe; see below.
    This part NEVER computes.
11. **Funding requirements.** The ask, instrument, use of funds tied to
    milestones (each category names what it achieves), post-raise runway
    quoted from the saved projection artifact. Skip or compress per the
    matrix when bootstrapping.
12. **Risk analysis.** Required at every stage and depth, and the decisive
    fact never absorbs it: name every dependency the plan's case rests on,
    including the ones that fact does not touch. Run the checklist —
    customer, supplier and channel concentration · regulatory · labour and
    worker classification · key person · platform or single-vendor dependency
    · litigation · liquidity and financing — and give each either a row with
    likelihood, impact and a specific mitigation, or one line saying it does
    not apply here and why. A deep single finding over a thin risk surface
    loses to a plainer document that maps the whole surface; that is measured
    in blind judging, not a matter of taste. Financial rows quote reversal
    thresholds from saved `fa.sh scenarios` output when depth is
    `innovation`, printed as the driver's current value and the value at the
    flip with its direction, never as a bare multiplier.
13. **Assumptions & Limitations.** See below. Consolidates every assumption
    and unknown in the document.

### Part 10: the financial plan is a driver checklist

This part assembles tagged drivers and delegates. All arithmetic runs in fa.sh;
the plan quotes only values present in saved output JSONs. Driver names below
are the real ones from `financial-analysis/references/viability.md`; read that
file before emitting any driver file.

Must-have drivers (missing ones become `unknown` and the section says so). For
`projection`: price per unit or subscription `activities[].price`; bottom-up
starting volume and monthly growth `activities[].volume_start` +
`activities[].volume_growth_pct_monthly` (percent: 10 = 10%), or explicit
`activities[].volumes`; variable cost per unit `activities[].unit_variable_cost`;
cash in the bank today `starting_cash`; itemized fixed costs `opex_lines[]`; the
team plan `payroll[]`. For `unit-economics`: revenue per customer per month
`arpa`; monthly churn `monthly_churn_rate` (0-1 fraction: 3% = 0.03); and, for
the same period, `sm_spend` with `new_customers`.

Nice-to-have drivers (`gross_margin_pct`, `tax_rate_pct`, `dso_days`,
`dpo_days`, `capex[]`, `loans[]`, `funding[]`, `months`, `fixed_monthly_costs`)
are specified in viability.md. Unit conventions differ by design: relay them
exactly as that file states them, and tag every scalar so provenance survives
into the envelope echo. When payroll or tax matters, run its localization
procedure — ask the country, research burden and tax components with the user,
tag each component.

Delegation recipe (quote nothing that is not in a saved file):

```bash
BP=~/.claude/skills/business-planning/scripts/bp.sh
FA=~/.claude/skills/financial-analysis/scripts/fa.sh

# 1. Scenario table + fa.sh-ready driver objects (base multipliers pinned at 1.0);
#    write the emitted driver_files to bp_acme/scenarios/drivers-<scenario>.json
$BP scenarios --inputs-file bp_acme/acme.bp.json --json

# 2. Outcomes come from fa.sh, one saved JSON per run
$FA unit-economics --inputs-file bp_acme/acme.fa.json --json > bp_acme/unit-economics.json
$FA projection --drivers-file bp_acme/scenarios/drivers-base.json --json \
  > bp_acme/scenarios/projection-base.json

# 3. Stress (depth = innovation): comparison and reversal thresholds
$FA scenarios --model projection --drivers-file bp_acme/scenarios/drivers-base.json \
  --scenarios-file bp_acme/scenarios/scenarios.json --json \
  > bp_acme/scenarios/comparison.json
```

The part's body then contains: the driver table with tags, the 3-year
`annual_summary` pasted verbatim, break-even and cash floor with tag trails,
runway per scenario (conservative is the planning row), and the guard
messages relayed as findings. If fa.sh is unavailable (`bp.sh doctor` says
so), the section carries `not_computed` entries, not estimates.

### Part 13: Assumptions & Limitations

The consolidation part; `bp.sh lint` fails the artifact without it (heading
must contain "Assumptions & Limitations", or "Premissas e Limitações" in
Portuguese deliverables). It collects, from every part:

- every input tagged `assumption`, with its basis and what evidence would
  upgrade it;
- every `unknown`, rendered as unknown (never blank, never zero), with what
  would settle it;
- every warning and `not_computed` entry relayed from script envelopes;
- scope limits, and the disclaimer that projections are scenario math on
  stated drivers, not predictions.

Order by load: the assumption that moves the verdict most goes first (use
reversal output when available).

### Artifact frontmatter

The block itself is in `assets/templates/plan-skeleton.md`; fill it, do not
retype it. `bp.sh lint` requires four keys: `research_sources` (the COUNT of
sources archived in `bp_<slug>/sources.md` — founder-os inlines the URL list,
this skill counts and archives), `confidence_level` (rubric in
`references/research.md`), `stage`, and `mode`. The skeleton also carries
`slug`, `route`, `depth`, `language`, and `date`; keep values bare for the linter.

### The 10-slide pitch outline (text only)

Produce it only at depth `innovation` or on request. Slide order and per-slide
content live in `assets/templates/pitch-outline.md`, which is the authority; the
outline stays a text file inside `bp_<slug>/`, and rendering is
/executive-deck-builder's job. This route contributes the discipline:

- One idea per slide; numbers beat adjectives; a number on a slide appears
  identically in the plan part it came from, because both quote the same saved
  artifact (`market.json`, the projection, `unit-economics.json`).
- The decisive fact is the headline of whichever slide it belongs to — problem,
  market, model, or competition — never a footnote on it.
- Each slide answers one silent investor question, and the outline is wrong if
  any of the ten goes unanswered: should I pay attention · is the problem real
  and widespread · does the approach convince · is the market big enough · how
  does it make money · what is hard to copy · can you reach the buyer · why do
  you win against the alternatives, including doing nothing · do the numbers
  hold · who builds this, what do they need, and what does it buy.
- Pre-revenue, the traction claim is validation evidence with tags, or it reads
  "Unknown" and says what would settle it. Adjectives do not substitute.

### Assembly checks before delivery

- Cross-part consistency is mechanical: a number may appear in several parts
  only because each occurrence quotes the same saved artifact value.
- Rebuild test: pick the three figures the argument leans on and check that a
  reader with no terminal can recompute each from figures printed in the plan.
- Coverage test: every checklist item in Part 12 answered, none left silent
  because the decisive fact went deep somewhere else.
- Contradiction sweep (from codex-startup-business-planner): does pricing
  track value and cost; does a free plan expose uncapped costs; does the
  forecast assume acquisition without a named channel; does any scenario
  change outputs without changing drivers; is any price called proven
  without purchase evidence?
- `bp.sh lint bp_<slug>/ --json` must pass; fix violations, do not allowlist.
- No placeholder text ("[TODO]", "[INSERT]") remains.

## Benchmarks with provenance

This route file carries no market figures. Any benchmark quoted in a plan
follows `references/research.md` (tier, URL, access date) or is labeled a
framework heuristic with its origin named. Heuristics this route may cite:

- SAM typically 10 to 30% of TAM for a focused startup; year-1 penetration
  typically 1 to 5% (founder-os planning heuristics, MIT; label as heuristic,
  never as market data).
- TAM above $1B for venture relevance (founder-os pitch heuristic reflecting
  common VC practice; irrelevant for bootstrapped plans, and the plan says so).
- LTV:CAC, payback, and margin bands live in
  `financial-analysis/references/viability.md` with their own provenance
  block; quote them from there, never from memory.

## Handoffs

- **financial-analysis**: all Part 10 computation, localization research, and
  the benchmark bands. Physical rule: no saved fa.sh JSON, no figure in the plan.
- **executive-deck-builder**: renders the 10-slide outline into a deck.
- **office-hours**: back upstream when drafting reveals the idea itself is
  still in question.
- **plan-ceo-review**: ambition and scope critique of the finished plan.
- **sat**: premortem and kill-assumptions challenge at the stress-test step.
- **problem-solving**: issue-tree framing when the request arrives unstructured.
- **expert-review**: outside perspectives before the user commits.
- **to-prd**: when Part 3's roadmap needs a real product spec.
- **humanizer**: prose conventions for every deliverable section.
