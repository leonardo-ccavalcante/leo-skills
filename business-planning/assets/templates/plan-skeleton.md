---
research_sources: 0
confidence_level: LOW
stage: idea
mode: pre-revenue
depth: starter
slug: <slug>
route: FULL-PLAN
language: <language of the user's request>
---

<!-- plan-skeleton.md: 13-part business plan template.
     Frozen by contract: the first four frontmatter keys above (bp.sh lint
     requires them), the decisive-fact section below the title, the Part 13
     heading ("Assumptions & Limitations", PT: "Premissas e Limitações"), and
     the Inputs & Sources table. Part titles 1-12 follow
     references/full-plan.md; the stage/depth matrices there say which parts to
     skip. The decisive-fact section is not a numbered part and is never
     skipped — SKILL.md Step 5 requires the plan to open with it.
     Frontmatter values stay bare (the linter reads the raw value):
     research_sources integer >= 0, count of independent sources cited;
     confidence_level HIGH | MEDIUM | LOW; stage idea | validating | building |
     revenue; mode pre-revenue | revenue; depth starter | essential | innovation.
     Rules for filling this in:
     - Replace every <placeholder>. Write in the language of the user's request;
       framework terms (TAM, SAM, SOM, ICP, LTV, CAC, GTM) stay in English.
     - Every number in the body must exist in the Inputs & Sources table or in a
       saved script artifact under bp_<slug>/. The linter flags currency and
       percent figures that appear nowhere else ("orphan figures"). For a figure
       that is legitimately body-only, put `<!-- bp-lint: allow -->` on the line
       above it, but fixing the table is almost always the right move.
     - Every headline figure shows its arithmetic on the page: the inputs and
       the operation beside the result ("transaction 2,677 + ads 1,065 =
       revenue 3,742"), never "revenue 3,742 (see saved output)". Measured: in
       blind judging a reviewer rebuilt the rival document's whole financial
       spine live from its printed figures and could rebuild none of this
       skill's, because they lived only inside artifacts nobody can run.
     - Unknowns render as "Unknown". Never blank, never zero, never an average. -->

# <company>: business plan

## The decisive fact

<!-- Where Step 4 lands. One fact — the one that most changes the reader's
     decision — in plain language, with where it came from and what it moves.
     Written after the parts below are researched, read before all of them.
     Rules:
     - It leads. The readiness verdict, the tag table, the artifact list and
       the script names are support; none of them belongs above this line.
     - Provenance travels with the fact: user / public (URL + access date) /
       assumption (with basis) / unknown. A fact that is only an assumption
       says so in the same sentence, and still leads.
     - "What it changes" names a decision, not a mood: which way the reader
       leans now, and the value at which they would lean the other way. When
       the fact is a driver, that flip value comes from `bp.sh scenarios` and
       the saved fa.sh artifact, and prints as the driver's own value ("breaks
       below about 820 a month"), never as a bare multiplier.
     - One fact. Three findings are a list — rank candidates by swing and lead
       with the winner; runners-up go in the part they inform or in decisions/.
     - Prose rounds to the precision the weakest input supports and says the
       band out loud; the artifact keeps the decimals.
     - An empty hunt keeps this section and the form below at the same
       prominence: an honest unknown opens better than a plan that never asked.
     - The heading translates with the rest of the document. -->

<the decisive fact, one or two sentences, in plain language>

- Where it comes from: <source and tag; public claims carry URL, access date, and tier>
- What it changes: <the decision it moves, and the value at which it would move the other way>

<!-- Empty-hunt form — replaces the three lines above and keeps the heading:
     "The fact that decides this is <the fact>. We looked in <the sources and
     searches, archived in sources.md> and it is not published there. The
     cheapest way to settle it is <the call, the filing, the experiment>, at
     <effort in days or interviews>; until then the plan carries it as <the
     labeled assumption>, and Part 12 lists it as a kill assumption." -->

## Part 1: One-page summary

<!-- Write this LAST. The whole thesis in under 500 words: the decision this
     plan serves, the decisive fact above and what it changes, the readiness
     verdict (from bp_<slug>/readiness.json), the som_revenue headline (from
     bp_<slug>/market.json), and the ask. Quote only values present in saved
     artifacts, carry each headline figure's arithmetic with it — this page is
     where a reader checks the spine — and keep the argument ahead of the
     machinery here too. -->

<one-page summary>

## Part 2: Executive summary

<!-- At most 800 words, standalone: problem and why now, solution, market,
     model, traction or validation evidence, team, ask. -->

<executive summary>

## Part 3: Company and product

<!-- The problem in customer language with quantified pain, how you know
     (every claim tagged), what the product does, and what it replaces. -->

<problem statement and product description>

| Claim | Tag | Basis / source |
|---|---|---|
| <claim> | <user / public / assumption / unknown> | <basis or sources.md ref> |

## Part 4: Market analysis

<!-- ICP first, sizing second. ICP + anti-ICP from assets/templates/icp.md:
     the anti-ICP (who you will NOT serve) is what makes the ICP falsifiable.
     Sizing is bottom-up only: counts times rates, computed by `bp.sh market`,
     saved to bp_<slug>/market.json. Paste the chain table from that artifact,
     each step showing its own multiplication, so the reader multiplies down
     the column to the SOM headline without opening the file. Top-down shapes
     ("x percent of the big market") are rejected by the script. Close with
     why now. -->

<ICP and anti-ICP summary>

<market sizing narrative; numbers pasted verbatim from market.json>

## Part 5: Competition and positioning

<!-- Direct, indirect, and do-nothing alternatives. Competitor prices are
     competitor price references, never willingness-to-pay evidence. Cite each
     competitor claim in sources.md. -->

<positioning statement and competitor table>

## Part 6: Business model and pricing

<!-- Canvas lives in assets/templates/canvases.md; summarize the chosen model,
     name the revenue streams, and state the pricing structure with the
     evidence behind it. Viability gate (LTV > 3x CAC heuristic) comes from the
     saved fa.sh unit-economics artifact, never prose arithmetic. -->

<business model, revenue streams, and pricing>

## Part 7: Go-to-market

<channels matched to the ICP's buying trigger, first-100-customers motion, and
the evidence targets per channel>

## Part 8: Operations and team

<!-- Who is on the team and why they fit this problem; the operating model;
     milestone plan. Roadmap detail lives in bp_<slug>/roadmap-90d.csv
     (template: assets/templates/roadmap-90d.csv); summarize workstreams. -->

<team, operating model, milestones, roadmap summary>

## Part 9: Customer success

<onboarding to first value, health signals, and churn levers; pre-revenue,
state the retention hypothesis as a tagged assumption>

## Part 10: Financial plan

<!-- Delegated: business-planning computes NO financial metric. Every figure in
     this part is pasted from a saved fa.sh --json artifact under
     bp_<slug>/scenarios/ (unit-economics, projection, scenarios). Pasting is
     not enough: each headline figure prints the inputs and the operation
     behind it (price x volume - variable cost = contribution) so the reader
     checks it without running fa.sh. If the financial-analysis skill is not
     installed, this part carries the not_computed sections honestly. -->

<unit economics, projection, and runway; values pasted from fa.sh artifacts>

## Part 11: Funding requirements

<the ask, instrument, and use of funds tied to the milestones in Part 8>

## Part 12: Risk analysis

<!-- Market, execution, financial, competitive, and customer risks. Scenario
     assumption table from `bp.sh scenarios` (base multipliers pinned at 1.0);
     outcomes from fa.sh. Scenario and reversal figures print the driver — its
     current value, the value at the flip, and the direction ("volume 1,200 a
     month today, breaks below about 820") — not a bare multiplier. Include the
     kill-assumptions table: which single assumption, if wrong, kills the plan.
     Required section, and the decisive fact never absorbs it: name every
     dependency the plan rests on, including the ones that fact does not touch
     — concentration (customer, supplier, channel), regulatory, labour and
     worker classification, key person, platform dependency, litigation,
     liquidity — each as a row, or one line saying it does not apply and why. -->

<risk register, dependency checklist, scenario table, and kill-assumptions table>

## Part 13: Assumptions & Limitations

<!-- Frozen heading (PT: "Premissas e Limitações"). The linter requires this
     section. List every assumption tag with its basis, every unknown with the
     evidence that would settle it, and what this plan does NOT claim. -->

| # | Assumption or unknown | Tag | Basis / evidence that would settle it |
|---|---|---|---|
| 1 | <assumption> | <assumption / unknown> | <basis, or the data that would resolve it> |

<limitations: what this plan does not cover and why>

## Appendix: Inputs & Sources

<!-- The provenance backbone. Mirror of bp_<slug>/<slug>.bp.json plus
     sources.md. Every numeric driver used anywhere in the plan appears here
     with its tag; every public source carries URL, access date, and tier. -->

### Tagged inputs

| Input | Value | Status | Basis | Source URL | Source date | Confidence |
|---|---|---|---|---|---|---|
| <name> | <value or Unknown> | <user / public / assumption / unknown> | <basis> | <url or n/a> | <ISO date or n/a> | <low / medium / high> |

### Sources

| # | Claim supported | URL | Access date | Tier |
|---|---|---|---|---|
| 1 | <claim> | <url> | <ISO date> | <gov_industry / analyst / press / blog> |
