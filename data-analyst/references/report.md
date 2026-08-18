# Phase 6 — REPORT: structure, prose, deliverables

## Structure — Pyramid Principle

The report answers the question first and proves it after. Template:

```markdown
# [Title: the answer, not the topic]

## Recommendation
[Governing Thought: one or two sentences that answer "what should we do / believe".
A synthesis, not a summary — "churn rose because our acquisition mix shifted to a
high-churn channel; fixing partner onboarding is worth ~$X/yr" — never "we analyzed
churn and found several patterns".]

## Key findings
### 1. [Key Line — a claim, stated as a sentence]
[Evidence: the computed numbers, with source citations (file, column, period, notebook
cell). Table if it helps. Chart only if it earns its place.]
### 2. ...
### 3. ...
[Max 3. If removing one doesn't weaken the Recommendation, cut it.]

## Sizing
[Impact model written out with every component tagged data-backed or assumption;
conservative/base/aggressive range; break-even; guardrail verdict.]

## How this was verified
[2-3 sentences: profiling, competing explanations tested, tie-out result, what changed
because of validation. Include the [ASSUMED] items from solo-mode decisions.]

## What would change this conclusion
[The strongest counter-case and the evidence that would confirm it; next data to collect.]
```

Storyline before storytelling: know the audience (a CFO wants sizing and confidence; a
PM wants the driver and the fix) and order the Key Lines for that reader.

## Prose — humanizer rules (distilled from the humanizer skill)

Reports read like a sharp human analyst wrote them. Hard bans:

- **No em dashes or en dashes** (— –). Replace with period, comma, colon, or parentheses.
- **No inflated significance**: "pivotal", "crucial", "underscores", "highlights the
  importance", "testament to", "marks a shift", "evolving landscape".
- **No fake-depth "-ing" tails**: "...showcasing the team's commitment", "...reflecting
  broader trends". State the fact; stop.
- **No rule-of-three padding** ("innovation, inspiration, and insights") and no false
  ranges ("from X to Y" where X and Y aren't on a scale).
- **Plain copulas**: "is/are/has", not "serves as / stands as / boasts".
- **Active voice** where the actor matters: "duplicates inflated the March count", not
  "the count was inflated".
- **No bold-header bullet lists** ("**Performance:** improved...") — write sentences.
- **No generic upbeat endings** ("the future looks bright"), no signposting ("let's dive
  in"), no hedging stacks ("could potentially possibly").
- Vary sentence length; compress the dull parts; specifics over abstractions.

Two things style editing never touches: **numbers** (exact as computed, with their
units and periods) and **provenance citations**. If the `humanizer` skill is installed,
run it in embedded mode on report.md as the final pass; these bans still apply to the
draft so the pass has little to fix.

## Charts

Only when a chart carries the argument better than a sentence or small table: trends,
distributions, funnel drops, before/after mix. Every chart gets an action title (the
takeaway, not the axis description: "Partner channel churns 3x organic", not "Churn by
channel"). Label directly, drop legends where possible, no decorative color. Save to
`outputs/` as PNG next to the CSV of its underlying data.

## Deliverables contract

The analysis is not delivered until the user has the files in hand:

1. `report.md` — the report itself.
2. `analysis_<slug>.ipynb` — executed, outputs embedded, re-runnable. Offer to open it:
   `jupyter lab analysis_<slug>.ipynb`.
3. `outputs/*.csv` — the computed tables behind each Key Line (and each chart).

In Claude Code, send these with the file-sharing tool (SendUserFile) rather than only
citing paths. DIRECTED mode: same contract (result + notebook/script + output CSV).
QUICK mode: the answer with citation is enough; offer the snippet on request.
