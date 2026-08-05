# spec-kit reference (github/spec-kit)

Complete reference for GitHub's Spec-Driven Development toolkit. Source: `github.com/github/spec-kit` (MIT). This document preserves the conceptual and operational detail so the SDD skill loses no information; read the section you need.

## Table of contents
1. Definition & philosophy
2. Workflow phases & slash commands
3. Per-command internal logic
4. The `specify` CLI
5. Templates (section structure)
6. Constitution — Articles & framework
7. Supported agents/tools
8. Directory structure created
9. Development contexts & experimental goals
10. Extensions / Presets / Workflows systems
11. Project metadata

---

## 1. Definition & philosophy

**Spec-Driven Development (SDD)** makes specifications **executable primary artifacts** rather than secondary documentation: "Specifications don't serve code—code serves specifications." The PRD "isn't a guide for implementation; it's the source that generates implementation."

**Power inversion:** historically code dominated and specs guided. SDD makes specs *directly generative* of implementations. Specs must be "precise, complete, and unambiguous enough to generate working systems."

**Why now — three convergent trends:**
1. **AI capability** — LLMs reliably translate natural-language specs into functional code.
2. **Complexity growth** — multi-service/framework systems make manual alignment hard.
3. **Accelerated change** — organizations pivot fast; regenerable implementations support agility.

**Core tenets:**
1. Specifications as primary artifact — code is the spec expressed in a language/framework; maintenance evolves the spec.
2. Continuous refinement — consistency validation is iterative, not a single gate.
3. Research-driven context — agents gather library compatibility, performance, org constraints.
4. Bidirectional feedback — production metrics/incidents feed spec evolution.
5. Branching for exploration — multiple implementations from one spec.
6. Rich specification via guardrails — templates constrain LLMs toward quality.
7. Multi-step refinement — avoid single-prompt code generation.

---

## 2. Workflow phases & slash commands

**Lean path** (quick experiments): `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`

**Full path** (production): `/speckit.constitution` → `/speckit.specify` → `/speckit.clarify` → `/speckit.checklist` → `/speckit.plan` → `/speckit.tasks` → `/speckit.analyze` → `/speckit.implement`

| Command | Purpose | Output |
|---|---|---|
| `/speckit.constitution` | Establish project principles & governance (immutable foundation) | `.specify/memory/constitution.md` with version tracking |
| `/speckit.specify` | Create feature spec from natural language (WHAT/WHY) | `specs/<prefix>-<short-name>/spec.md` + `checklists/requirements.md` |
| `/speckit.clarify` | Resolve ambiguities via ≤5 targeted questions | spec updated with `## Clarifications` |
| `/speckit.checklist` | Quality checklists validating requirement completeness ("unit tests for requirements") | `checklists/<domain>.md` with CHK-IDs |
| `/speckit.plan` | Implementation plan (tech stack, architecture, artifacts) | `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/` |
| `/speckit.tasks` | Dependency-ordered executable task list | `tasks.md` with T-IDs, `[P]`, `[StoryX]` |
| `/speckit.analyze` | Read-only cross-artifact consistency check | findings table |
| `/speckit.implement` | Execute tasks systematically | source code; tasks marked `[X]` |
| `/speckit.taskstoissues` | Convert tasks → GitHub issues (dependency-ordered) | issues created |
| `/speckit.doctor` | Project health diagnostics | report |

Dependencies: Constitution → Specify (needs description) → Clarify (optional; needs spec) → Checklist (needs spec) → Plan (needs spec + constitution) → Tasks (needs plan + spec) → Analyze (optional; needs all three) → Implement (needs tasks + context).

---

## 3. Per-command internal logic

### `/specify`
1. Parse feature description. 2. Generate 2–4 word short name (e.g. `user-auth`). 3. Create `specs/<prefix>-<short-name>/`. 4. Copy resolved spec template to `spec.md`. 5. Fill User Scenarios, Requirements, Success Criteria, Key Entities, Assumptions. 6. Validate: ≤3 `[NEEDS CLARIFICATION]`; no implementation details; testable requirements; tech-agnostic success criteria. 7. Generate `checklists/requirements.md`. 8. If clarifications remain, present ≤3 critical questions, await answers, update. 9. Run `after_specify` hooks.

### `/plan`
1. Check `hooks.before_plan`. 2. Run setup script; parse JSON for FEATURE_SPEC, IMPL_PLAN, SPECS_DIR, BRANCH. 3. Load spec + `/memory/constitution.md`. 4. **Phase 0 Research**: extract NEEDS CLARIFICATION; research deps/tech choices → `research.md`. 5. **Phase 1 Design**: `data-model.md`, `contracts/`, `quickstart.md`, update agent context. 6. Run `after_plan` hooks. 7. Report branch, plan path, artifacts.

### `/tasks`
1. Run setup; extract FEATURE_DIR, TASKS_TEMPLATE. 2. Load plan.md, spec.md (required); data-model/contracts/research/constitution (optional). 3. Extract tech stack; parse user stories + priorities. 4. Map entities/contracts/decisions to stories. 5. Generate tasks by story (highest priority first); build dependency graph. 6. Output phases Setup → Foundational → User Stories (P1→P2→P3+) → Polish. 7. Each task specific enough for LLM execution.

### `/constitution`
1. Load existing; find `[PLACEHOLDER]` tokens. 2. Collect concrete values. 3. Draft with placeholders resolved. 4. Validate consistency across plan/spec/tasks/templates. 5. Generate Sync Impact Report (version changes, affected files). 6. Validate no unexplained tokens; ISO dates (YYYY-MM-DD); principles testable. 7. Version bump: **MAJOR** (backward-incompatible removals), **MINOR** (new principles), **PATCH** (clarifications).

### `/clarify`
1. Check `hooks.before_clarify`. 2. Load spec; evaluate against 10 taxonomy categories (scope, data model, UX, quality, integration, edge cases, constraints, terminology, completion, misc). 3. Generate ≤5 questions ranked by impact×uncertainty. 4. For each: present recommended option + reasoning; accept letter/yes/"recommended" or custom. 5. Integrate incrementally: create `## Clarifications`, add session subheading, update spec sections atomically. 6. Re-check spec quality checklist. 7. Run `after_clarify` hooks.

### `/analyze`
1. Locate spec.md, plan.md, tasks.md. 2. Load requirements, stories, tasks, constitution principles. 3. Build semantic inventories (FR-/SC- IDs, task↔requirement maps). 4. Five passes: **Duplication**, **Ambiguity** (vague terms w/o metrics, unresolved placeholders), **Underspecification** (missing acceptance criteria/undefined refs), **Constitution conflicts** (MUST violations → auto CRITICAL), **Coverage gaps** (orphan requirements/tasks). 5. Findings table: Category | Severity | Location | Summary | Recommendation (≤50 rows). 6. Coverage summary + metrics + next actions. 7. Run hooks.

### `/implement`
1. Check `hooks.before_implement`. 2. Run script; ensure absolute FEATURE_DIR paths. 3. Review `checklists/` status; halt if incomplete (user may override). 4. Load tasks.md, plan.md (required); data-model/contracts/research/constitution/quickstart (conditional). 5. Create/verify ignore files per detected tech. 6. Parse task phases/deps. 7. Execute by phase (Setup → Tests → Core → Integration → Polish). 8. Respect `[P]`; halt on non-parallel failure. 9. Mark tasks `[X]`. 10. Run `after_implement` hooks. 11. Completion report.

### `/checklist`
1. Env check; parse JSON for feature dir + docs. 2. Load constitution if present. 3. ≤3 contextual clarification questions if ambiguous (≤5 total). 4. Load spec.md (+ optional plan/tasks). 5. Create/append `checklists/[domain].md` with incremental CHK IDs. 6. **CRITICAL: questions evaluate requirement quality, NOT implementation behavior** — ❌ "Verify button clicks"; ✅ "Are visual-hierarchy requirements quantified?". 7. Dimensions: Completeness, Clarity, Consistency, Coverage, Measurability, Edge Cases, Gap, Ambiguity. 8. Traceability: ≥80% items reference spec sections or use gap/conflict markers. 9. Report path, count, focus.

### `/taskstoissues`
1. Check `hooks.before_taskstoissues`. 2. Run script; extract FEATURE_DIR, AVAILABLE_DOCS (absolute). 3. Load constitution (optional). 4. Verify Git remote is GitHub via `git config --get remote.origin.url`. 5. Create issues per task via GitHub MCP. 6. **CRITICAL**: only create issues in the repo matching the remote URL. 7. Run `after_taskstoissues` hooks.

---

## 4. The `specify` CLI

Separate installable tool; the SDD skill performs the workflow directly and treats the CLI as optional tooling. Preserved here for completeness.

**Install:** `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z`

**Core / project:**
- `specify init [<project_name>]` — flags: `--integration <key>`, `--script sh|ps`, `--here`, `--force`, `--ignore-agent-tools`, `--preset <id>`, `--integration-options`
- `specify check` — verify CLI agents installed (offline)
- `specify version` — flags `--features`, `--features --json`, `-V`
- `specify self upgrade` — auto-detect & upgrade

**Integrations:** `integration list` · `integration install <key> [--dev --from <url> --priority <N>]` · `integration switch <key>` · `integration upgrade [<key>]`

**Extensions:** `extension search [query] [--tag --author --verified]` · `add <name> [--dev --from <url> --priority <N>]` · `list` · `remove <name> [--keep-config --force]` · `info <name>` · `update [<name>]` · `enable/disable <name>` · `set-priority <name> <priority>` · `catalog add <url> --name` · `catalog list` · `catalog remove <name>`

**Presets:** `preset search [query]` · `add <preset_id> [--priority <N>]` · `list` · `remove <preset_id>` · `enable/disable <preset_id>` · `set-priority <preset_id> <priority>` · `info <preset_id>` · `resolve <name>` · `catalog add <url> --name`

**Workflows:** `workflow run <source> [-i key=value] [--json]` · `resume <run_id>` · `status [<run_id>]` · `add <source>` · `list` · `search [query]`

**Default behavior:** interactive terminals prompt for integration; non-interactive defaults to GitHub Copilot; one integration active per project (switchable); multiple extensions can run simultaneously.

---

## 5. Templates — section structure

**A) Spec template** (`templates/spec-template.md`)
- Header: feature name, branch ID, creation date, status.
- **User Scenarios & Testing** (mandatory): user stories with priority (P1/P2/P3+); each has title, description, priority justification, independent test approach, Given/When/Then acceptance scenarios, edge cases.
- **Requirements** (mandatory): functional requirements (FR-001+) in MUST language; key entities + attributes; `[NEEDS CLARIFICATION]` markers (max 3).
- **Success Criteria**: measurable outcomes (SC-001+); satisfaction, business impact, performance — tech-agnostic.
- **Assumptions**: audience expectations, scope boundaries, dependencies, data environment.

**B) Plan template** (`templates/plan-template.md`)
- Header metadata: branch, date, spec link.
- Summary: primary requirements + technical approach.
- Technical Context: language/version, dependencies, storage, testing framework, target platform, project type, performance goals, scale/scope.
- **Constitution Check**: validation gate (pre-Phase 0 and post-Phase 1).
- Project Structure: docs hierarchy + 3 source layouts — (1) single project `src/`+`tests/`; (2) web `backend/`+`frontend/`; (3) mobile+API `api/` + iOS/Android.
- Complexity Tracking: table of constitution violations + justifications.
- Artifacts: `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `tasks.md`.

**C) Tasks template** (`templates/tasks-template.md`)
- Format (mandatory): `- [ ] [TaskID] [P?] [Story?] Description with file path`.
- Elements: checkbox `- [ ]`; ID T001…; `[P]` if parallelizable; `[StoryX]` for story phases; description + file path.
- Phases: **Setup → Foundational** ("MUST complete before ANY user story") **→ User Stories** (priority-ordered, independently testable) **→ Polish**.

**D) Constitution template** (`templates/constitution-template.md`)
- Blank blueprint to populate with org-specific values. Five foundational principles (library-first, CLI exposure, test-first, integration testing, observability/versioning/simplicity).
- Sections: Constraints (security, tech stack, compliance); Workflow (review, testing gates, deployment); Governance (amendment procedures, compliance verification). Metadata: version tracking with ratification/amendment dates.

**E) Checklist template** (`templates/checklist-template.md`)
- Header (feature, purpose, date, spec link); category sections; checkbox tasks CHK001…; quality dimensions in brackets `[Completeness]`/`[Clarity]`/…; traceability `[Spec §X.Y]`.
- **CRITICAL constraint**: checklists evaluate the *requirements*, never implementation behavior.

---

## 6. Constitution — Articles & framework

Nine constitutional articles (from `spec-driven.md`):

| Article | Principle | Description |
|---|---|---|
| I | Library-First | Every feature begins as a standalone library; modularity from the start |
| II | CLI Interface Mandate | Libraries expose functionality through text-in/text-out CLIs (JSON for structured data) |
| III | Test-First Imperative | **NON-NEGOTIABLE**: strict TDD; tests validated *failing* before implementation |
| IV | Integration Approaches | Integration and dependency management |
| VII | Simplicity | Max 3 projects initially; more require documented justification |
| VIII | Anti-Abstraction | Use framework features directly rather than wrapping; single model representations |
| IX | Integration-First Testing | Realistic environments with real databases/services, not mocks |

(Articles V and VI exist in the framework's numbering; the published emphasis centers on the above.)

**Enforcement gates:** Phase -1 gates in plan templates operationalize principles as compile-time checks; implementations pass gates or document justified exceptions in Complexity Tracking; violations auto-flagged CRITICAL in `/analyze`.

**Constitutional power:** consistency across time, consistency across LLMs, architectural integrity, quality guarantees (test-first + simplicity → maintainability).

**Beyond the constitution — core development principles:** Observability over opacity · Simplicity over cleverness · Integration over isolation · Modularity over monoliths · Template-driven quality · Hierarchical detail management · Structured self-review.

---

## 7. Supported AI agents/tools

40+ integrations.
- **IDE agents:** Cline, Cursor, Windsurf, Zed, GitHub Copilot, Junie, IBM Bob, Kilo Code, Roo Code, Trae.
- **CLI agents:** Claude Code, Gemini CLI, Devin for Terminal, Goose, Codex, Tabnine CLI, Kiro CLI, Pi Coding Agent, Mistral Vibe, Amp, Qwen Code, opencode, Forge, Auggie, SHAI, RovoDev ACLI, CodeBuddy, Qoder CLI, iFlow CLI.
- **Skills-based (auto-install skills):** Claude Code (`.claude/skills`), Devin (`.devin/skills/`), Codex CLI (`.agents/skills`), Kimi Code, Trae, Lingma, Antigravity.
- ~20 integrations are multi-install-safe (isolated directories). **Generic** integration for unlisted agents: `specify integration install generic --integration-options="--commands-dir <path>"`.

---

## 8. Directory structure created

**`.specify/`**
- `init-options.json` — init config (numbering, integration type)
- `feature.json` — persisted feature directory path
- `integration-catalogs.yml`, `extension-catalogs.yml`, `extensions.yml` (installed extensions + before_*/after_* hooks)
- `extensions/<ext-id>/`, `templates/overrides/`, `presets/`
- `workflows/runs/<run_id>/` — `state.json`, `inputs.json`, `log.jsonl`
- `scripts/` — `setup-*.sh`, `setup-*.ps1`
- `memory/constitution.md` — immutable principles

**`specs/`**
- `<prefix>-<short-name>/` — `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, `tasks.md`, `checklists/requirements.md`, `checklists/<domain>.md`

**Project root**
- `scripts/` (`.sh`/`.ps1`), source dirs (per plan), tech-specific ignore files (`.gitignore`, `.dockerignore`, `.eslintignore`, …).

---

## 9. Development contexts & experimental goals

**Three development contexts:**
1. **0-to-1 (greenfield)** — generate applications from scratch.
2. **Creative exploration** — parallel implementations across stacks; what-if experiments.
3. **Iterative enhancement (brownfield)** — incremental features; legacy modernization.

**Four experimental research dimensions:** Technology independence · Enterprise constraints · User-centric development · Creative iteration.

**Time-savings claim:** ~12 hours of traditional documentation → ~15 minutes for a full feature spec + plan + contracts + data models + test scenarios, versioned in feature branches.

---

## 10. Extensions / Presets / Workflows

**Extensions** — add capabilities/commands (docs, code, process, integration, visibility). Read-only or read+write. Install: `specify extension add <name> [--from <url>]`. Submission: prepare `extension.yml`, create repo w/ README + OSS license + semver, file Extension Submission issue; maintainers verify catalog/manifest (no code audit); 3–7 business days.

**Presets** — customization layers overriding templates/commands/terminology; stackable by priority. **Resolution stack (first match wins):** project-local overrides → installed presets (by priority, lower = higher precedence) → installed extensions → core defaults. Composition strategies: `replace`, `prepend`, `append`, `wrap`. Examples: governance (A11Y, arc42, Zero Trust, iSAQB), creative (fiction, game narrative, screenwriting), technical (AIDE migration, multi-repo branching, Spec2Cloud/Azure, Jira), UX (Claude AskUserQuestion, ToC navigation, command density).

**Workflows** — automate multi-step SDD into repeatable sequences. Built-in **speckit** workflow = specify → plan → tasks → implement with review gates. Step types: `command`, `prompt`, `shell`; `gate`, `if`/`switch`, `while`/`do-while`; `fan-out`/`fan-in`. YAML config, inputs `string`/`number`/`boolean`, expressions `{{ inputs.spec }}` / `{{ steps.specify.output.file }}`, filters `default`/`join`/`contains`/`map`. State persists at `.specify/workflows/runs/<run_id>/`; resumable.

---

## 11. Project metadata

Package `specify-cli` (v0.11.1.dev0), Python ≥3.11, build hatchling, entry point `specify = "specify_cli:main"`. Deps: typer, click, rich, platformdirs, readchar, pyyaml, packaging, pathspec, json5; test: pytest, pytest-cov. License MIT.
