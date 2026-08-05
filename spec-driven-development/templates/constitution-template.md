# [PROJECT NAME] Constitution

**Version:** [MAJOR.MINOR.PATCH] · **Ratified:** [YYYY-MM-DD] · **Last amended:** [YYYY-MM-DD]

> Immutable project principles. These become enforcement gates in the plan's Constitution Check.
> Versioning: MAJOR = backward-incompatible removals/redefinitions; MINOR = new principles; PATCH = clarifications.
> Replace each `[PLACEHOLDER]`; no unexplained tokens may remain. Principles must be testable.

## Principles

### Article I — Library-First
[Every feature begins as a standalone, self-contained library/module. State how modularity is enforced.]

### Article II — CLI / Interface Mandate
[Libraries expose functionality through a text-in/text-out interface (JSON for structured data). State the contract.]

### Article III — Test-First *(NON-NEGOTIABLE)*
All implementation follows strict TDD: write tests, confirm they FAIL, then implement. [State how this is verified.]

### Article IV — Integration & Dependencies
[How integration points and dependency management are handled.]

### Article VII — Simplicity
Max 3 projects initially; additional projects require justification in the plan's Complexity Tracking.

### Article VIII — Anti-Abstraction
Use framework features directly rather than wrapping them; maintain single model representations.

### Article IX — Integration-First Testing
Use realistic test environments with real databases/services rather than mocks where feasible.

### [Article X — project-specific principle]
[Add your own. Each must be observable/testable.]

## Constraints
- **Security:** [requirements]
- **Tech stack:** [mandated/forbidden technologies]
- **Compliance:** [regulatory/organizational]

## Workflow
- **Code review:** [requirements]
- **Testing gates:** [what must pass before merge]
- **Deployment:** [process]

## Governance
- **Amendment procedure:** [how this document changes; who approves]
- **Compliance verification:** [how adherence is checked; `/analyze` flags MUST-violations as CRITICAL]

## Sync Impact Report *(regenerate on each amendment)*
- Version change: [old] → [new] ([MAJOR/MINOR/PATCH] — why)
- Affected files/templates: [list]
