---
name: executive-deck-builder
description: >
  Most executive decks fail because the author renders before thinking — they jump into
  PowerPoint, end up with a pile of charts, and never land a recommendation. This skill
  fixes that by enforcing three phases (storyline → ghost deck → slides) using the
  McKinsey/consulting playbook: Pyramid Principle, MECE, action titles, and audience-fit
  storylining. Use this skill whenever the user asks for a "deck", "slides",
  "presentation", "executive summary slides", "board deck", "pitch deck", "leadership
  update", "steering committee deck", or wants to improve an existing deck. Also use it
  when the user has rough content (notes, a doc, data, bullets) and wants it turned into
  slides for senior audiences. ALWAYS trigger on slide creation or improvement requests
  for executives, board, C-level, steering committees, or clients — even if the word
  "deck" isn't used.
---

# Executive Deck Builder — McKinsey-style Presentations

## Why This Skill Exists

Most executive decks fail for the same reason: the author opens PowerPoint and starts dragging boxes before deciding what they want the audience to *do*. The result is a deck that looks polished but has no recommendation, no synthesis, and no through-line.

The fix is non-obvious but cheap: **separate the thinking from the rendering**. Spend the first 60–80% of your effort on the argument (storyline, action titles, ghost deck) and only then build slides. Done this way, the rendering becomes mechanical and the deck lands.

That's the entire point of this skill. The frameworks below are tools for that separation, not ceremony.

## Two Entry Points

Decide which one you're in before doing anything else:

### A) Building from scratch

The user has findings/data/notes and wants a new deck. Run them through the **three-phase workflow** below.

### B) Improving an existing deck

The user has a `.pptx` (or PDF) and wants it better. Run the **review-and-revise workflow** further down. Don't try to apply phases 1–3 from scratch on a deck that's already half-built.

If you're not sure which entry point applies, ask the user — it's a 10-second question that saves 10 minutes of confused work.

## When to Hand Off, Not Apply This Skill

Be honest about when this skill isn't the right tool. Hand off cleanly when:

- **The user hasn't done the analysis yet.** If they say *"help me think about whether to enter Brazil"* — they need analysis, not slides. Point them to the `problem-solving-coach` skill (issue trees, MECE problem structuring, hypothesis generation). Come back to this skill once they have findings.
- **The deck is for an informal team standup or a casual update.** McKinsey-style action titles and ghost decks are overkill. A simple bulleted summary or even a doc may be better.
- **The audience expects a narrative-heavy or visually rich style** (founder pitch decks, design-led product showcases, marketing keynotes). The McKinsey style optimizes for analytical density and decision speed; some audiences actively want storytelling, big imagery, and emotional pacing instead. Acknowledge the trade-off and adapt — or refer the user to a different style.
- **The user wants speaker notes, talk-tracks, or live presentation coaching as the primary output.** This skill stops at the deck file. Speaker notes can be added in Phase 3 but aren't the focus.

When you hand off, say so explicitly: *"What you actually need first is the analysis — let me bring in the problem-solving-coach skill."*

## Phase-Based Workflow (Building from Scratch)

For trivial decks (3–5 slides, low stakes, time-boxed), you can compress phases into one pass. For everything else — anything going to a board, C-level, or external client — run the full three-phase loop.

### Phase 1 — Storyline (the thinking)

Goal: produce a one-page logical structure of the entire deck before any slide exists.

1. **Anchor on a question and a decision.** Ask the user: *what is the audience meant to decide or do after this?* If they can't answer, the deck has no purpose yet — stop and clarify.
2. **Draft the Governing Thought.** One sentence. The recommendation that synthesizes the analysis. It must include both the answer and the "so what" — not just facts. (Read `references/pyramid-principle.md` for the full method and worked examples.)
3. **Draft 3–5 Key Lines.** Pillars supporting the Governing Thought. Must be MECE and each is itself a complete-sentence claim.
4. **Sketch supporting evidence under each Key Line** — what data, exhibit, or example proves it.
5. **Show the user the storyline as a tree** (ASCII or markdown outline) and confirm before moving on.

`references/pyramid-principle.md` is the most important reference — read it whenever the user gives you content for a new deck.

### Phase 2 — Ghost Deck (the structure)

Goal: produce a slide-by-slide outline with action titles only — no content, no design.

1. **Translate the storyline into a slide list.** Typically: Cover → Executive Summary → 1 section divider per Key Line → 2–4 evidence slides per Key Line → Recommendation → Appendix.
2. **Write the action title for every slide** (full declarative sentence stating the takeaway). Apply `references/action-titles.md`. Vary verbs so the deck doesn't read like a checklist.
3. **Sketch each slide's body in one line** — *"chart of X showing Y"*, *"two-column comparing A and B"*, *"table of segments with growth rates"*. Pick from the archetypes in `references/slide-types.md`.
4. **Read only the action titles top to bottom** — the headline test. If the storyline isn't audible from titles alone, rewrite them.
5. **Cut for the audience.** Apply `references/storylining.md` — drop anything that doesn't serve this audience's decision in this meeting.

Save the ghost deck as a markdown file (`storyline.md`) and show it to the user. Sign-off here is cheap; in `.pptx` it's expensive.

### Phase 3 — Slide Generation (the artifact)

Goal: produce the actual `.pptx` (and optional PDF) using the `pptx` skill.

1. **Read the `pptx` skill's SKILL.md first** — specifically `pptxgenjs.md` for creating from scratch. Follow its current best practices instead of inventing your own.
2. **Generate slides in 16:9 (13.33"×7.5" / 960×540 pt)** by default — the consulting standard.
3. **Apply the visual conventions in `references/style-guide.md`:** action title at top, content in body, footnote line, source line, page number. One sans-serif family. Restricted color palette.
4. **For data slides, build the chart programmatically** rather than describing one. Use python-pptx native shapes/charts or matplotlib → image insertion.
5. **Produce a PDF if asked** (LibreOffice headless conversion — see the `pptx` skill).

If the user asks for *just* the storyline (markdown), stop after Phase 2 and deliver `storyline.md`. The thinking is often the highest-leverage thing you can deliver — don't generate a `.pptx` unless they want one.

## Review-and-Revise Workflow (Improving an Existing Deck)

When the user already has a deck:

1. **Read the deck.** Use the `pptx` skill (`python -m markitdown deck.pptx` or `editing.md`) to extract every slide's title and body.
2. **Reconstruct the implicit storyline.** What's the Governing Thought as written? What are the Key Lines (read off section dividers or first slide of each cluster)? Write them out.
3. **Run the four diagnostics** (in order — most leverage to least):
   - **Action title test.** Read every title in order. Is it a coherent argument that ends in a recommendation? If many titles are topic labels (*"Q3 Performance"*) instead of takeaways (*"Q3 revenue beat plan by 8%"*), that's the first thing to fix. See `references/action-titles.md`.
   - **MECE check.** Do the Key Lines overlap? Are there gaps a smart skeptic would point out?
   - **Synthesis vs. summary check.** Is the Governing Thought a recommendation or just a list of findings restated?
   - **Audience fit.** Is anything in the deck the audience already knows? Anything missing they'd ask about? See `references/storylining.md`.
4. **Propose changes as a diff.** Show the user the existing titles and the proposed replacements side-by-side. Don't rewrite the whole deck silently.
5. **Apply the diff with `pptx`** — `editing.md` covers in-place edits.

Don't propose throwing the whole deck out unless the structure is genuinely broken. Most decks are 80% there and need title rewrites + reordering, not a rebuild.

## When to Read the Reference Files

You don't need to read all references for every request — use judgment:

- **Always read `references/pyramid-principle.md`** at the start of any new deck — it grounds the storyline.
- **Read `references/action-titles.md`** before writing any titles or running the action title test on existing titles.
- **Read `references/slide-types.md`** when sketching the ghost deck.
- **Read `references/style-guide.md`** before Phase 3 (visual rules) or when reviewing the visual quality of an existing deck.
- **Read `references/storylining.md`** when the user has lots of content and needs help cutting, or when checking audience fit.

## Defaults and Assumptions

Unless the user says otherwise:

- **Language**: English.
- **Audience**: senior executives — C-level, board, steering committee. Tone is decision-oriented and concise.
- **Aspect ratio**: 16:9.
- **Length**: 8–15 main-body slides + appendix. Push back gently if the user wants 40+ — that's almost always a sign the storyline isn't tight.
- **Style**: clean, minimal, McKinsey-adjacent. Sans-serif. No clipart. No drop shadows. Action titles, not topic labels.

These are defaults, not laws. Adapt when the user gives different constraints.

## How to Push Back

Part of the value of this skill is catching weak structure before it becomes a weak deck. When you spot one of these, name it and propose a fix in one sentence each:

- **Governing Thought is a summary, not a synthesis.** *"That's a finding, not a recommendation. Try framing it as the action you want them to take."*
- **Key Lines aren't MECE** (overlapping or gappy). *"Pillars 2 and 3 are saying the same thing in different words. Combine them and let's see what's missing."*
- **Title is a topic label, not an action title.** *"'Q3 Performance' is a label. The takeaway is 'Q3 revenue beat plan by 8%' — use that."*
- **Background-heavy deck.** *"Five slides of context and one of recommendation is inverted. Cut context to two slides; expand the recommendation."*
- **Mixed audiences.** *"This deck is trying to serve the board *and* the eng team. Pick one. Build a second deck for the other."*

Direct, not preachy. One sentence diagnosing, one sentencing the fix.

## Three Worked Examples (different shapes)

### Example 1 — Analytical deck (churn)

User: *"I have data showing our churn went up. Help me build a deck for the CEO."*

Storyline:
- *Question:* What is causing the churn increase and what should we do?
- *Governing Thought:* Churn rose 4 pts in Q3 because of onboarding friction in SMB; a 90-day overhaul fixes it and pays back in 2 quarters.
- *Key Lines:* (1) churn is concentrated in SMB first-60-days; (2) root cause is onboarding, not pricing or product; (3) a 90-day overhaul addresses the root cause and pays back fast.

Ghost deck (titles only):
1. *Q3 churn rose 4 pts; the cause is concentrated and fixable*
2. *SMB customers in their first 60 days drive 70% of new churn*
3. *Onboarding completion correlates with retention; price changes do not*
4. *NPS confirms onboarding — not product fit — is the friction*
5. *A 90-day overhaul fixes the three highest-friction steps*
6. *Payback is 2 quarters; a price cut would not pay back*
7. *Recommendation: approve the overhaul; kick off in 30 days*

### Example 2 — Strategic decision deck (market entry)

User: *"Board wants me to recommend whether to enter Brazil."*

Storyline:
- *Question:* Should we enter Brazil and how?
- *Governing Thought:* Enter Brazil now via partnership rather than direct, because the window closes in 6 months and partnership is 3x faster to revenue.
- *Key Lines:* (1) the market is large and growing fast; (2) two competitors will lock up partners within 6 months; (3) partnership beats direct on speed-to-revenue and risk-adjusted return.

Ghost deck (5 slides only — narrow purpose):
1. *Enter Brazil now via partnership; window closes in 6 months*
2. *Brazilian market is $4B and growing 18% CAGR*
3. *Two competitors are 3 months away from locking up the natural partners*
4. *Partnership reaches revenue in 9 months vs. 24 for direct entry, at 1/3 the capital*
5. *Approve partnership track; LOI by end of Q1*

### Example 3 — Status-and-ask deck (project update)

User: *"Quarterly project update for the steering committee — we're behind but we have a fix."*

Storyline:
- *Question:* What's the status and what do we need from the committee?
- *Governing Thought:* The project is 6 weeks behind due to a vendor delay; we recover the timeline with a $400K acceleration spend that the committee is asked to approve today.
- *Key Lines:* (1) where we are vs. plan; (2) what caused the delay and what we've already done; (3) the recovery plan and the ask.

Notice example 3 isn't pure analysis — it's a status update with a decision. Same skill, same frameworks, different shape.

## Common Slide Archetypes (cheat-sheet)

Full descriptions in `references/slide-types.md`. Most-used:

| Archetype | Use when |
|---|---|
| **Title slide** | First slide. Project name, audience, date. |
| **Executive summary** | Slide 2. Governing Thought as title; Key Lines as bullets. |
| **Section divider** | Marks each Key Line. Big number + Key Line text. |
| **Lead-in slide** | Action title + a single chart/table that proves it. The workhorse. |
| **Two-column compare** | Side-by-side options, before/after, current vs. target. |
| **Exhibit with call-outs** | Chart with annotated arrows pointing to the insight. |
| **Recommendation slide** | Penultimate. Restates Governing Thought + concrete next steps with owner/date. |

## Final Reminder

The biggest mistake when building decks is going straight to PowerPoint. Resist that. If the user is impatient, deliver Phase 1+2 as a markdown storyline first, then Phase 3 as a follow-up. They'll often realize the markdown is enough — and that's not failure, that's the skill working.
