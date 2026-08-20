# Market and go-to-market: ICP, sizing, interviews, decisions, channels, qualification

Serves the MODULE route (ICP, market sizing, GTM) and the market sections of
FULL-PLAN. The center of gravity is `bp.sh market`: a bottom-up sizing chain
where every step carries provenance and an unknown step truncates honestly.

## When NOT to use

- "Should this idea exist at all" is upstream validation: office-hours skill.
  This file assumes the answer is yes and the question is who, how many, and
  through which door.
- Canvas, revenue streams, monetization, pricing: `references/business-model.md`.
- Top-down sizing requests ("take 1% of the $N B market"). Not supported
  anywhere in this skill; `bp.sh market` exits 3 on that shape by contract.
  Offer the bottom-up method instead.
- Financial outcomes (CAC, LTV, payback, projections): `fa.sh` territory.
  This file only defines which drivers the GTM plan feeds into it.
- Audit verdicts on an existing model: `references/evaluate.md`.

## Input checklist

- Stage (`idea | validating | building | revenue`) and geography.
- Segment hypotheses, plus whatever evidence exists for them: interview notes,
  current-spend signals, waitlists. Tag each item honestly; friend-heavy
  interview samples are weaker evidence and the scoring below discounts them.
- For sizing: the bottom-up chain steps, each tagged. `public` steps need
  `source_url` + `source_date` (protocol in `references/research.md`);
  estimates are `assumption` with a basis; anything else is `unknown`.
- Sales motion, if known (product-led vs sales-led), to pick the qualification
  framework in section 6.
- Existing project state: `bp_<slug>/<slug>.bp.json` and `decisions/` carry
  across sessions; read before asking anything twice.

## Method

### 1. ICP and anti-ICP

Schema adapted from codex-startup-business-planner (MIT); the delivered layout
is `assets/templates/icp.md`. One segment per pass; two equally good segments
make a decision record, not a merged profile.

| Field | What goes in it |
|---|---|
| primary_segment | One narrow segment, named tightly enough that a list of its members could be built |
| user | Who touches the product day to day |
| buyer | Who approves the money. If user and buyer are the same person, say so explicitly |
| company_profile | Size band, industry, tooling, and maturity markers that make the problem acute |
| buying_trigger | The event that opens budget: an audit, a hire, a funding round, a breakage |
| qualification_signals | Observable facts that mark a fit before any conversation |
| anti_icp | Disqualifying attributes: who you refuse even if they would pay, and why they would churn or distort the roadmap |
| where_to_find | Where these buyers already gather: communities, events, lists, marketplaces |

Rules:

- `anti_icp` is mandatory and non-empty. An ICP without disqualifiers is a
  description of everyone.
- Keep the user/buyer distinction alive downstream: interviews target users,
  qualification targets buyers, and pricing anchors to the buyer's alternative.
- Never substitute followers, page views, GitHub stars, or a broad industry
  total for an account count without labeling the proxy and its limitation.

### 2. Bottom-up TAM/SAM/SOM

The discipline (adapted from codex-startup-business-planner): sizing is built
from counts of accounts you could actually name, times what one account pays.

- TAM = eligible accounts x annual revenue per account
- SAM = serviceable accounts x annual revenue per account
- SOM = accounts realistically acquired within the plan horizon x annual
  revenue per account

`bp.sh market` computes the chain as a cumulative product. Input shape (frozen
contract): a `steps` list where each step is a tagged number and a step may
mark a level boundary with `marks`. Example shape; replace every `<...>`
placeholder with real tagged data, and note this is a shape, not runnable
numbers:

```json
{"inputs": {"steps": {"value": [
  {"name": "<count-of-eligible-accounts>", "value": "<integer>",
   "status": "public", "source_url": "<gov-or-industry-url>",
   "source_date": "<YYYY-MM-DD>", "marks": "TAM"},
  {"name": "<share-serviceable>", "value": "<fraction-0-to-1>",
   "status": "public", "source_url": "<url>", "source_date": "<YYYY-MM-DD>"},
  {"name": "<share-reachable-today>", "value": "<fraction-0-to-1>",
   "status": "assumption", "basis": "<why-this-fraction>", "marks": "SAM"},
  {"name": "<share-won-in-24-months>", "value": "<fraction-0-to-1>",
   "status": "assumption", "basis": "<capacity: reps, funnel, cycle length>",
   "marks": "SOM"},
  {"name": "<annual-revenue-per-account>", "value": "<currency-amount>",
   "status": "assumption", "basis": "<planned-tier-price x 12>",
   "marks": "SOM_REVENUE"}
], "status": "user"}}}
```

Save the steps into the state file, then run:

```bash
BP=~/.claude/skills/business-planning/scripts/bp.sh
"$BP" market --inputs-file bp_<slug>/<slug>.bp.json --json > bp_<slug>/market.json
```

Semantics and rules:

- Cumulative product down the chain; each `marks` boundary emits `tam`, `sam`,
  `som` (accounts) and `som_revenue`.
- An `unknown` step (value null) truncates: everything downstream lands in
  `not_computed` with the step named, and the step itself joins the `missing`
  list. That output is the question agenda, not a failure.
- A `public` step without a URL is downgraded to `assumption` at runtime and
  fails `bp.sh validate`. Cite or relabel.
- A currency-denominated market total combined with a bare percentage share
  is the top-down shape: exit 3 with a corrective message. Rebuild from
  account counts.
- Quote `tam`, `sam`, `som`, `som_revenue` only from the saved
  `bp_<slug>/market.json`, verbatim.

**Trend, not snapshot.** A market claim is a series, not a point. When a source
publishes the same metric across periods — category revenue, penetration,
account counts, average price — read every period it publishes and cite the
series, not the newest figure. One period is a data point; four periods flat
against a "fast-growing category" claim is a finding, and it belongs in the
why-now argument rather than a footnote. Two checks settle most of it: is the
growth rate the market's or one company's, and does the base year of the series
match the base year of the step it feeds? A chain step sourced from a
five-year-old count inherits five years of drift, and the plan says so instead
of implying currency.

### 3. Mom Test interviews

Template adapted near-verbatim from founder-os (MIT); method from Rob
Fitzpatrick, "The Mom Test" (2013). Ask about their life, past behavior, and
actual spending. Never pitch, never ask for opinions about the idea.

Before scheduling: subject matches the ICP; not a friend or supporter (the
founder-os discipline: at least 70% of interviews with strangers); 30 minutes;
video. Write the hypothesis and kill criteria first and do not edit them after:

> "We believe [specific customer] experiences [specific problem] when
> [specific situation]. We confirm if [positive signal]. We kill if
> [negative signal]."

Opening (2 min): "I'm doing research on how [their role] handles [broad
problem area]. I'm not selling anything. I'll mostly ask how you work today."
Do not say "I'm building a tool that..." or "I'd love feedback on my idea."

Question flow:

1. Context (3 min): their role; the three most time-consuming tasks in a
   typical week; the most frustrating recurring part. Note whether your
   problem area appears unprompted; weight it heavily if it does.
2. Problem stories (15 min): "Tell me about the last time [problem] caused
   you a headache; what actually happened?" Then frequency, and worst-case
   cost when it goes wrong.
3. Current behavior: "Walk me through exactly what you do when it occurs."
   Workarounds are the highest-value signal; "it works itself out" is a kill
   signal. What tools; whether they ever searched for a better solution.
4. Money and time: hours per week or month it costs; whether any money is
   already spent on it (current spend is proven willingness to pay and a
   price ceiling datum).
5. Commitment (5 min): what a solution would unlock, in their numbers;
   active project or background annoyance; if the concept is mentioned at
   all, only in the last five minutes, and the ask is a prototype follow-up.
   "Can I pay to be first in line?" is signal; "send me an email sometime"
   is noise.

Questions that seem good but are not:

| Do not ask | Ask instead |
|---|---|
| "Do you think this is a big problem?" | "How did you handle it last time?" |
| "What features would you want?" | "What's the worst part of your current approach?" |
| "Would you pay $X/month?" | "What do you currently spend on this?" |
| "Would your company buy this?" | "Who else is involved when you buy tools like this?" |

Within 30 minutes after, capture: subject profile (no names); a signal inventory
with verbatim evidence (problem unprompted, specific incident, current
workaround, money spent, time spent, frustration with existing tools, asked to
try it, offered a referral); three quotes; what surprised you; the hypothesis
update (CONFIRM / REFUTE / NEUTRAL, plus the running tally). Score quality 1 to
5 on subject fit, specificity, unprompted signal, commitment, and objectivity;
founder-os discounts anything under 12 of 25 as noise. The `problem_evidence`
dimension reaches `validated` or `researched` only when these records exist.

### 4. Go / pivot / kill

Decision framework adapted from founder-os (MIT). Its purpose is to resist
motivated reasoning: the conversion of a PIVOT into a GO because months were
invested. All thresholds are framework heuristics against founder-os's 0 to
90 validation scorecard, calibrated for roughly 10 quality stranger
interviews (fewer, or friend-heavy samples: discount by 10 to 15 points):

| Score | Verdict | Action |
|---|---|---|
| 68 to 90 | GO | Proceed to business model work |
| 54 to 67 | Soft PIVOT | One dimension is broken; fix it with 5 targeted interviews |
| 36 to 53 | Hard PIVOT | Several dimensions failing; reformulate the hypothesis |
| 0 to 35 | KILL | The evidence does not support this idea, in this form, for this customer |

A GO needs all of: problem mentioned unprompted by at least half the
subjects; specific incidents recalled by most; active workarounds common;
some subjects already spending money; the pre-registered positive signal
observed; and a plausible market from the section 2 chain (founder-os uses a
$500M TAM heuristic; the chain is the evidence, the number is theirs).

A PIVOT is one broken dimension, diagnosed before acting: wrong segment, pain
too mild, no urgency, wrong buyer or pricing, market too small (or a wedge into
an adjacent one), strong incumbents, demand too early, wrong team. Write a new
pre-registered hypothesis and preserve the positive evidence from the old one.

KILL when any holds: near-zero unprompted problem recognition after 10+ good
interviews; no workarounds and no prior search anywhere in the sample; zero
current spend and zero commitment; the pre-registered kill criterion fired; a
well-liked incumbent owns the space with no clear differentiation. KILL rather
than pivot after two reformulation rounds with no improving signal, or when
finding even five people willing to talk proved impossible. Document every KILL
under `bp_<slug>/decisions/`: hypothesis, evidence, the kill signals, what was
learned, and adjacent ideas worth exploring.

### 5. GTM channel selection

- Candidate channels come from the ICP's `where_to_find` list, nowhere else. A
  channel where the buyer does not already gather is a hope, not a channel.
- Match channel to `buying_trigger`: the winning channel reaches the buyer near
  the trigger event, when budget is open. A great channel at the wrong moment
  produces impressions, not customers.
- Sequence wedge-first: one segment, one channel, one offer, until it repeatedly
  converts or a stop condition trips. Expanding before the wedge works
  multiplies spend, not learning.
- Write funnel assumptions as `assumption` entries (visitor-to-lead,
  lead-to-close, cycle length) and define stop conditions before launch. A
  channel plan without stop conditions cannot fail, so it cannot be tested.
- Motion fork: product-led when the user can start alone and value shows up
  fast; sales-led when the buyer is not the user or procurement is involved.
  Sales-led motions continue to section 6.
- The channel plan feeds the delegation seam: per-channel `sm_spend` and
  `new_customers` are the CAC drivers for `fa.sh unit-economics` and the
  growth drivers for `bp.sh scenarios`.

### 6. MEDDIC / BANT qualification (sales-led motions)

Compact references adapted from founder-os (MIT). BANT (IBM) filters whether to
invest sales time; MEDDIC (Dunkel and Napoli, PTC) manages a qualified deal
through multiple stakeholders. BANT at the top of the funnel, MEDDIC on long
cycles.

BANT, one point each, qualified when: **Budget** — allocated, or the problem's
cost justifies creating it. **Authority** — the contact decides, or brings the
decision-maker in. **Need** — named pain, known cost, a reason to act now.
**Timeline** — a decision inside ~90 days with a forcing event behind it.
Scoring: 4/4 advance now; 3/4 advance while developing the weak criterion; 2/4
nurture; below that disqualify cleanly. "No budget" often means "not yet a
priority", so probe before disqualifying.

MEDDIC, 0 to 2 per component, 12 maximum, strong when: **Metrics** — an ROI
model the buyer agrees with. **Economic Buyer** — identified and met, not just
named. **Decision Criteria** — formal and informal, including the unwritten
ones. **Decision Process** — mapped through procurement and legal. **Identify
Pain** — active, with a stated consequence of waiting. **Champion** — will
arrange the Economic Buyer meeting. Bands (founder-os): 10 to 12 commit; 7 to 9
best case, develop the weakest component; 4 to 6 pipeline only; below 4 is not
a real deal.

The hardest competitor is "do nothing": quantify the cost of inaction from the
buyer's own numbers, gathered in discovery, never invented for them.

### 7. Precision and voice in the market sections

- The chain artifact keeps full precision; the prose rounds to what the weakest
  step justifies and states the band. A SOM resting on two assumption-tagged
  fractions reads "roughly nine hundred accounts, and the count moves by a third
  if the reachability fraction is wrong" — not a figure carried to the unit,
  which claims a precision no fraction in the chain has.
- The chain prints so the reader can multiply it: each step as count x rate =
  result, ending on the SOM headline, with no step visible only in the artifact
  (rule 7).
- Step names, `marks` boundaries, `not_computed`, `missing` and file names stay
  in the chain table and the method note (SKILL.md evidence rules 6 and 8). The
  argument names the accounts, what each one pays, and the door you reach them
  through; it names the tool once.

## Benchmarks with provenance

This file ships no market statistics. Every numeric threshold above is a
framework heuristic, labeled here once:

| Numbers | Label and origin |
|---|---|
| 70% strangers, 30-minute format, quality score bands | Interview discipline heuristics, founder-os mom-test template; method from Fitzpatrick, "The Mom Test" (2013) |
| 0 to 90 scorecard bands (68/54/36 cuts), 10-interview minimum, 10 to 15 point friend-sample discount | Decision heuristics, founder-os go-pivot-kill framework |
| $500M TAM (GO) and $100M TAM (KILL) screens | founder-os heuristics; in this skill any TAM figure must come from the section 2 chain with per-step provenance, never from the heuristic itself |
| BANT ~90-day timeline, 4-point scoring; MEDDIC 12-point bands; deal-size split between the two | Sales qualification heuristics, founder-os meddic-bant-challenger reference; BANT originally IBM, MEDDIC from PTC (Dunkel and Napoli), Challenger research in Dixon and Adamson, "The Challenger Sale" (2011) |

Rules for real figures: market sizes, account counts, and adoption shares
enter only through the bottom-up chain, each step `public` with URL + access
date (two independent sources per `references/research.md`) or `assumption`
with a basis. Heuristics never appear inside a plan artifact as market facts;
if quoted, they are quoted as heuristics with their origin, as labeled here.

Source repositories (all MIT, accessed 2026-08-19):

- founder-os: https://github.com/vinicius91carvalho/founder-os
  (mom-test-interview, go-pivot-kill, meddic-bant-challenger)
- codex-startup-business-planner:
  https://github.com/Kappaemme-git/codex-startup-business-planner
  (ICP schema, bottom-up sizing discipline)
- pm-skills: https://github.com/phuryn/pm-skills (market-sizing framing;
  its top-down triangulation step is deliberately not adopted here)

## Handoffs

- Canvas, revenue streams, monetization, pricing:
  `references/business-model.md`; its viability gate consumes the CAC drivers
  this file's channel plan produces.
- Scenario stress-tests of GTM assumptions: `references/scenarios.md`, then
  `bp.sh scenarios` and `fa.sh projection`.
- Sourcing any public number for the sizing chain: `references/research.md`
  first; archive citations in `bp_<slug>/sources.md`.
- Readiness verdict (the `icp_specificity`, `reachable_market`, and `gtm`
  dimensions draw on this file's outputs): `references/evaluate.md`,
  `bp.sh readiness`.
- Structured challenge of a GO verdict the user doubts: the sat skill.
- Before delivery: `bp.sh lint bp_<slug>/ --json` must pass.
