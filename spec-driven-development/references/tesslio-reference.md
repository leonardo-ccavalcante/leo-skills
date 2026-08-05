# tesslio reference (tesslio/spec-driven-development-tile)

Complete reference for the Tessl Labs Spec-Driven Development tile. Source: `github.com/tesslio/spec-driven-development-tile` (MIT, v2.0.1, by Tessl / tessl-labs). The tile targets AI coding agents and frames SDD as agent *steering* — skills + rules + evaluation scenarios. This document preserves its content so the SDD skill loses no information.

## Table of contents
1. What a "tile" is
2. Purpose
3. Repo structure & manifest
4. The six-step SDD process
5. The 4 skills (full)
6. The 3 rules (full)
7. `.spec.md` format & styleguide
8. Validation scripts
9. Relationship to spec-kit

---

## 1. What a "tile" is

A **tile** in the Tessl ecosystem is a packaged, versioned capability module that steers AI agent behavior. Tiles are composable (install via `tessl install tessl-labs/spec-driven-development`), are steering modules (shape workflow via skills, rules, docs — no special framework needed), are versioned to the Tessl Registry (semver; this tile v2.0.1), and are configuration-based (a `tile.json` manifest declaring skills, rules, docs). They work alongside library tiles for technology-specific guidance.

## 2. Purpose

Teach AI coding agents to **"gather requirements, write specifications, and get approval before writing code."** It directly counters "vibecoding" — unstructured prompting that produces hallucinated APIs, poor error handling, inadequate testing, and no requirement traceability. Value proposition: enforce explicit requirements documentation and traceability between code, specs, and test coverage before implementation.

## 3. Repo structure & manifest

```
spec-driven-development-tile/
├── docs/            index.md · spec-format.md · spec-styleguide.md
├── evals/           9 scenarios (see references/examples.md)
├── rules/           spec-before-code.md · one-question-at-a-time.md · spec-format-compliance.md
├── scripts/         validate-specs.sh · check-spec-links.sh
├── skills/          requirement-gathering · spec-writer · spec-verification · work-review (each SKILL.md)
├── LICENSE · Makefile · README.md · tile.json
```

**tile.json:**
```json
{
  "name": "tessl-labs/spec-driven-development",
  "version": "2.0.1",
  "summary": "Spec-driven workflow covering requirement gathering, spec authoring, implementation review, and verification — with skills, rules, and evaluation scenarios.",
  "private": false,
  "docs": "docs/index.md",
  "skills": {
    "requirement-gathering": { "path": "skills/requirement-gathering/SKILL.md" },
    "spec-writer": { "path": "skills/spec-writer/SKILL.md" },
    "spec-verification": { "path": "skills/spec-verification/SKILL.md" },
    "work-review": { "path": "skills/work-review/SKILL.md" }
  },
  "steering": {
    "spec-before-code": { "rules": "rules/spec-before-code.md" },
    "one-question-at-a-time": { "rules": "rules/one-question-at-a-time.md" },
    "spec-format-compliance": { "rules": "rules/spec-format-compliance.md" }
  }
}
```

**Makefile targets:** `publish` (lint then `tessl tile publish .`), `lint` (`tessl tile lint .`), `review` (`tessl skill review` per skill), `eval` (`tessl eval run .`). CI verifies the `tile.json` version changed on PRs, lints structure, and runs `tessl skill review` per skill.

## 4. The six-step SDD process

1. **Gather requirements** — ask clarifying questions one at a time.
2. **Write specifications** — `.spec.md` files with YAML frontmatter + test linkages.
3. **Obtain approval** — explicit stakeholder sign-off before coding.
4. **Implement** — build against approved specs.
5. **Review work** — verify implementation meets spec requirements.
6. **Maintain sync** — keep specs, code, and tests synchronized over time.

Core concept (docs/index.md): "Spec-driven development creates and maintains natural language specifications as an integral, versioned component of software projects." It establishes traceability from business requirements through code to verification mechanisms.

## 5. The 4 skills (full)

### requirement-gathering
**Triggers:** stakeholders submit unclear requests ("new feature", "build me", "implement" without detailed acceptance criteria).
**Process:** 1) review existing documentation; 2) identify spec gaps; 3) conduct one-question-at-a-time interviews; 4) summarize findings addressing scope boundaries, primary workflows, edge cases/error handling, performance/security constraints; 5) obtain explicit stakeholder validation.
**Success:** "Zero ambiguous requirements remain after interview" and the stakeholder confirms the summary is accurate.

### spec-writer
**Triggers:** after requirement-gathering produces confirmed requirements, or when existing specs need updates.
**Six-step workflow:** 1) scope determination — new vs update, one spec per logical feature; 2) YAML frontmatter (`name`, `description`, `targets`); 3) requirements documentation with API contracts; 4) test linking — inline `[@test]` next to relevant requirements; 5) styleguide review; 6) file placement — `specs/` with `.spec.md` extension.
**Quality standards:** concise, scannable, clear headings, specific behavior, granular test files; requirements address edge cases and error handling; test references provide context.

### spec-verification
**Purpose:** detect/resolve mismatches between documented requirements and actual implementation; reports "mismatched targets, broken test links, and undocumented behavioral changes."
**Six-step process:** 1) locate specs in `specs/`; 2) validate structural integrity (paths + test refs resolve); 3) execute linked tests (ensure pass); 4) compare implementation against requirements (read target files); 5) identify drift signals (behavior changes not in specs, orphaned tests, broken references); 6) remediate (update spec or implementation), then re-verify.
**Output:** structured verification report — checked specs, broken links, detected drift, corrective actions. Treats specs as **living documents** reflecting current behavior.

### work-review
**Purpose:** "Review completed implementation to confirm all spec requirements are satisfied and specs remain accurate."
**Phases:** 1) locate relevant specs by matching changed files to spec `targets`; 2) validate each requirement — find implementation evidence with file paths + line numbers; 3) execute linked tests (verify pass before approval); 4) document discovered requirements (new functions, behavioral differences, error handling beyond original scope); 5) update spec metadata for structural changes.
**Output tracks:** checklist of requirements with implementation locations; newly identified requirements beyond original scope; test execution results (pass/fail counts); spec modifications made during review.
**Pass condition:** all requirements verified, linked tests pass, discovered requirements documented in spec.

## 6. The 3 rules (full)

### spec-before-code
**Mandate:** specs must be approved before implementation begins.
**Four steps:** 1) check for existing specs in `specs/`; 2) verify current specs are still accurate (if any); 3) write new specs if none cover the work; 4) get explicit stakeholder approval on the spec before any code.
**Valid approval:** stakeholder confirms "the spec is accurate", or accepts a corrected version.
**Invalid approval:** silence, no response, "just do it" without review, or personal assumptions.
**Permitted shortcuts:** minor corrections preserving existing behavior; urgent production fixes (require retroactive documentation). Pragmatism: don't waste effort searching for a non-existent specs directory.

### one-question-at-a-time
**Scope:** applies exclusively to live interactive requirement gathering with present stakeholders — NOT to written documents, interview-prep materials, or analysis reports.
**Rationale:** single questions yield higher-quality answers; bundled topics produce incomplete responses; sequential questioning lets each answer shape the next.
**Practice:** pose one specific clear question → pause for reply → build the next from that response → continue until clarity.
**Avoid in live settings:** "What about errors, pagination, and auth?"; numbered lists delivered at once; "a few quick questions:" preambles before multiple inquiries.

### spec-format-compliance
**File structure:** `.spec.md` extension + YAML frontmatter with `name` (human-readable), `description` (feature summary), `targets` (≥1 relative path or glob indicating covered code).
**Test link format:** place `[@test]` links inline alongside the requirements they verify, not in separate sections — e.g. `Invalid passwords return 401 `[@test] ../tests/test_auth_invalid_password.py``.
**Organization:** one spec per logical functional unit; reside in `specs/`; use relative paths from the spec file location for targets and test references. Ensures traceability between requirements and test coverage.

## 7. `.spec.md` format & styleguide

**docs/spec-format.md:** "Specs are markdown files that define functional requirements and unit tests that verify correct implementation of those requirements." All use `.spec.md`. Frontmatter: `name`, `description`, `targets` ("a list of relative file paths or glob patterns described by the spec"; "All specs must have at least one target"). `[@test]` notation references verification tests, embedded beside relevant requirements.

**Example:**
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

Invalid passwords return 401 `[@test] tests/test_auth_invalid_password.py`
```

**docs/spec-styleguide.md — five principles:**
1. **Provide context** — markdown text around test links explaining what is checked.
2. **Use headings** — organize related requirements under clear headings.
3. **Be specific** — describe expected behavior, edge cases, constraints.
4. **Granular tests** — `[@test]` next to the requirement; targeted test files per requirement.
5. **Keep synchronized** — specs stay up-to-date with implementation.

## 8. Validation scripts

**validate-specs.sh** — files must end `.spec.md`; must contain YAML frontmatter (`---` delimiters); frontmatter requires `name`, `description`, `targets`; `targets` must have ≥1 entry; warns about `.md` files that look like specs but lack the extension. Output: "OK" / "FAIL" with messages; summary count + exit codes; default directory `./specs`; safe bash (`set -euo pipefail`). (Adapted versions in `scripts/`.)

**check-spec-links.sh** — (1) frontmatter targets: parse `targets:`, verify each file exists, flag patterns matching nothing; (2) `[@test]` links: scan body, confirm referenced files exist relative to the spec's directory. Usage `check-spec-links.sh [specs-directory]` (default `./specs`); per-file OK/BROKEN + summary; `set -euo pipefail`; processes `.spec.md` via `find` with null delimiters.

## 9. Relationship to spec-kit

Independent implementation by Tessl Labs — does **not** reference or build on github/spec-kit. Both promote specification-driven development, but spec-kit is a general-purpose tool/framework with a CLI and slash-command lifecycle, whereas this tile is an agent-steering module (skills + rules + evals). In this SDD skill they are **synthesized**: spec-kit supplies lifecycle structure and artifact generation (its gap: interpersonal requirement discipline); tesslio supplies approval gates, one-question interviewing, and living-spec traceability (its gap: design/plan/tasks decomposition). The two are complementary halves rather than competitors.
