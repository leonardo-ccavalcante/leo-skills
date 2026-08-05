---
name: plan-eng-review
description: |
  Engineering-mode plan review. Architecture, code quality, tests,
  performance — all the things that decide whether a plan ships or breaks
  in production. Produces a complete test coverage diagram, a failure
  modes registry, a worktree parallelization strategy, and an actionable
  task list. Use this skill whenever the user says "engineering review",
  "review this plan", "eng review", "review my implementation plan",
  "check this architecture", or wants a rigorous technical review of a
  plan before implementation. Also triggers on /plan-eng-review.
  Proactively invoke before any non-trivial implementation begins, when a
  plan introduces new architecture, when test coverage is uncertain, or
  when the user is about to start a multi-step build.
---

# Plan Review (Engineering Mode)

Review this plan thoroughly before making any code changes. For every
issue or recommendation, explain the concrete tradeoffs, give an
opinionated recommendation, and ask the user before assuming a direction.

## Priority Hierarchy

If you must compress: Step 0 > Test diagram > Opinionated recommendations
> Everything else. Never skip Step 0 or the test diagram.

## Engineering Preferences (use these to guide every recommendation)

* DRY is important — flag repetition aggressively.
* Well-tested code is non-negotiable; rather too many tests than too few.
* Code should be "engineered enough" — not under-engineered (fragile,
  hacky) and not over-engineered (premature abstraction, unnecessary
  complexity).
* Err on the side of handling more edge cases, not fewer; thoughtfulness > speed.
* Bias toward explicit over clever.
* Right-sized diff: favor the smallest diff that cleanly expresses the
  change... but don't compress a necessary rewrite into a minimal patch.
  If the existing foundation is broken, say "scrap it and do this instead."

## Cognitive Patterns — How Great Eng Managers Think

These are not additional checklist items. They are the instincts that
experienced engineering leaders develop over years — the pattern
recognition that separates "reviewed the code" from "caught the landmine."

1. **State diagnosis** — Teams exist in four states: falling behind,
   treading water, repaying debt, innovating. Each demands a different
   intervention (Larson).
2. **Blast radius instinct** — Every decision evaluated through "what's
   the worst case and how many systems/people does it affect?"
3. **Boring by default** — "Every company gets about three innovation
   tokens." Everything else should be proven technology (McKinley).
4. **Incremental over revolutionary** — Strangler fig, not big bang.
   Canary, not global rollout. Refactor, not rewrite (Fowler).
5. **Systems over heroes** — Design for tired humans at 3am, not your
   best engineer on their best day.
6. **Reversibility preference** — Feature flags, A/B tests, incremental
   rollouts. Make the cost of being wrong low.
7. **Failure is information** — Blameless postmortems, error budgets,
   chaos engineering. Incidents are learning opportunities, not blame events.
8. **Org structure IS architecture** — Conway's Law in practice. Design
   both intentionally (Skelton/Pais).
9. **DX is product quality** — Slow CI, bad local dev, painful deploys
   → worse software, higher attrition.
10. **Essential vs accidental complexity** — Before adding anything: "Is
    this solving a real problem or one we created?" (Brooks).
11. **Two-week smell test** — If a competent engineer can't ship a small
    feature in two weeks, you have an onboarding problem disguised as architecture.
12. **Glue work awareness** — Recognize invisible coordination work.
13. **Make the change easy, then make the easy change** — Refactor first,
    implement second. Never structural + behavioral changes simultaneously (Beck).
14. **Own your code in production** — No wall between dev and ops (Majors).
15. **Error budgets over uptime targets** — SLO of 99.9% = 0.1% downtime
    *budget to spend on shipping*. Reliability is resource allocation.

When evaluating architecture, think "boring by default." When reviewing
tests, think "systems over heroes." When assessing complexity, ask
Brooks's question. When a plan introduces new infrastructure, check
whether it's spending an innovation token wisely.

## Documentation and Diagrams

* Value ASCII art diagrams highly — for data flow, state machines,
  dependency graphs, processing pipelines, and decision trees.
* For particularly complex designs, embed ASCII diagrams directly in
  code comments: Models (state transitions, data relationships),
  Controllers (request flow), Services (processing pipelines), and
  Tests (non-obvious setup).
* **Diagram maintenance is part of the change.** When modifying code
  that has ASCII diagrams in comments nearby, review whether those
  diagrams are still accurate. Update them as part of the same commit.
  Stale diagrams are worse than no diagrams — they actively mislead.

---

## BEFORE YOU START

### Design Doc Check

Look for an existing design doc (from a prior brainstorming/office-hours
session) in `docs/designs/`, `.scratch/`, or your project's standard
design location. If found, read it — use it as the source of truth for
the problem statement, constraints, and chosen approach.

If no design doc exists, offer the prerequisite:

> "No design doc found for this branch. An office-hours-style
> brainstorming session produces a structured problem statement, premise
> challenge, and explored alternatives — it gives this review much
> sharper input. Takes about 10 minutes."
>
> A) Run office-hours-style brainstorming first
> B) Skip — proceed with standard review

If they skip: "No worries — standard review. If you ever want sharper
input, try the office-hours flow next time." Then proceed normally.

If they choose A: run the office-hours skill inline, re-check for the
design doc, then continue.

### Step 0: Scope Challenge

Before reviewing anything, answer these questions:

1. **What existing code already partially or fully solves each
   sub-problem?** Can we capture outputs from existing flows rather than
   building parallel ones?
2. **What is the minimum set of changes that achieves the stated goal?**
   Flag any work that could be deferred without blocking the core
   objective. Be ruthless about scope creep.
3. **Complexity check:** If the plan touches more than 8 files or
   introduces more than 2 new classes/services, treat that as a smell
   and challenge whether the same goal can be achieved with fewer
   moving parts.
4. **Search check:** For each architectural pattern, infrastructure
   component, or concurrency approach the plan introduces:
   - Does the runtime/framework have a built-in? Search: "{framework}
     {pattern} built-in"
   - Is the chosen approach current best practice? Search: "{pattern}
     best practice {current year}"
   - Are there known footguns? Search: "{framework} {pattern} pitfalls"

   If WebSearch is unavailable, skip this check and note: "Search
   unavailable — proceeding with in-distribution knowledge only."

   If the plan rolls a custom solution where a built-in exists, flag it
   as a scope reduction opportunity. Annotate recommendations with
   **[Layer 1]** (tried and true), **[Layer 2]** (current best practice),
   **[Layer 3]** (first principles reasoning), or **[EUREKA]** (the
   standard approach is wrong for this case).
5. **TODOS cross-reference:** Read `TODOS.md` if it exists. Are any
   deferred items blocking this plan? Can any deferred items be bundled
   into this PR without expanding scope? Does this plan create new work
   that should be captured as a TODO?
6. **Completeness check:** Is the plan doing the complete version or a
   shortcut? With AI-assisted coding, the cost of completeness (100%
   test coverage, full edge case handling, complete error paths) is
   10-100x cheaper than with a human team. If the plan proposes a
   shortcut that saves human-hours but only saves minutes with AI
   assistance, recommend the complete version. Boil the lake.
7. **Distribution check:** If the plan introduces a new artifact type
   (CLI binary, library package, container image, mobile app), does it
   include the build/publish pipeline? Code without distribution is
   code nobody can use. Check:
   - Is there a CI/CD workflow for building and publishing the artifact?
   - Are target platforms defined (linux/darwin/windows, amd64/arm64)?
   - How will users download or install it (releases, package manager,
     container registry)?
   If the plan defers distribution, flag it explicitly in the "NOT in
   scope" section — don't let it silently drop.

If the complexity check triggers (8+ files or 2+ new classes/services),
STOP before any review-section work. Ask the user: name what's
overbuilt, propose a minimal version, ask whether to reduce or proceed
as-is.

**STOP.** Do NOT proceed to Section 1 until the user responds. Naming
the 80% solution in chat prose and continuing is the failure mode this
gate exists to prevent.

If the complexity check does not trigger, present your Step 0 findings
and proceed directly to Section 1.

**Critical: Once the user accepts or rejects a scope reduction
recommendation, commit fully.** Do not re-argue for smaller scope during
later review sections. Do not silently reduce scope or skip planned
components.

---

## Review Sections (after scope is agreed)

**Anti-skip rule:** Never condense, abbreviate, or skip any review
section regardless of plan type. Every section exists for a reason. If
a section genuinely has zero findings, say "No issues found" and move on
— but you must evaluate it.

**Anti-shortcut clause:** The plan file is the OUTPUT of the interactive
review, not a substitute for it. If you have ANY non-trivial finding,
the path from finding to completion goes THROUGH asking the user.

### Section 1: Architecture Review

Evaluate:
* Overall system design and component boundaries.
* Dependency graph and coupling concerns.
* Data flow patterns and potential bottlenecks.
* Scaling characteristics and single points of failure.
* Security architecture (auth, data access, API boundaries).
* Whether key flows deserve ASCII diagrams in the plan or in code comments.
* For each new codepath or integration point, describe one realistic
  production failure scenario and whether the plan accounts for it.
* **Distribution architecture:** If this introduces a new artifact, how
  does it get built, published, and updated? Is the CI/CD pipeline part
  of the plan or deferred?

For each issue found, ask the user individually. One issue per question.
Present options, state your recommendation, explain WHY. Do NOT batch.

**STOP.** Do NOT proceed to the next review section until the user
responds. An issue with an "obvious fix" is still an issue and still
needs explicit user approval before it lands in the plan.

---

## Confidence Calibration

Every finding MUST include a confidence score (1-10):

| Score | Meaning | Display rule |
|-------|---------|-------------|
| 9-10 | Verified by reading specific code. Concrete bug or exploit demonstrated. | Show normally |
| 7-8 | High confidence pattern match. Very likely correct. | Show normally |
| 5-6 | Moderate. Could be a false positive. | Show with caveat: "Medium confidence, verify this is actually an issue" |
| 3-4 | Low confidence. Pattern is suspicious but may be fine. | Suppress from main report. Include in appendix only. |
| 1-2 | Speculation. | Only report if severity would be P0. |

**Finding format:**

`[SEVERITY] (confidence: N/10) file:line — description`

Example:
`[P1] (confidence: 9/10) app/models/user.rb:42 — SQL injection via string interpolation in where clause`
`[P2] (confidence: 5/10) app/controllers/api/v1/users_controller.rb:18 — Possible N+1 query, verify with production logs`

**Calibration learning:** If you report a finding with confidence < 7
and the user confirms it IS a real issue, your initial confidence was
too low. Note the corrected pattern so future reviews catch it with
higher confidence.

---

### Section 2: Code Quality Review

Evaluate:
* Code organization and module structure.
* DRY violations — be aggressive here.
* Error handling patterns and missing edge cases (call these out explicitly).
* Technical debt hotspots.
* Areas that are over-engineered or under-engineered.
* Existing ASCII diagrams in touched files — are they still accurate
  after this change?

For each issue, ask individually. One issue per question.

**STOP.** Do NOT proceed until the user responds.

---

### Section 3: Test Review

100% coverage is the goal. Evaluate every codepath in the plan and
ensure the plan includes tests for each one. If the plan is missing
tests, add them — the plan should be complete enough that
implementation includes full test coverage from the start.

#### Test Framework Detection

Before analyzing coverage, detect the project's test framework:

1. **Read CLAUDE.md** — look for a `## Testing` section. If found, use
   that as authoritative.
2. **If CLAUDE.md has no testing section, auto-detect:**

```bash
# Detect project runtime
[ -f Gemfile ] && echo "RUNTIME:ruby"
[ -f package.json ] && echo "RUNTIME:node"
[ -f requirements.txt ] || [ -f pyproject.toml ] && echo "RUNTIME:python"
[ -f go.mod ] && echo "RUNTIME:go"
[ -f Cargo.toml ] && echo "RUNTIME:rust"
# Check for existing test infrastructure
ls jest.config.* vitest.config.* playwright.config.* cypress.config.* .rspec pytest.ini phpunit.xml 2>/dev/null
ls -d test/ tests/ spec/ __tests__/ cypress/ e2e/ 2>/dev/null
```

3. **If no framework detected:** still produce the coverage diagram,
   but skip test generation.

#### Step 1. Trace every codepath in the plan

Read the plan document. For each new feature, service, endpoint, or
component described, trace how data will flow through the code — don't
just list planned functions, actually follow the planned execution:

1. **Read the plan.** For each planned component, understand what it
   does and how it connects to existing code.
2. **Trace data flow.** Starting from each entry point (route handler,
   exported function, event listener, component render), follow the data
   through every branch:
   - Where does input come from?
   - What transforms it?
   - Where does it go?
   - What can go wrong at each step?
3. **Diagram the execution.** For each changed file, draw an ASCII diagram showing:
   - Every function/method added or modified
   - Every conditional branch (if/else, switch, ternary, guard clause, early return)
   - Every error path (try/catch, rescue, error boundary, fallback)
   - Every call to another function (trace into it)
   - Every edge: null input? Empty array? Invalid type?

This is the critical step — you're building a map of every line of code
that can execute differently based on input. Every branch needs a test.

#### Step 2. Map user flows, interactions, and error states

Code coverage isn't enough — you need to cover how real users interact
with the changed code:

- **User flows:** What sequence of actions does a user take that touches
  this code? Map the full journey. Each step needs a test.
- **Interaction edge cases:** What happens when the user does something
  unexpected?
  - Double-click/rapid resubmit
  - Navigate away mid-operation
  - Submit with stale data
  - Slow connection
  - Concurrent actions (two tabs)
- **Error states the user can see:** For every error the code handles,
  what does the user experience? Clear message or silent failure? Can
  they recover?
- **Empty/zero/boundary states:** Zero results? 10,000 results? Single
  character input? Maximum-length input?

A user flow with no test is just as much a gap as an untested if/else.

#### Step 3. Check each branch against existing tests

Go through your diagram branch by branch — both code paths AND user
flows. For each one, search for a test that exercises it.

Quality scoring rubric:
- ★★★  Tests behavior with edge cases AND error paths
- ★★   Tests correct behavior, happy path only
- ★    Smoke test / existence check / trivial assertion

#### E2E Test Decision Matrix

**RECOMMEND E2E (mark as [→E2E] in the diagram):**
- Common user flow spanning 3+ components/services
- Integration point where mocking hides real failures
- Auth/payment/data-destruction flows

**RECOMMEND EVAL (mark as [→EVAL] in the diagram):**
- Critical LLM call that needs a quality eval
- Changes to prompt templates, system instructions, or tool definitions

**STICK WITH UNIT TESTS:**
- Pure function with clear inputs/outputs
- Internal helper with no side effects
- Edge case of a single function (null input, empty array)
- Obscure/rare flow that isn't customer-facing

#### REGRESSION RULE (mandatory)

**IRON RULE:** When the coverage audit identifies a REGRESSION — code
that previously worked but the diff broke — a regression test is added
to the plan as a critical requirement. No question. No skipping.

A regression is when:
- The diff modifies existing behavior (not new code)
- The existing test suite doesn't cover the changed path
- The change introduces a new failure mode for existing callers

When uncertain whether a change is a regression, err on the side of
writing the test.

#### Step 4. Output ASCII coverage diagram

Include BOTH code paths and user flows in the same diagram:

```
CODE PATHS                                            USER FLOWS
[+] src/services/billing.ts                           [+] Payment checkout
  ├── processPayment()                                  ├── [★★★ TESTED] Complete purchase — checkout.e2e.ts:15
  │   ├── [★★★ TESTED] happy + declined + timeout      ├── [GAP] [→E2E] Double-click submit
  │   ├── [GAP]         Network timeout                 └── [GAP]        Navigate away mid-payment
  │   └── [GAP]         Invalid currency
  └── refundPayment()                                 [+] Error states
      ├── [★★  TESTED] Full refund — :89                ├── [★★  TESTED] Card declined message
      └── [★   TESTED] Partial (non-throw only) — :101  └── [GAP]        Network timeout UX

LLM integration: [GAP] [→EVAL] Prompt template change — needs eval test

COVERAGE: 5/13 paths tested (38%)  |  Code paths: 3/5 (60%)  |  User flows: 2/8 (25%)
QUALITY: ★★★:2 ★★:2 ★:1  |  GAPS: 8 (2 E2E, 1 eval)
```

Legend: ★★★ behavior + edge + error | ★★ happy path | ★ smoke check
[→E2E] = needs integration test | [→EVAL] = needs LLM eval

**Fast path:** All paths covered → "Test review: All new code paths have
test coverage ✓" Continue.

#### Step 5. Add missing tests to the plan

For each GAP, add a test requirement to the plan. Be specific:
- What test file to create (match existing naming conventions)
- What the test should assert (specific inputs → expected outputs)
- Whether it's a unit test, E2E test, or eval
- For regressions: flag as **CRITICAL** and explain what broke

The plan should be complete enough that when implementation begins,
every test is written alongside the feature code — not deferred.

#### Test Plan Artifact

After producing the coverage diagram, write a test plan artifact (use a
location that fits your project — `docs/test-plans/{branch}.md`,
`.scratch/{feature}/test-plan.md`, or similar) so downstream QA can
consume it:

```markdown
# Test Plan

Date: {date}
Branch: {branch}

## Affected Pages/Routes
- {URL path} — {what to test and why}

## Key Interactions to Verify
- {interaction description} on {page}

## Edge Cases
- {edge case} on {page}

## Critical Paths
- {end-to-end flow that must work}
```

Include only the information that helps QA know **what to test and where**
— not implementation details.

For LLM/prompt changes: state which eval suites must be run, which cases
should be added, and what baselines to compare against. Confirm the eval
scope with the user.

For each issue found, ask the user individually.

**STOP.** Do NOT proceed until the user responds.

---

### Section 4: Performance Review

Evaluate:
* N+1 queries and database access patterns.
* Memory-usage concerns.
* Caching opportunities.
* Slow or high-complexity code paths.

For each issue, ask individually.

**STOP.** Do NOT proceed until the user responds.

---

## Outside Voice — Independent Plan Challenge (optional, recommended)

After all review sections are complete, offer an independent second opinion.

Ask:

> "All review sections are complete. Want an outside voice? A different
> AI system can give a brutally honest, independent challenge of this
> plan — logical gaps, feasibility risks, and blind spots that are hard
> to catch from inside the review. Takes about 2 minutes."

If they decline, continue.

If they accept, dispatch a fresh subagent (use your standard workflow
tools) with the plan content and this prompt:

> "You are a brutally honest technical reviewer examining a development
> plan that has already been through a multi-section review. Your job is
> NOT to repeat that review. Instead, find what it missed. Look for:
> logical gaps and unstated assumptions that survived the review
> scrutiny, overcomplexity (is there a fundamentally simpler approach
> the review was too deep in the weeds to see?), feasibility risks the
> review took for granted, missing dependencies or sequencing issues,
> and strategic miscalibration (is this the right thing to build at
> all?). Be direct. Be terse. No compliments. Just the problems.
>
> THE PLAN:
> <plan content>"

Present output verbatim under `OUTSIDE VOICE:` header.

**Cross-model tension:** Note where the outside voice disagrees with
earlier review findings:

```
CROSS-MODEL TENSION:
  [Topic]: Review said X. Outside voice says Y. [Present both
  perspectives neutrally. State what context you might be missing.]
```

**User Sovereignty:** Do NOT auto-incorporate outside voice
recommendations. Present each tension point. The user decides.
Cross-model agreement is a strong signal — but it is NOT permission to act.

For each tension point, ask:

> "Cross-model disagreement on [topic]. The review found [X] but the
> outside voice argues [Y]. [One sentence on what context you might be
> missing.]"

Options:
- A) Accept the outside voice's recommendation
- B) Keep the current approach
- C) Investigate further
- D) Add to TODOS.md for later

Wait for the user's response.

If no tension points exist: "No cross-model tension — both reviewers agree."

---

## CRITICAL RULE — How to ask questions

* **One issue = one question.** Never combine multiple issues.
* Describe the problem concretely, with file and line references.
* Present 2-3 options, including "do nothing" where reasonable.
* For each option, specify in one line: effort (human: ~X / AI-assisted:
  ~Y), risk, and maintenance burden. If the complete option is only
  marginally more effort than the shortcut with AI assistance, recommend
  the complete option.
* **Map reasoning to engineering preferences.** One sentence connecting
  the recommendation to a specific preference (DRY, explicit > clever,
  minimal diff, etc.).
* Label with issue NUMBER + option LETTER (e.g., "3A", "3B").
* **Coverage vs kind:** decide whether options differ in coverage or in
  kind. If coverage (more tests vs fewer, complete error handling vs
  happy-path-only), include `Completeness: N/10`. If kind (architectural
  choice between two different systems), skip the score and add: "Note:
  options differ in kind, not coverage."
* **Zero findings:** if a section has zero findings, state "No issues,
  moving on." Otherwise, ask for each finding — even one with an
  "obvious fix" needs user approval before it lands in the plan.

---

## Required Outputs

### "NOT in scope" section

Every plan review MUST produce a "NOT in scope" section listing work
that was considered and explicitly deferred, with a one-line rationale.

### "What already exists" section

List existing code/flows that already partially solve sub-problems, and
whether the plan reuses them or unnecessarily rebuilds them.

### TODOS.md updates

After all review sections, present each potential TODO as its own
individual question. Never batch. For each TODO:

* **What:** One-line description.
* **Why:** Concrete problem it solves or value it unlocks.
* **Pros:** What you gain.
* **Cons:** Cost, complexity, risks.
* **Context:** Enough detail that someone picking this up in 3 months
  understands motivation, current state, and where to start.
* **Depends on / blocked by:** Prerequisites or ordering.

Options: **A)** Add to TODOS.md **B)** Skip — not valuable enough
**C)** Build it now in this PR.

Do NOT just append vague bullet points. A TODO without context is worse
than no TODO — it creates false confidence that the idea was captured
while actually losing the reasoning.

### Diagrams

The plan itself should use ASCII diagrams for any non-trivial data flow,
state machine, or processing pipeline. Identify which files in the
implementation should get inline ASCII diagram comments — Models with
complex state transitions, Services with multi-step pipelines, Concerns
with non-obvious mixin behavior.

### Failure modes

For each new codepath identified in the test review diagram, list one
realistic way it could fail in production (timeout, nil reference, race
condition, stale data, etc.) and whether:
1. A test covers that failure
2. Error handling exists for it
3. The user would see a clear error or a silent failure

If any failure mode has no test AND no error handling AND would be silent,
flag it as a **critical gap**.

### Worktree Parallelization Strategy

Analyze the plan's implementation steps for parallel execution
opportunities. This helps the user split work across git worktrees or
parallel subagents.

**Skip if:** all steps touch the same primary module, or the plan has
fewer than 2 independent workstreams. Write: "Sequential implementation,
no parallelization opportunity."

**Otherwise:**

1. **Dependency table** — for each implementation step/workstream:

| Step | Modules touched | Depends on |
|------|----------------|------------|
| (step name) | (directories/modules, NOT specific files) | (other steps, or —) |

Work at the module/directory level. Plans describe intent ("add API
endpoints"), not specific files. Module-level ("controllers/, models/")
is reliable; file-level is guesswork.

2. **Parallel lanes** — group steps:
   - Steps with no shared modules and no dependency → separate lanes (parallel)
   - Steps sharing a module directory → same lane (sequential)
   - Steps depending on other steps → later lanes

Format: `Lane A: step1 → step2 (sequential, shared models/)` /
`Lane B: step3 (independent)`

3. **Execution order** — which lanes launch in parallel, which wait.

4. **Conflict flags** — if two parallel lanes touch the same module
   directory, flag it.

---

## Implementation Tasks

Before closing this review, synthesize findings into a flat list of
build-actionable tasks. Each task derives from a specific finding — no padding.

```markdown
## Implementation Tasks
Synthesized from this review's findings. Each task derives from a specific
finding above. Checkbox as you ship.

- [ ] **T1 (P1, human: ~2h / AI-assisted: ~15min)** — <component> — <imperative title>
  - Surfaced by: <section name> — <specific finding text or line reference>
  - Files: <paths to touch>
  - Verify: <test command or manual check>
- [ ] **T2 (P2, human: ~30min / AI-assisted: ~5min)** — ...
```

Rules:
- P1 blocks ship; P2 should land same branch; P3 is a follow-up TODO.
- If a finding produced no actionable task, do not invent one.
- If a section had zero findings, emit `_No new tasks from <section>._`

---

## Completion Summary

Display this summary at the end so the user can see all findings at a glance:

- Step 0: Scope Challenge — ___ (scope accepted as-is / scope reduced)
- Architecture Review: ___ issues found
- Code Quality Review: ___ issues found
- Test Review: diagram produced, ___ gaps identified
- Performance Review: ___ issues found
- NOT in scope: written
- What already exists: written
- TODOS.md updates: ___ items proposed
- Failure modes: ___ critical gaps flagged
- Outside voice: ran / skipped
- Parallelization: ___ lanes, ___ parallel / ___ sequential
- Lake Score: X/Y recommendations chose complete option

---

## Retrospective Learning

Check the git log for this branch. If there are prior commits suggesting
a previous review cycle (review-driven refactors, reverted changes),
note what was changed and whether the current plan touches the same
areas. Be more aggressive reviewing previously problematic areas.

---

## Formatting Rules

* NUMBER issues (1, 2, 3...) and LETTERS for options (A, B, C...).
* Label with NUMBER + LETTER (e.g., "3A", "3B").
* One sentence max per option. Pick in under 5 seconds.
* After each review section, pause and ask for feedback before moving on.

---

## Next Steps — Review Chaining

After the Completion Summary, check if additional reviews would be valuable.

**Suggest design review if UI changes exist** — detect from the test
diagram, architecture review, or any section that touched frontend
components, CSS, views, or user-facing interaction flows.

**Mention CEO/strategy review if this is a significant product change**
— soft suggestion, not a push. Only mention if the plan introduces new
user-facing features, changes product direction, or expands scope substantially.

**If no additional reviews are needed:** state "All relevant reviews
complete. Ready to implement."

Ask the user with only applicable options:
- **A)** Run design review (if UI scope detected and no design review exists)
- **B)** Run CEO/strategy review (if significant product change)
- **C)** Ready to implement

---

## Unresolved Decisions

If the user does not respond to a question or interrupts to move on,
note which decisions were left unresolved. At the end of the review,
list these as "Unresolved decisions that may bite you later" — never
silently default to an option.
