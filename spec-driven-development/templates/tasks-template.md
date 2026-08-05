# Tasks: [FEATURE NAME]

**Spec:** [link] · **Plan:** [link]
**Format:** `- [ ] T### [P?] [Story?] Description — file path`
`[P]` = parallelizable (no dependency/file conflict). `[StoryN]` = which user story it serves. Mark `[X]` when done.

## Phase 1 — Setup
- [ ] T001 Initialize project structure per plan — [path]
- [ ] T002 [P] Configure tooling/linting/test runner — [path]

## Phase 2 — Foundational
> Core infrastructure that MUST be complete before ANY user story can be implemented.
- [ ] T003 [P] [shared model/schema] — [path]
- [ ] T004 [data layer / migrations] — [path]

## Phase 3 — User Story 1 (P1)
> Independently completable and testable.
- [ ] T005 [Story1] Write failing test for [behavior] — [path]   ← test-first
- [ ] T006 [Story1] Implement [capability] — [path]
- [ ] T007 [P] [Story1] [parallelizable sub-task] — [path]

## Phase 4 — User Story 2 (P2)
- [ ] T008 [Story2] Write failing test for [behavior] — [path]
- [ ] T009 [Story2] Implement [capability] — [path]

## Phase 5 — Polish
- [ ] T010 [P] Docs / cleanup / cross-cutting improvements — [path]
- [ ] T011 [P] Performance / observability — [path]

## Dependency notes
- Setup → Foundational → Stories (P1 → P2 → P3…) → Polish.
- Within a phase, `[P]` tasks may run together; non-`[P]` tasks are sequential — halt on failure.
