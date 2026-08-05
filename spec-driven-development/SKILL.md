---
name: spec-driven-development
description: Use when building a feature from a written specification, running or executing a spec, or doing spec-driven development (SDD) — and whenever the user says "spec-driven", "spec kit", "speckit", "run this spec", "build from the spec", "implement this spec", ".spec.md", "constitution/specify/plan/tasks/implement", or wants spec-before-code discipline, requirement gathering before coding, or traceability keeping specs, code, and tests in sync. Drives a feature from spec → plan → tasks → implementation → verification, enforcing approval gates and living-spec traceability. Prefer this over ad-hoc coding for any non-trivial feature where the "what/why" should be settled before the "how".
---

# Spec-Driven Development (SDD)

## Overview

Spec-Driven Development inverts the usual order: **the specification is the source of truth, and code serves the spec** — not the other way around. Two ideas drive it:

1. **Power inversion (from github/spec-kit):** specs are precise, complete, and unambiguous enough to *generate* implementation. You maintain the spec; the code is its expression in a particular stack.
2. **Anti-"vibecoding" discipline (from tesslio/spec-driven-development-tile):** you gather requirements, write a spec, and get *explicit approval* **before** writing code — then keep the spec, code, and tests traceably in sync afterward.

This skill is an **operational orchestrator**. The normal entry point is: *the user gives you a spec (or a feature request), and you run the lifecycle on it.* spec-kit supplies the **skeleton** (phases, templates, governance); tesslio supplies the **conscience** (approval gates, one-question interviewing, `.spec.md`+`[@test]` living specs, review). Full source detail lives in `references/` — load it when a step needs depth.

## When to use / when not

**Use it** when: implementing a non-trivial feature; you were handed a spec to build; starting a greenfield project that deserves structure; modernizing/extending a system feature-by-feature; or you need traceability between requirements, code, and tests.

**Skip it** (tesslio's *trivial-change exception*) for: typo/copy fixes, behavior-preserving refactors, or urgent production hotfixes — but document hotfixes retroactively. Don't bureaucratize a one-line change.

## The unified SDD lifecycle

One sequence. Each phase shows the spec-kit **mechanism** and the tesslio **discipline** it pairs with. You don't need spec-kit's CLI installed — you perform the workflow directly. (`references/spec-kit-reference.md` has every command's internal logic; `references/tesslio-reference.md` has every rule and skill in full.)

| Phase | spec-kit mechanism | tesslio discipline |
|---|---|---|
| **P0 · Govern** *(optional, once per project)* | `constitution` → `.specify/memory/constitution.md`; Articles I–IX | — |
| **P1 · Requirements** | `specify` → `spec.md` (WHAT/WHY, not HOW) | **requirement-gathering** + **one-question-at-a-time** |
| **P2 · Approval gate** | — | **spec-before-code**: get explicit "the spec is accurate" |
| **P3 · Clarify & quality** | `clarify` (≤5 Qs) + `checklist` (CHK-IDs) | **spec-format-compliance** |
| **P4 · Plan & Tasks** | `plan` → `plan.md`/`research.md`/`data-model.md`/`contracts/`; `tasks` → `tasks.md` | *(tesslio has no equivalent — spec-kit fills this gap)* |
| **P5 · Implement** | `implement`: execute tasks in order, respect `[P]`, mark `[X]` | build **only** against the approved spec |
| **P6 · Verify & review** | `analyze` (read-only cross-artifact consistency) | **spec-verification** + **work-review** |

### P0 — Govern (optional)
Establish project principles once. Copy `templates/constitution-template.md`. These become gates later (e.g. test-first, ≤3 projects, library-first). Skip for small/experimental work.

### P1 — Requirements
If you were given a complete spec, **skip to P3 to verify it**. If you only have intent:
- Run a **requirement-gathering** interview. Follow **one-question-at-a-time**: ask ONE focused question, wait for the answer, let it shape the next. Bundled questions ("what about errors, pagination, and auth?") yield shallow answers. This rule applies only to *live* interviews — not to written prep docs or analysis.
- Cover scope boundaries, primary workflows, edge cases/errors, and performance/security constraints.
- Capture the result as a spec. Use `templates/spec-template.md` (spec-kit, rich) **or** `templates/feature.spec.md` (tesslio `.spec.md`, lightweight + test-linked). Mark unknowns with `[NEEDS CLARIFICATION]` (≤3); write testable functional requirements (FR-001…) and tech-agnostic success criteria (SC-001…).

### P2 — Approval gate (the hard line)
**Do not write implementation code until the spec is approved.** Valid approval = the stakeholder confirms "the spec is accurate" or accepts your corrected version. **Invalid** approval = silence, no response, "just do it" without review, or your own assumption. If specs already exist, verify they're still accurate before trusting them.

### P3 — Clarify & quality
- **Clarify**: scan the spec against spec-kit's taxonomy (scope, data model, UX, quality attributes, integration, edge cases, constraints, terminology, completion, misc). Ask up to 5 questions, highest impact×uncertainty first, **one at a time**, recording answers in a `## Clarifications` section. *(Synthesis seam: spec-kit supplies the question taxonomy; tesslio's one-question rule governs delivery.)*
- **Checklist**: generate a quality checklist (CHK001…) that tests the **requirements themselves**, never implementation behavior. Ask "Are the visual-hierarchy requirements quantified?" — never "Does the button click work?". Dimensions: Completeness, Clarity, Consistency, Coverage, Measurability, Edge Cases, Gap, Ambiguity.
- **Format compliance**: if using `.spec.md`, ensure YAML frontmatter (`name`, `description`, `targets` ≥1) and inline `[@test]` links beside the requirements they verify. Run `scripts/validate-specs.sh` and `scripts/check-spec-links.sh`.

### P4 — Plan & Tasks
- **Plan** (`templates/plan-template.md`): fill Technical Context (language, deps, storage, testing, platform, scale), run the **Constitution Check** gate, choose a project structure, log any violations in Complexity Tracking. Produce design artifacts (`research.md`, `data-model.md`, `contracts/`, `quickstart.md`) as warranted.
- **Tasks** (`templates/tasks-template.md`): derive a dependency-ordered list. Format `- [ ] T001 [P] [Story] description with file path`. `[P]` = parallelizable. Phases: **Setup → Foundational → User Stories (P1→P2→P3, each independently testable) → Polish**.

### P5 — Implement
Execute tasks phase by phase. Run `[P]` tasks together; halt on a non-parallel failure. Build only what the approved spec calls for. Mark each finished task `[X]`. Create stack-appropriate ignore files as needed.

### P6 — Verify & review
- **analyze** (read-only): check cross-artifact consistency — duplication, ambiguity, underspecification, **constitution conflicts (auto-CRITICAL)**, and coverage gaps (orphan requirements/tasks). Emit a findings table: Category | Severity | Location | Summary | Recommendation.
- **spec-verification**: confirm `targets` and `[@test]` links resolve, run the linked tests, compare code against the spec, flag drift (behavior changed but spec didn't), remediate, re-verify.
- **work-review**: match changed files to spec `targets`; for each requirement find implementation evidence (file:line); run linked tests; **document discovered requirements** (behavior built beyond the original spec) back into the spec. Pass = all requirements verified, linked tests pass, discoveries recorded.

## Decision tree — which path

```
Do you already have an approved, accurate spec?
├─ YES → P3 (quick verify/clarify) → P4 → P5 → P6
└─ NO  → is this trivial / behavior-preserving?
         ├─ YES → just do it (trivial-change exception); update spec only if behavior changes
         └─ NO  → Lean vs Full?
                  ├─ Lean (experiment, small):  P1 → P2 → P4 → P5
                  └─ Full (production, shared):  P0 → P1 → P2 → P3 → P4 → P5 → P6
```
**Lean path** = specify → plan → tasks → implement. **Full path** adds governance, clarification, checklists, and analysis/review. Match rigor to stakes.

## The `.spec.md` format (tesslio living specs)

When you want specs that travel with the code and stay verifiable, use `.spec.md` (one file per logical feature, in `specs/`):

```markdown
---
name: Authentication
description: Login, token refresh, and session management
targets:
  - src/identity/authentication.py
  - src/identity/sessions.py
---

# Authentication

## Login
- Invalid credentials return 401
  `[@test] tests/identity/test_authentication_errors.py`
- Accounts lock after 3 failed attempts
  `[@test] tests/identity/test_lockout.py`
```
Rules: `targets` lists ≥1 relative path/glob the spec covers; put `[@test]` links **inline, next to** the requirement they verify (never grouped at the end); add prose context around each link. Keep specs scannable and synchronized with the code. Copy `templates/feature.spec.md` to start.

## Guardrails (always apply)

From **tesslio** (interaction discipline):
- **spec-before-code** — no implementation before an approved spec; silence ≠ approval.
- **one-question-at-a-time** — in live interviews, one question per message.
- **spec-format-compliance** — `.spec.md` + valid frontmatter + inline `[@test]`.

From **spec-kit's constitution** (engineering defaults — adapt per project; full text in `references/spec-kit-reference.md`):
- **Test-first (Article III, non-negotiable):** write tests, see them fail, then implement.
- **Simplicity (Article VII):** ≤3 projects initially; justify more in Complexity Tracking.
- **Library-first / CLI interface (I, II):** features as standalone, observable units.
- **Integration-first testing (IX):** prefer real dependencies over mocks.
- **Templates are guardrails:** they constrain output toward quality; keep `[NEEDS CLARIFICATION]` markers honest rather than guessing.

## Pointers — go deeper when a step needs it

- `references/spec-kit-reference.md` — every slash command's internal logic, all template section headings, Constitution Articles I–IX, the `specify` CLI surface, extensions/presets/workflows, supported agents, and the `.specify/`+`specs/` directory layout.
- `references/tesslio-reference.md` — the 4 skills in full, the 3 rules (with valid/invalid approval and exceptions), the `.spec.md` format + styleguide, directory conventions.
- `references/examples.md` — 9 worked behavioral scenarios (vague request → interview, spec drift after refactor, trivial-change exception, work-review with discovered requirements, skip-spec pushback, …). Read these to calibrate judgment on real cases.
- `templates/` — copy these to produce real artifacts immediately.
- `scripts/validate-specs.sh`, `scripts/check-spec-links.sh` — validate `.spec.md` format and `[@test]`/`targets` links.
