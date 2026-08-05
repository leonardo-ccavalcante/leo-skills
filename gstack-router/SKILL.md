---
name: gstack-router
description: |
  Smart entry point for the 32-skill gstack suite (office-hours, plan-ceo-review,
  plan-eng-review, plan-design-review, plan-devex-review, autoplan, design-consultation,
  design-shotgun, design-html, design-review, review, qa, qa-only, investigate, ship,
  land-and-deploy, document-release, document-generate, retro, canary, benchmark, cso,
  codex, pair-agent, careful, freeze, guard, unfreeze, open-gstack-browser, setup-deploy,
  setup-gbrain, gstack-upgrade). Given a user need, picks the right skill or chain of
  skills, explains why using a MECE issue tree (McKinsey) + chain-of-thought decomposition
  + Key Assumptions Check (CIA Structured Analytic Techniques), communicates in Pyramid
  Principle style, then bootstraps by invoking the first skill in the chain. Use this
  skill whenever the user says "which gstack skill", "what should I use", "where do I
  start", "help me pick a skill", "route me", "what's next", describes a multi-phase
  software task without naming a specific skill (e.g. "I have an idea and want to ship
  it", "I just finished building X what now", "it broke in prod help"), or invokes
  /gstack-router. Proactively invoke when the user describes a workflow spanning two or
  more lifecycle phases (idea→plan→build→ship→deploy→monitor→retro). DO NOT use when
  the user has already named a specific gstack skill (e.g. "run /qa") — call that skill
  directly. DO NOT use for non-gstack tasks.
---

# GStack Router

You orchestrate 32 gstack skills. Your job: take a user need, pick the smallest
useful chain of skills, justify the pick using the protocol below, then bootstrap
the chain by invoking the first skill. You do **not** invoke later skills — their
preconditions depend on the previous step finishing successfully, so the user (or
the next router call) advances the chain.

## Why this protocol exists

The 32 skills cover the full software lifecycle, and most real requests span
multiple phases. Picking the right skill by keyword match alone is brittle: "ship
this" might mean `/ship` (PR creation) or `/land-and-deploy` (merge + deploy) or
even `/setup-deploy` (no platform configured yet). The protocol forces an
auditable trail — classify → decompose → verify → communicate → bootstrap — so
the routing is defensible and the user can interrupt early if the chain is wrong.

## The 5-step routing protocol

### Step 1 — Classify (MECE issue tree)

Place the user's situation in exactly one branch of this tree. Each leaf maps to
1–3 candidate skills. Cross-cutting safety modes apply on top of any branch.

```
1. PRE-BUILD (no code yet, exploring whether to build)
   1a. Idea-stage diagnostic        → /office-hours
   1b. Plan exists, needs review    → /plan-ceo-review, /plan-eng-review,
                                      /plan-design-review, /plan-devex-review
   1c. Plan exists, auto-pipeline   → /autoplan

2. DESIGN (visual identity / UI decisions)
   2a. No design system yet         → /design-consultation
   2b. Need to explore visuals      → /design-shotgun
   2c. Approved mockup → HTML       → /design-html
   2d. Audit existing UI for slop   → /design-review

3. BUILD (writing or fixing code)
   3a. Bug reported, root cause TBD → /investigate
   3b. Generic implementation       → (no skill — direct coding)

4. VERIFY (does it work?)
   4a. Test in browser + auto-fix   → /qa
   4b. Test only, never fix         → /qa-only
   4c. Pre-merge diff sanity        → /review
   4d. Performance check            → /benchmark

5. SHIP (commit, PR, merge)
   5a. Branch → PR ready to merge   → /ship
   5b. PR ready → prod              → /land-and-deploy

6. POST-SHIP
   6a. Watch prod after deploy      → /canary
   6b. Update docs after merge      → /document-release
   6c. Generate missing docs        → /document-generate
   6d. Weekly retrospective         → /retro

7. SECURITY (any phase)
   7a. Security audit / threat model → /cso
   7b. Adversarial code review      → /codex

8. SETUP (one-time)
   8a. Deploy platform              → /setup-deploy
   8b. gstack knowledge base        → /setup-gbrain
   8c. Upgrade gstack itself        → /gstack-upgrade

9. COLLABORATION (any phase)
   9a. Pair a remote AI agent       → /pair-agent
   9b. Visible browser session      → /open-gstack-browser

CROSS-CUTTING — SAFETY (compose with any branch above)
   S1. Warn before destructive cmds → /careful
   S2. Restrict edits to one dir    → /freeze (clear with /unfreeze)
   S3. Both at once                 → /guard
```

This tree is MECE: every situation lands in exactly one leaf (safety modes
compose on top, they don't replace the leaf). If a request seems to span two
leaves, that's the signal you have a *chain*, not a single skill — move to
Step 2.

### Step 2 — Decompose (chain-of-thought)

Most real requests span phases. Write the chain out as a step-by-step plan with
the *why* of each step before naming the skill. This makes the chain auditable
rather than rote.

Reasoning template:
1. What state is the user in *right now*? (which leaf in Step 1)
2. What state do they want to reach? (terminal leaf)
3. What states sit between, in order? Each transition = one skill.
4. For each skill in the chain, name the **exit condition** that ends its turn
   (e.g. "/ship exits when the PR URL is printed").

Keep chains short. 2–5 skills is typical. If you're writing a 7-skill chain,
stop and ask whether some steps can be batched (`/autoplan` collapses four
plan-review skills) or skipped.

### Step 3 — Verify (Key Assumptions Check)

Before recommending the chain, surface every assumption it bakes in. For each,
mark `[CONFIRMED]`, `[LIKELY]`, or `[UNSURE — needs check]`. Use only the
evidence visible in the conversation; don't invent confirmations.

Common assumptions to test:
- The feature is already implemented (chain starts at `/qa`, not `/investigate`).
- Tests exist (chain uses `/qa` which auto-fixes vs `/qa-only` which reports).
- Deploy platform is configured (`/land-and-deploy` requires `/setup-deploy`
  output to exist first).
- The PR exists (`/land-and-deploy` assumes `/ship` already ran).
- The user wants automated decisions (`/autoplan` vs four interactive reviews).

If any assumption is `[UNSURE]`, do one of:
- Ask the user one focused question.
- Swap a skill into the chain that resolves it (e.g. prepend `/setup-deploy`).
- Flag the assumption explicitly in the output and let the user decide.

Then run a brief Analysis of Competing Hypotheses (ACH) when two skills both
fit the leaf. Common pairs:

| Decision | Pick A when… | Pick B when… |
|---|---|---|
| `/qa` vs `/qa-only` | User wants bugs fixed in the same loop | User wants a triage report, will decide later |
| `/design-consultation` vs `/design-shotgun` | No design system exists yet — set the foundation | Design system exists, need visual options for a screen |
| `/ship` vs `/land-and-deploy` | Branch is local, no PR yet | PR exists, CI green, ready to merge |
| `/document-release` vs `/document-generate` | Just shipped — sync docs to the diff | Greenfield docs from scratch |
| Four reviews vs `/autoplan` | User wants control on each pass | User wants speed and is OK with auto-decisions |

### Step 4 — Communicate (Pyramid Principle)

Output structure, in this exact order:

1. **Governing thought** — one sentence: *"Start with `/X` because Y."*
2. **Supporting reasons** — 1–3 key-line statements (one per line) that hold up
   the governing thought.
3. **The chain** — numbered list. Each entry:
   - `N. /<skill>` — *one-line purpose*. **Exit when:** *trigger that ends it*.
4. **Assumptions surfaced in Step 3** — bullet list, marked `[CONFIRMED]`,
   `[LIKELY]`, `[UNSURE]`. Only show this section if any are `[LIKELY]` or
   `[UNSURE]`.

Skip preamble. The user reads this top-down: they get the recommendation in
one line, the rationale in three, the execution plan as a list, and the
caveats last.

### Step 5 — Bootstrap

After printing the output from Step 4, invoke the **first** skill in the chain
via the `Skill` tool. Don't invoke later skills — their preconditions depend on
the previous step finishing. The user or agent advances the chain by
re-invoking this router or calling the next skill directly.

**Skip Step 5 when:**
- The user asked an *informational* question ("which skill would I use for X?",
  "what does /ship do?") — they want to know, not to do.
- The user explicitly said "just recommend, don't run" or similar.
- The first skill in the chain requires user setup (e.g. `/setup-deploy`
  expects credentials the user hasn't supplied yet).

In any of those cases, output the recommendation only and stop.

## When NOT to route

This skill is the wrong choice when:
- The user named a specific gstack skill — call that skill directly, don't
  re-route.
- The task isn't gstack-shaped (general coding, debugging without the
  systematic-debugging framing, writing prose, math, etc.) — use the
  appropriate non-gstack skill or just answer.
- The user is mid-conversation inside another skill and asks a tangential
  question — answer in-place; don't break flow with a routing exercise.

## When in doubt — load the long reference

If two leaves of the MECE tree both seem to apply, or the user's situation
doesn't map cleanly to any leaf, read `references/skill-map.md` for the
detailed per-skill catalog (one-paragraph purpose + "use when" + "don't use
when" + "common next skill" for each of the 32). For situations that match
one of the five canonical patterns (idea-to-ship, post-build verify, prod
hotfix, prod-touch with safety, full design pipeline), read
`references/common-chains.md` for the worked example.

Both files only need to be read when the short-term tree above is
insufficient — load lazily.

## Example application of the full protocol

> **User:** "I just finished building the auth flow on this branch. What now?"

**Step 1 (Classify):** State = "feature built, not yet verified" → leaf 4a (`/qa`).

**Step 2 (Decompose):** Target state = "feature live in prod, monitored, documented."
Transitions:
1. Verify works in browser → `/qa`
2. Pre-merge diff sanity → `/review`
3. PR + push → `/ship`
4. Merge + deploy → `/land-and-deploy`
5. Watch prod → `/canary`
6. Update docs → `/document-release`

**Step 3 (Verify):**
- `[LIKELY]` Auth UI exists in the browser (user said "finished building").
- `[UNSURE]` Deploy platform configured — if not, prepend `/setup-deploy`.
- `[CONFIRMED]` There's a branch (user said "on this branch").

**Step 4 (Communicate):**

> Start with `/qa` because the riskiest gap right now is whether auth actually
> works end-to-end in a real browser — tests can pass while real users hit
> redirect loops.
>
> - `/review` catches the structural issues `/qa` won't (SQL safety, LLM trust
>   boundaries) before the PR opens.
> - `/ship` and `/land-and-deploy` handle the PR-to-prod path; splitting them
>   keeps each commit auditable.
> - `/canary` and `/document-release` close the loop so post-deploy regressions
>   surface fast and docs don't drift.
>
> Chain:
> 1. `/qa` — test + auto-fix bugs. **Exit when:** all critical/high bugs fixed,
>    re-verified, regression tests added.
> 2. `/review` — pre-landing structural review. **Exit when:** safe issues
>    fixed, risky ones called out for user decision.
> 3. `/ship` — commits, push, PR. **Exit when:** PR URL printed.
> 4. `/land-and-deploy` — merge + deploy + canary verify. **Exit when:** prod
>    healthy.
> 5. `/canary` — sustained watch. **Exit when:** baseline window passes clean.
> 6. `/document-release` — sync docs to the diff. **Exit when:** docs reflect
>    what shipped.
>
> Assumptions to confirm:
> - `[UNSURE]` Deploy platform configured. If not, prepend `/setup-deploy`
>   before step 4.

**Step 5 (Bootstrap):** Invoke `/qa` via the `Skill` tool.

## Note on the four borrowed methodologies

This skill explicitly uses four methodology skills the user named:

- `/skill-creator` — informs the SKILL.md shape (lean, pushy description,
  imperative voice, explain WHY).
- `/problem-solving` (McKinsey) — Step 1 (MECE issue tree) and Step 4
  (Pyramid Principle output).
- `/prompt-reasoning` — Step 2 (chain-of-thought decomposition).
- `/sat` (CIA Tradecraft Primer) — Step 3 (Key Assumptions Check + ACH).

Each step cites which methodology it borrows so the routing logic is portable
to other skill suites.
