---
name: design-shotgun
description: |
  Visual design brainstorming via AI-generated variants. Generates multiple distinct design
  directions in parallel, opens a side-by-side comparison board, collects structured feedback
  with ratings and remix specs, then iterates. Use whenever the user says "explore designs",
  "show me design options", "visual brainstorm", "design variants", "I don't like how this
  looks", or wants to see what a screen *could* look like. Proactively invoke when the user
  describes a UI feature but hasn't yet seen what it could look like, or when they're stuck
  on visual direction and need divergent options to react to.
---

You are running a visual design exploration. Generate N distinct directions in parallel,
show them to the user, collect feedback, iterate. This requires an AI mockup-generation
tool (the gstack `design` CLI, or any equivalent image-generation tool you can drive from
the command line). If you don't have one, fall back to writing HTML wireframes.

## Step 0: Session detection

Check for prior design exploration sessions for this project (you choose where to persist
them — pick a stable per-project directory and use it consistently). If previous sessions
exist, show a summary and ask:

> "Previous design explorations for this project:
> - [date]: [screen] — chose variant [X], feedback: '[summary]'
>
> A) Revisit — reopen the comparison board to adjust your choices
> B) New exploration — start fresh
> C) Something else"

If A: regenerate the board from existing variant PNGs and resume the feedback loop.
If B: proceed to Step 1.

If no prior sessions, show the first-time message:

*"This is design-shotgun — your visual brainstorming tool. I'll generate multiple AI
design directions, open them side-by-side in your browser, and you pick your favorite.
You can run this anytime to explore design directions for any part of your product."*

## Step 1: Context gathering

When invoked from another skill (e.g. a design-plan-review), the caller may have already
pre-filled context. Check for a passed-in design brief; if set, skip to Step 2.

When standalone, gather context for a proper design brief.

### Required context (5 dimensions)

1. **Who** — who is the design for? (persona, audience, expertise level)
2. **Job to be done** — what is the user trying to accomplish on this screen?
3. **What exists** — what's already in the codebase? (existing components, patterns)
4. **User flow** — how do users arrive at this screen and where do they go next?
5. **Edge cases** — long names, zero results, error states, mobile, first-time vs power user

### Auto-gather first

```bash
cat DESIGN.md 2>/dev/null | head -80 || echo "NO_DESIGN_MD"
ls src/ app/ pages/ components/ 2>/dev/null | head -30
```

If `DESIGN.md` exists, tell the user: *"I'll follow your design system in DESIGN.md by
default. If you want to go off the reservation on visual direction, just say so —
design-shotgun will follow your lead, but won't diverge by default."*

### Check for a live site (for the "I don't like THIS" use case)

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "NO_LOCAL_SITE"
```

If a local site is running AND the user said something like "I don't like how this looks,"
screenshot the current page and use an *evolve-from-current* prompt instead of generating
fresh — that gives the model the existing design as a starting point.

### Ask for what's missing

Pre-fill from inferred context, then ask for the gaps in **one** question:

> "Here's what I know: [pre-filled context]. I'm missing [gaps].
> Tell me: [specific questions].
> How many variants? (default 3, up to 8 for important screens)"

Two rounds of context gathering MAX, then proceed with what you have and note assumptions.

## Step 2: Taste memory

If prior approved variants exist for this project, read them and extract patterns from
what the user has actually approved in past sessions:

- Which fonts get approved repeatedly?
- Which colors / palettes?
- Which layouts / aesthetics?
- What did they explicitly reject?

Include these as a bias in the design brief: *"Based on N prior sessions, this user's
taste leans toward: fonts [top-3], colors [top-3], layouts [top-3]. Bias generation
toward these unless the user explicitly requests otherwise. Avoid their strong
rejections: [top-3 rejected]."*

**Conflict handling:** if the current request contradicts a strong persistent signal
(e.g., "make it playful" when prior approvals strongly prefer minimal), flag it: *"Note:
your taste profile strongly prefers minimal. You're asking for playful this time — I'll
proceed, but want me to update the taste profile, or treat this as a one-off?"*

## Step 3: Generate variants

### 3a. Concept generation

Before any API calls, generate N **text concepts** describing each variant's design
direction. Each concept should be a distinct creative direction, not a minor variation.
Present as a lettered list:

```
I'll explore 3 directions:

A) "Name" — one-line visual description
B) "Name" — one-line visual description
C) "Name" — one-line visual description
```

Draw on DESIGN.md, taste memory, and the user's request to make each concept distinct.

**Anti-convergence directive (hard requirement):** Each variant MUST use a different
font family, color palette, and layout approach. If two variants look like siblings —
same typographic feel, overlapping color temperature, comparable layout rhythm — one
of them failed. Regenerate the weaker one with a deliberately different direction.

Concrete test: if someone could swap the headline text between two variants without
noticing, they're too similar. Variants should feel like they came from three different
design teams, not the same team at three different coffee levels.

### 3b. Concept confirmation

Before spending API credits, confirm:

> "These are the {N} directions I'll generate. Each takes ~60s, but I'll run them all
> in parallel so total time is ~60 seconds regardless of count."

Options:
- A) Generate all {N} — looks good
- B) I want to change some concepts (tell me which)
- C) Add more variants
- D) Fewer variants

Max 2 rounds of concept iteration before generation.

### 3c. Parallel generation

Launch N parallel subagents (or N parallel CLI invocations of your mockup tool), one per
variant. Each agent should:

1. Call the mockup generator with the variant-specific brief.
2. If a rate-limit error occurs, wait 5 seconds and retry. Up to 3 retries.
3. If the output file is missing or empty after the command succeeds, retry once.
4. Run a quality check (vision-model gate, if your tool supports it).
5. Report `VARIANT_X_DONE`, `VARIANT_X_FAILED`, or `VARIANT_X_RATE_LIMITED`.

**Sandboxed output dirs:** some sandbox restrictions block direct writes to user
directories. If that happens, write to `/tmp/` first then copy to the final location.

### 3d. Results

After all agents complete:

1. Read each generated PNG inline (Read tool) so the user sees all variants at once.
2. Report: "All {N} variants generated in ~{actual time}. {successes} succeeded,
   {failures} failed."
3. For any failures: report explicitly with the error. Do NOT silently skip.
4. If zero variants succeeded: fall back to sequential generation, showing each as it
   lands. Tell the user: *"Parallel generation failed (likely rate limiting). Falling
   back to sequential."*

## Step 4: Comparison board + feedback loop

Create a side-by-side comparison board (HTML page with all variants, rating controls,
per-variant comment fields, overall direction field, and Submit/Regenerate/Remix buttons).
Serve it on a local HTTP server so the page can POST feedback back to a JSON file:

```bash
# example shape; replace with your tool
mockup-tool compare --images "variant-A.png,variant-B.png,variant-C.png" \
  --output "design-board.html" --serve &
```

Parse the port from the server output. Show the user the URL and ask them to interact:

> "I've opened a comparison board with the design variants:
> http://127.0.0.1:<PORT>/ — Rate them, leave comments, remix elements you like, and
> click Submit when done. Let me know when you've submitted (or paste your preferences
> here). If you click Regenerate or Remix on the board, tell me and I'll generate new
> variants."

**Do NOT ask "which variant do you prefer?" — the board IS the chooser.** Your prompt is
just the blocking wait mechanism.

### After the user responds

Check for feedback files next to the board:

- `feedback.json` — written on Submit (final choice)
- `feedback-pending.json` — written on Regenerate/Remix/More Like This

Expected shape:
```json
{
  "preferred": "A",
  "ratings": { "A": 4, "B": 3, "C": 2 },
  "comments": { "A": "Love the spacing" },
  "overall": "Go with A, bigger CTA",
  "regenerated": false
}
```

**If `feedback.json`:** The user submitted. Read `preferred`, `ratings`, `comments`,
`overall`. Proceed with the approved variant.

**If `feedback-pending.json`:**
1. Read `regenerateAction` (`"different"`, `"match"`, `"more_like_B"`, `"remix"`, or
   custom text).
2. If `"remix"`, read `remixSpec` (e.g. `{"layout":"A","colors":"B"}`).
3. Generate new variants using updated brief.
4. Rebuild board, reload it in the user's browser (POST to your server's `/api/reload`
   endpoint if available, otherwise tell the user to refresh).
5. Ask again with the same board URL. Repeat until `feedback.json` appears.

**If neither file:** The user typed preferences directly. Use their text as feedback.

**Fallback if the local server fails:** Show each variant inline using the Read tool,
then ask which they prefer and any feedback as plain prose.

## Step 5: Feedback confirmation

After receiving feedback, output a clear summary:

```
Here's what I understood from your feedback:

PREFERRED: Variant [X]
RATINGS: A: 4/5, B: 3/5, C: 2/5
YOUR NOTES: [full text of per-variant and overall comments]
DIRECTION: [regenerate action if any]

Is this right?
```

Confirm before saving.

## Step 6: Save & next steps

Save the approved choice as JSON (use a stable per-project location):

```json
{
  "approved_variant": "A",
  "feedback": "...",
  "date": "2026-01-15T12:00:00Z",
  "screen": "dashboard",
  "branch": "feature/new-dashboard"
}
```

If invoked from another skill: return the structured feedback for that skill to consume.

If standalone, offer next steps:

> "Design direction locked in. What's next?
> A) Iterate more — refine the approved variant with specific feedback
> B) Finalize — generate production HTML/CSS with /design-html
> C) Save to plan — add this as an approved mockup reference
> D) Done — I'll use this later"

## Important Rules

1. **Show variants inline before opening the board.** The user should see designs
   immediately in their terminal. The browser board is for detailed feedback.
2. **Confirm feedback before saving.** Always summarize what you understood and verify.
3. **Taste memory is automatic.** Prior approved designs inform new generations by
   default.
4. **Two rounds max on context gathering.** Don't over-interrogate. Proceed with
   assumptions when needed.
5. **DESIGN.md is the default constraint.** Unless the user says otherwise, variants
   stay within the documented design system.
6. **Anti-convergence is a hard rule.** If two variants look like siblings, regenerate
   one with a deliberately different direction.
