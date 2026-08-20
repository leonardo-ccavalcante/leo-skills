# The decisive fact: hunting the number that settles the question

Read at Step 4 of every route, before drafting.

## Why this file exists

This is not a style preference. It comes from a measured failure of this skill.

In a blind quality comparison (iteration 1, three cases, three independent lenses,
judges who did not know which document came from which process), plans produced WITH
this skill lost 7 of 9 judgments to plans produced without it — while scoring 100% on
provenance discipline against the baseline's 19%. Every number was tagged, every
computation was delegated, every artifact was saved. And the analysis still lost.

The clearest instance: evaluating Instacart, the baseline noticed that advertising take
rate had been stuck near 2.9% of GTV across four consecutive reporting periods, when the
company's own IPO thesis was expansion toward 4-5%. That is the fact the investor
decision turns on: the highest-margin lever is not levering. The skill-driven analysis
never disaggregated advertising at all. It was more auditable and less useful.

The diagnosis: **provenance machinery is seductive.** Tagging, computing, saving and
reconciling consume exactly the attention that finding the decisive fact requires. A
plan can be perfectly traceable and still miss the point. This step is the counterweight.

## Method

### 1. Name the candidates before you look

Write down two or three facts in this form: *"If X turned out to be <value>, the reader
would decide differently."* If you cannot complete that sentence, you do not yet
understand the decision, and Step 1 was done too quickly.

Good candidates share a shape: they are **specific, checkable, and load-bearing**. "The
market might be smaller than we think" is not a candidate. "Advertising take rate has not
expanded in four periods despite being the stated thesis" is.

### 2. Estimate the swing, then spend where it is largest

For each candidate ask: how much does the recommendation move between the plausible
extremes of this fact? Rank by swing, not by how easy it is to research. The easiest
candidate is rarely the decisive one; if it were, someone would already have settled it.

Spend real effort on the top one. One well-chosen fact beats six cheap ones.

### 3. Where decisive facts hide, by kind of question

| The question is about... | Look here first |
|---|---|
| A public company's model | The segment the company does NOT break out, and the metric its own stated thesis depends on. Track the thesis metric across every period disclosed, not just the latest |
| A market you are entering | The denominator nobody states. Ratios hide inside totals: revenue as a share of the flow it intermediates, cost per unit against the price of the unit |
| A pricing decision | What the buyer already spends on this problem today, in money and in hours. Competitor list price is an anchor, never this |
| A new product or club | Whether someone is already doing it. "Nobody does this" is a claim to falsify with a search, not a premise to build on |
| An operating model | The single cost that scales with volume and is not under your control |
| Any plan with a growth story | Whether the growth rate is the market's or the company's. Growing at half the category rate while calling it growth is the most common disguised failure |

### 4. Trend, not snapshot

Most decisive facts are visible only across periods. One quarter of a metric is a data
point; four periods of the same metric flat against a thesis that required it to rise is
a finding. Whenever a source publishes a series, read the series.

### 5. Absence of evidence is a finding with a specific name

If you searched and found nothing, that is `unknown` with the search recorded — never a
fact. Write what you looked for, where, and what would settle it. "No competitor found"
after one search round is a hypothesis to validate, not a moat.

## Per-route prompts

**FULL-PLAN.** What single fact would make an investor decline in the first five minutes?
What does this business need to be true that nobody has checked? Is anyone already doing
this, and if so at what price?

**MODULE (sizing).** Which step of the chain, if wrong by 2x, moves the answer most — and
is it sourced or assumed? What population does the base actually count, and who does it
miss?

**MODULE (pricing).** What does the buyer spend on this problem today? What is the
combined bill this price joins, rather than the price in isolation?

**EVALUATE.** What is the company's own stated thesis, and is the metric it depends on
actually moving? Which disclosure is missing, and what does the choice to omit it imply?
What is the denominator that makes the margin look different?

## What goes in the deliverable

The decisive fact leads. It appears in the first screen of the document, in plain
language, with its provenance — before the score, before the tag table, before the
artifact list. Those are support; this is the argument.

If the hunt came up empty, say so with the same prominence: what you looked for, why it
matters, and the cheapest way to settle it. An honest "the fact that decides this is
still unknown, here is how to get it" is a strong opening. A confident plan that never
asked the question is not.

## Handoffs

- `/sat` for adversarial challenge once the candidate is named (What If, premortem).
- `references/research.md` before sourcing anything public — the hunt does not suspend
  the source hierarchy or the two-source rule.
- `references/scenarios.md` when the decisive fact is a driver: solve for the value where
  the verdict flips instead of arguing about the level.
