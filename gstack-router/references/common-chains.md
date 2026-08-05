# Common Skill Chains — Worked Examples

Five canonical patterns. Each exercises the full 5-step protocol (classify,
decompose, verify, communicate, bootstrap) end-to-end. Use them as templates
when the user's situation matches one of these shapes — copy the structure,
swap in their specifics, then bootstrap by invoking the first skill.

---

## Pattern 1 — "I have an idea and want to ship it"

**User says:** *"I want to build X. Where do I start?"* / *"I have an idea
but no code yet."* / *"From zero to shipped."*

**Step 1 (Classify).** Leaf 1a (idea-stage diagnostic) — no code exists.

**Step 2 (Decompose).** Idea → design doc → reviewed plan → implementation →
verified → shipped → deployed → monitored → documented.

**Step 3 (Verify).**
- `[LIKELY]` User actually wants to build (not just thinking aloud) — if not,
  stop after `/office-hours`, design doc is the deliverable.
- `[UNSURE]` Will require UI — if yes, `/design-consultation` slot in after
  the plan reviews.
- `[UNSURE]` Deploy platform configured — if not, prepend `/setup-deploy`
  before step 8.

**Step 4 (Communicate).**

> Start with `/office-hours` because before any code, the right question is
> *"is this worth building?"*. The forcing questions kill bad ideas in 30
> minutes and produce a design doc that feeds every subsequent skill.
>
> - `/office-hours` is the only skill that produces a design doc grounded in
>   demand evidence, not just feature specs.
> - The plan reviews (or `/autoplan`) catch the strategic and execution
>   mistakes that are cheap to fix in writing and expensive in code.
> - `/ship` → `/land-and-deploy` → `/canary` → `/document-release` is the
>   standard shipping spine; running them as a chain keeps each commit
>   small enough to bisect later.
>
> Chain:
> 1. `/office-hours` — design doc. **Exit when:** the doc names problem,
>    user, narrowest wedge, and one alternative seriously considered.
> 2. `/autoplan` — sequential CEO/design/eng/devex with auto-decisions.
>    **Exit when:** all four passes complete with no open questions.
> 3. *(implement — no skill; direct coding)*
> 4. `/qa` — verify in browser + auto-fix. **Exit when:** no critical/high
>    bugs remain.
> 5. `/review` — pre-merge structural review. **Exit when:** structural
>    issues fixed or flagged.
> 6. `/ship` — atomic commits + PR. **Exit when:** PR URL printed.
> 7. `/land-and-deploy` — merge + deploy. **Exit when:** prod healthy.
> 8. `/canary` — sustained watch. **Exit when:** baseline window passes.
> 9. `/document-release` — sync docs. **Exit when:** docs reflect diff.

**Step 5 (Bootstrap).** Invoke `/office-hours`.

---

## Pattern 2 — "I just finished building X, what now?"

**User says:** *"Done with the auth flow."* / *"Feature is built, what's
next?"* / *"Ready to ship."*

**Step 1 (Classify).** Leaf 4a (verify in browser + fix).

**Step 2 (Decompose).** Built → verified → reviewed → PR → deployed → watched
→ documented.

**Step 3 (Verify).**
- `[LIKELY]` Feature actually works in dev (user said "finished") — `/qa`
  will confirm or surface bugs.
- `[UNSURE]` Tests exist — if not, `/qa` will add regression tests as it
  fixes.
- `[UNSURE]` Deploy platform configured — check before step 4.

**Step 4 (Communicate).**

> Start with `/qa` because the highest-information step now is whether the
> feature actually works end-to-end in a real browser — tests can lie, real
> users don't.
>
> - `/review` catches structural issues `/qa` can't see (SQL safety, LLM
>   trust, scope drift).
> - Splitting `/ship` and `/land-and-deploy` keeps the merge gate auditable
>   — green CI is a precondition for deploy, not a side effect of it.
> - `/canary` + `/document-release` close the loop so regressions and
>   doc-drift don't pile up after merge.
>
> Chain:
> 1. `/qa` — verify + fix. **Exit when:** all critical/high bugs fixed.
> 2. `/review` — structural review. **Exit when:** issues fixed or flagged.
> 3. `/ship` — PR. **Exit when:** PR URL printed.
> 4. `/land-and-deploy` — merge + deploy. **Exit when:** prod healthy.
> 5. `/canary` — watch. **Exit when:** baseline clean.
> 6. `/document-release` — sync docs. **Exit when:** docs match diff.

**Step 5 (Bootstrap).** Invoke `/qa`.

---

## Pattern 3 — "It broke in prod, help"

**User says:** *"Prod is throwing 500s."* / *"It worked yesterday, broken now."*
/ *"Customer says X is broken."*

**Step 1 (Classify).** Leaf 3a (bug, root cause TBD) + cross-cutting safety
(touching prod).

**Step 2 (Decompose).** Investigate → reproduce → fix → verify → ship hotfix
→ deploy → watch → retro.

**Step 3 (Verify).**
- `[LIKELY]` There's a real symptom (error, broken behaviour) — `/investigate`
  starts from symptom.
- `[UNSURE]` Cause is in code (vs. config, infra, third-party) — `/investigate`
  separates these.
- `[CONFIRMED]` Blast radius is high (production) — engage `/guard` so a
  fix-in-haste can't make it worse.

**Step 4 (Communicate).**

> Start with `/guard` because the riskiest thing about a prod incident isn't
> the bug itself — it's the second mistake made while fixing the first.
> Locking edit scope + warning on destructive commands narrows the blast
> radius before debugging starts.
>
> - `/investigate` enforces root-cause-before-fix, which prevents the classic
>   "fix the symptom, ship, then it re-occurs" loop.
> - `/qa` proves the fix actually works in a browser, not just in tests.
> - `/retro` after the dust settles converts the incident into a learning
>   rather than just a closed ticket.
>
> Chain:
> 1. `/guard` — restrict edits + warn on destructive. **Exit when:** boundary
>    set, you tell user "guard active."
> 2. `/investigate` — root cause. **Exit when:** root cause named, fix
>    proposed.
> 3. `/qa` — verify the fix. **Exit when:** original symptom gone, no
>    regressions.
> 4. `/ship` — hotfix PR. **Exit when:** PR URL printed.
> 5. `/land-and-deploy` — merge + deploy. **Exit when:** prod healthy.
> 6. `/canary` — sustained watch (longer than usual after an incident).
> 7. `/unfreeze` — release guard boundary. **Exit when:** confirmed.
> 8. `/retro` — capture the learning. **Exit when:** retro doc written.

**Step 5 (Bootstrap).** Invoke `/guard`.

---

## Pattern 4 — "I'm touching prod, be careful"

**User says:** *"About to run a migration on prod."* / *"Need to debug live."*
/ *"Working on the prod DB."*

**Step 1 (Classify).** Cross-cutting safety leaf (S3 if both bash + edits;
S1 if bash only; S2 if edit scope only).

**Step 2 (Decompose).** Lock safety → do task → release safety.

**Step 3 (Verify).**
- `[UNSURE]` Whether edits will be needed — if yes/maybe, `/guard`; if just
  bash, `/careful`.
- `[CONFIRMED]` Stakes are high — that's why the user invoked routing.

**Step 4 (Communicate).**

> Start with `/guard` because touching prod is the situation where pausing
> for confirmation has the highest expected value — one wrong rm or one
> wrong table-drop is unrecoverable.
>
> - `/careful` alone covers destructive bash; `/freeze` alone covers stray
>   edits. `/guard` does both, which is the right default when you don't yet
>   know what the task will need.
> - Putting the safety lock *before* the work means the protections are in
>   place from the first command, not added after the fact.
> - `/unfreeze` is the clean exit — leaving the boundary in place would block
>   legitimate edits in the next task.
>
> Chain:
> 1. `/guard` — destructive warnings + edit boundary. **Exit when:** boundary
>    set.
> 2. *(the user's actual task — could be `/investigate`, `/qa`, manual SQL,
>    a migration script, etc. Re-route if the task is itself multi-step.)*
> 3. `/unfreeze` — release the boundary. **Exit when:** confirmed.

**Step 5 (Bootstrap).** Invoke `/guard`.

---

## Pattern 5 — "I need a design system"

**User says:** *"Set up the visual identity."* / *"This needs a design system."*
/ *"Make it look professional."*

**Step 1 (Classify).** Leaf 2a (no design system yet).

**Step 2 (Decompose).** Design system → explore variants → implement → audit.

**Step 3 (Verify).**
- `[UNSURE]` Whether a `DESIGN.md` already exists — if it does, skip step 1
  and jump to `/design-shotgun`.
- `[LIKELY]` There are specific screens to design, not just brand — that's
  what `/design-shotgun` is for.
- `[LIKELY]` Implementation target is HTML — if it's React/Vue/native, adapt
  `/design-html` output accordingly.

**Step 4 (Communicate).**

> Start with `/design-consultation` because every later design decision is
> faster and more coherent once typography, color, spacing, and motion are
> set as a written design system, not just imagined per-screen.
>
> - `/design-shotgun` generates *divergent* options to choose between —
>   convergent decisions in isolation lead to AI slop.
> - `/design-html` is the bridge from approved variant to production code
>   without losing layout fidelity.
> - `/design-review` is the audit step after the UI is live — visual slop
>   is easier to spot side-by-side than alone.
>
> Chain:
> 1. `/design-consultation` — system + DESIGN.md. **Exit when:** DESIGN.md
>    written, preview pages generated, user approves direction.
> 2. `/design-shotgun` — visual variants. **Exit when:** one variant chosen.
> 3. `/design-html` — production HTML/CSS. **Exit when:** code matches mock.
> 4. `/design-review` — UI audit + fixes. **Exit when:** no slop remains.

**Step 5 (Bootstrap).** Invoke `/design-consultation`.

---

## How to adapt these patterns

When the user's situation is close to but not exactly one of the five:

- **Keep the spine.** The first 1–2 skills are usually the same as the
  pattern's; the rest may vary.
- **Splice in safety.** Any pattern can be wrapped with `/guard` (prepend)
  + `/unfreeze` (append) when blast radius is high.
- **Skip steps the user already completed.** If they've already shipped,
  start the chain at `/canary`, not `/qa`.
- **Re-verify on every adaptation.** Step 3 (Key Assumptions Check) is what
  catches "this pattern assumes X but the user actually has not-X." Don't
  skip it just because the pattern matches at a glance.
