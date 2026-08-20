---
research_sources: 0
confidence_level: LOW
stage: idea
mode: pre-revenue
slug: <slug>
route: <FULL-PLAN | MODULE>
language: <language of the user's request>
---

<!-- pitch-outline.md: the 10-slide pitch outline, text only.
     This file is delivered at the ROOT of bp_<slug>/, which is exactly where
     `bp.sh lint` looks, so the frontmatter above and the "Assumptions &
     Limitations" section at the bottom are load-bearing, not decoration. Keep
     both. A delivered outline that drops either one fails the skill's own lint.
     Frontmatter values stay bare (the linter reads the raw value):
     research_sources integer >= 0, the count of independent sources behind
     these slides; confidence_level HIGH | MEDIUM | LOW; stage idea |
     validating | building | revenue; mode pre-revenue | revenue. Copy these
     four from the plan's frontmatter so the two artifacts cannot disagree.

     This skill produces the text outline only. Rendering to an actual deck is
     the executive-deck-builder skill's job; hand this file to it. The ten-slide
     shape follows Guy Kawasaki's 10/20/30 rule (a pitch heuristic: 10 slides,
     20 minutes, 30-point font), adapted to this skill's evidence discipline.
     Every number on any slide must exist in the plan's Inputs & Sources table
     or a saved script artifact, and a headline number carries the arithmetic
     that builds it ("transaction 2,677 + ads 1,065 = revenue 3,742"), not the
     result alone; a slide may say "Unknown" and say what would settle it. That
     honesty is a feature in front of good investors.
     The decisive fact from Step 4 is the headline of whichever slide it
     belongs to — problem, market, model, or competition — not a footnote on
     it. Write in the language of the user's request; framework terms (TAM,
     SAM, SOM, ICP, LTV, CAC, GTM) stay in English. -->

# <company>: pitch outline

## Slide 1: Title

- <company>, <one-line what it is>
- <presenter, date, contact>

## Slide 2: Problem

- <the problem in the customer's words>
- <evidence it is real: tagged claim, not adjectives>

## Slide 3: Solution

- <what the product does and what it replaces>
- <why now: the trigger that makes this buildable or buyable today>

## Slide 4: Market (TAM / SAM / SOM)

- <bottom-up chain summary, pasted from market.json>
- <the som_revenue headline with its tag trail>

## Slide 5: Business model

- <who pays, for what, how much, how often; from the canvas>

## Slide 6: Product / underlying magic

- <demo pointer, screenshot list, or architecture in one line>
- <what is hard to copy; "nothing yet" plus the plan for it is honest>

## Slide 7: Go-to-market

- <first channel, first-100-customers motion, evidence targets>

## Slide 8: Competition

- <the alternatives grid; why the ICP picks you>

## Slide 9: Financials

- <projection headline from fa.sh artifacts; scenarios conservative / base / optimistic>
- <unit economics line, from fa.sh unit-economics output only>

## Slide 10: Team, traction, ask

- <who builds this and why them>
- <traction that is real today>
- <the ask: amount, runway, milestone it funds>

## Assumptions & Limitations

<!-- Frozen heading; the linter requires it (PT: "Premissas e Limitações",
     ES: "Premisas y Limitaciones" — translate with the rest of the document
     and the check still passes).
     This is not slide 11 and it is not presented. It is the backing that lets
     the ten slides above stay short, and it is the first thing a serious
     investor asks for after the meeting. When this outline accompanies a plan,
     mirror the plan's Part 13 instead of inventing new entries: an assumption
     load-bearing enough to reach a slide belongs in both, worded the same way.
     One row per slide that rests on something unproven. Unknowns render as
     "Unknown" — never blank, never zero, never a plugged average. -->

| # | Slide | Assumption or unknown | Tag | Basis / evidence that would settle it |
|---|---|---|---|---|
| 1 | <slide n> | <assumption or unknown> | <assumption / unknown> | <basis, or the data that would resolve it> |

<limitations: which slides rest on assumptions rather than evidence, and what
this outline does not claim>
