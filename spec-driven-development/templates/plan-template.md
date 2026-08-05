# Implementation Plan: [FEATURE NAME]

**Branch:** `[###-short-name]` · **Date:** [YYYY-MM-DD] · **Spec:** [link to spec.md]

## Summary
[Primary requirements (from spec) + the technical approach in 2–4 sentences.]

## Technical Context
- **Language/Version:** [e.g., Python 3.12]
- **Primary dependencies:** [frameworks/libraries]
- **Storage:** [db/files/N/A]
- **Testing:** [framework]
- **Target platform:** [server/web/mobile/CLI]
- **Project type:** [single / web / mobile]
- **Performance goals:** [e.g., p95 < 200ms]
- **Scale/scope:** [users, data volume, request rate]

## Constitution Check *(gate)*
> Run BEFORE Phase 0 and again AFTER Phase 1. List each relevant principle and PASS/FAIL.
- Test-first (III): [PASS/FAIL — plan writes failing tests before code?]
- Simplicity (VII, ≤3 projects): [PASS/FAIL — project count?]
- Library-first / CLI (I, II): [PASS/FAIL]
- Integration-first testing (IX): [PASS/FAIL — real deps?]
- [Project-specific principles…]

## Project Structure
Choose one and delete the rest:
```
# (1) Single project (default)
src/        tests/
# (2) Web application
backend/    frontend/
# (3) Mobile + API
api/        ios/        android/
```
Documentation artifacts: `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `tasks.md`.

## Phase 0 — Research (`research.md`)
- Resolve each `[NEEDS CLARIFICATION]`; record decisions on dependencies/tech choices + rationale.

## Phase 1 — Design
- `data-model.md` — entities, fields, relationships, state transitions.
- `contracts/` — API/interface contracts.
- `quickstart.md` — how to validate the feature end to end.

## Complexity Tracking *(only if a Constitution Check failed)*
| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| [e.g., 4th project] | [reason] | [why 3 wasn't enough] |
