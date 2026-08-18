# Phase 1 — FRAME: the interview protocol

Distilled from the McKinsey problem-solving framework (see the `problem-solving` skill
for full depth) and ai-analyst's question-framing agent. The goal of this phase is to
make sure the expensive part — the analysis — answers a question worth answering.

## Why frame first

Most bad analyses are correct answers to the wrong question. "Churn went up 2pp" is an
observation; the user's real question is usually "should I spend engineering time on
retention or acquisition next quarter?". If you don't know the decision, you can't know
which numbers matter, what precision is needed, or when to stop.

## The five questions

Ask these conversationally, not as a form. Skip any the user's prompt already answers.

1. **The real question.** "If this analysis works perfectly, what will you know that you
   don't know now?" Push past the metric to the decision. Use the Question Ladder:
   Goal → Decision → Metric → Hypothesis.
2. **The actor.** Who acts on the answer, and what would they do differently? An analysis
   for a CFO deciding budget needs different denominators than one for a PM fixing a
   funnel.
3. **The denominator of "big".** What baseline turns a number into a judgment? 500 lost
   customers is a crisis for a 5k-customer business and noise for a 5M one. Get the
   sizing denominator now — Phase 5 needs it.
4. **Falsifiable hypotheses.** 2-4 statements in the form "We hypothesize [claim]. If
   true, we should see [pattern]; if false, [other pattern]." If true and false look the
   same in the data, the hypothesis is not testable — rewrite it. Generate hypotheses
   across categories so the analysis doesn't tunnel: product change, technical issue,
   external factor, mix shift.
5. **The belief to beat.** What does the user currently think is happening, and what
   evidence would change their mind? This calibrates how strong the validation in
   Phase 4 must be — and warns you when you're about to confirm a favorite hypothesis
   (that's when the CHALLENGE phase matters most).

## Problem statement

Compress the answers into one SMART problem statement:

> Determine whether [metric change] in [population, period] is driven by [candidate
> causes], and size the impact of addressing it, to inform [decision] by [actor].

## Mini issue tree

For open questions ("where are we losing money?"), build a 3-5 branch MECE tree before
analyzing, and prioritize branches by impact × feasibility (can this data even answer
it?). Present the ranked candidates to the user and let them pick — or in solo mode,
pick the top branch and say so. Check feasibility against the actual files: a branch
that needs data you don't have is a tracking gap to report, not a dead end to hide.

## Vague-question protocol

When the ask is "here's the data, tell me what matters":

1. Profile first (Phase 2) — the data's shape suggests the questions.
2. Propose the top 3 questions this data can actually answer, ranked by likely business
   impact × feasibility, each with the decision it would inform.
3. Checkpoint with the user; in solo mode, analyze the top-ranked question and note the
   other two as follow-ups.

## Solo mode

The checkpoint exists to catch misframing early, not to create a dependency. If the user
is unavailable or their prompt already contains the answers: write the problem statement
and hypotheses anyway, mark each inferred item `[ASSUMED]` in findings.md, and proceed.
Surface all `[ASSUMED]` items prominently in the final report so the user can correct
them cheaply.
