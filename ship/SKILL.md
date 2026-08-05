---
name: ship
description: |
  Fully automated ship workflow — merges base, runs tests, audits coverage, runs
  pre-landing review, bumps VERSION, writes CHANGELOG, updates TODOS.md, splits into
  bisectable commits, pushes, syncs documentation, creates the PR/MR. Use this
  skill whenever the user says "ship it", "ship this", "ship the branch", "make a
  PR", "create a pull request", "open a PR", "release this branch", or finishes a
  feature and is ready to land it. Also triggers on /ship. Proactively invoke when
  the user is on a feature branch and says they're done with the work. Non-
  interactive — only stops for genuine decisions (MINOR/MAJOR version bumps, plan
  items NOT DONE, in-branch test failures, ASK-tier review findings).
---

# Ship: Fully Automated Ship Workflow

You are running the `/ship` workflow. This is a **non-interactive, fully automated** workflow. Do NOT ask for confirmation at any step. The user said `/ship` which means DO IT. Run straight through and output the PR URL at the end.

**Only stop for:**
- On the base branch (abort)
- Merge conflicts that can't be auto-resolved
- In-branch test failures (pre-existing failures are triaged, not auto-blocking)
- Pre-landing review finds ASK items that need user judgment
- MINOR or MAJOR version bump needed
- AI-assessed coverage below minimum threshold
- Plan items NOT DONE with no user override
- Plan verification failures
- TODOS.md missing/disorganized and user wants action

**Never stop for:**
- Uncommitted changes (always include them)
- Version bump choice for MICRO or PATCH (auto-pick)
- CHANGELOG content (auto-generate)
- Commit message approval (auto-commit)
- Multi-file changesets (auto-split into bisectable commits)
- Auto-fixable review findings

**Re-run behavior (idempotency):** Re-running `/ship` means "run the whole checklist again." Every verification step runs on every invocation. Only *actions* are idempotent: skip the VERSION bump if already bumped, skip the push if up to date, update the PR body instead of creating a new PR.

---

## Step 0: Detect platform and base branch

Detect the platform (GitHub via `gh`, GitLab via `glab`, or git-native). Determine the base branch via `gh pr view --json baseRefName -q .baseRefName`, `glab mr view -F json` → `target_branch`, or `git symbolic-ref refs/remotes/origin/HEAD`. Substitute everywhere subsequent steps say `<base>`.

---

## Step 1: Pre-flight

1. Check the current branch. If on the base branch, **abort**: "You're on the base branch. Ship from a feature branch."

2. Run `git status` (never use `-uall`). Uncommitted changes are always included.

3. Run `git diff <base>...HEAD --stat` and `git log <base>..HEAD --oneline` to understand what's being shipped.

4. Check whether prior reviews exist on this branch. Display a readiness summary. If no prior review exists, note: "No prior eng review found — ship will run its own pre-landing review in Step 9." If the diff is large (>200 lines), suggest running an architecture review first.

---

## Step 2: Distribution Pipeline Check

If the diff introduces a new standalone artifact (CLI binary, library package, tool), verify a release workflow exists. Check:

```bash
git diff origin/<base> --name-only | grep -E '(cmd/.*/main\.go|bin/|Cargo\.toml|setup\.py|package\.json)' | head -5
ls .github/workflows/ 2>/dev/null | grep -iE 'release|publish|dist'
```

**If no release pipeline exists and a new artifact was added:** Ask:
- A) Add a release workflow now
- B) Defer — add to TODOS.md
- C) Not needed — internal/web-only

If release pipeline exists, continue silently.

---

## Step 3: Merge the base branch (BEFORE tests)

Fetch and merge the base branch into the feature branch so tests run against merged state:

```bash
git fetch origin <base> && git merge origin/<base> --no-edit
```

**If merge conflicts:** Try to auto-resolve simple cases (VERSION, schema.rb, CHANGELOG ordering). If complex, **STOP** and show conflicts.

---

## Step 4: Test Framework Bootstrap

Detect existing test framework (`jest.config.*`, `vitest.config.*`, `.rspec`, `pytest.ini`, etc.) and project runtime (`Gemfile`, `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`).

**If test framework detected:** Print "Test framework detected — skipping bootstrap." Read 2-3 existing test files to learn conventions.

**If no runtime:** Ask the user what runtime, or accept "this project doesn't need tests" and write a marker.

**If runtime detected but no test framework — bootstrap:** Use WebSearch or the built-in table to pick a framework, install packages (pnpm/npm/gem/pip/etc.), create config, create test directory, generate 3-5 real tests for recently changed files, verify, create `.github/workflows/test.yml` for GitHub-hosted repos, update or create TESTING.md and append a `## Testing` section to CLAUDE.md, then commit `chore: bootstrap test framework`.

---

## Step 5: Run tests (on merged code)

Run the project's test command and check pass/fail.

**If any test fails:** Apply the Test Failure Ownership Triage:

### Test Failure Ownership Triage

For each failing test, classify:

1. **In-branch** if: the failing test file was modified on this branch, OR the test references code changed on this branch, OR you can trace the failure to a branch change.
2. **Likely pre-existing** if: neither the test nor its target was modified on this branch AND the failure is unrelated to any branch change.
3. **When ambiguous, default to in-branch.** Safer to stop than to ship broken tests.

**In-branch failures: STOP.** The developer must fix their own broken tests.

**Pre-existing failures:**

If this is a solo repo, ask:
- A) Investigate and fix now (recommended)
- B) Add as P0 TODO
- C) Skip — ship anyway

If collaborative, ask:
- A) Fix now anyway
- B) Blame + assign issue to the author who broke it (recommended)
- C) Add as P0 TODO
- D) Skip

For "Blame + assign", check who last touched both the test AND the production code (production-code author usually broke it). Create an issue:

```bash
gh issue create --title "Pre-existing test failure: <test-name>" --body "..." --assignee "<github-username>"
```

After triage: if in-branch failures remain unfixed, **STOP**. Otherwise continue.

---

## Step 6: Eval Suites (conditional)

If the diff touches prompt-related files (`*_prompt_builder.rb`, `*_generation_service.rb`, `config/system_prompts/*.txt`, `test/evals/**/*`, etc.), run the affected eval suites at the full tier (pre-merge gate). Map runner → test file by grepping `PROMPT_SOURCE_FILES` declarations. Run sequentially — if the first fails, stop.

If no prompt files in diff: skip silently.

---

## Step 7: Test Coverage Audit

**Dispatch this step as a subagent** (general-purpose). The subagent runs in fresh context — parent sees only the conclusion. This is context-rot defense.

**Subagent prompt:** "You are running a ship-workflow test coverage audit. Run `git diff <base>...HEAD` as needed. Do not commit. 100% coverage is the goal — every untested path is where bugs hide."

### Test Framework Detection

Read CLAUDE.md `## Testing` section for the authoritative command and framework. If absent, auto-detect via config files.

**0. Before/after test count.** Save the count for the PR body.

**1. Trace every codepath changed:**

Read every changed file. For each, trace data flow — don't just list functions, follow the execution:
- Where does input come from? (request params, props, DB, API)
- What transforms it? (validation, mapping, computation)
- Where does it go? (DB write, API response, rendered output)
- What can go wrong? (null/undefined, invalid input, network failure)

Diagram every changed file with every conditional branch (if/else, switch, ternary, guard clause, early return), every error path, every call to another function, every edge.

**2. Map user flows, interactions, and error states:**

- **User flows:** Full sequence of actions touching this code
- **Interaction edge cases:** Double-click, navigate-away, stale data, slow connection, concurrent actions
- **Error states:** Clear message vs silent failure, recoverable vs stuck, network/server errors
- **Empty/boundary states:** Zero results, 10000 results, single character, max length

**3. Check each branch against existing tests.** Quality scoring:
- ★★★ Tests behavior with edge cases AND error paths
- ★★ Tests correct behavior, happy path only
- ★ Smoke test / existence check / trivial assertion

### E2E Test Decision Matrix

| Mark | When |
|------|------|
| **[→E2E]** | Common user flow spanning 3+ components, integration where mocking hides failures, auth/payment/data-destruction |
| **[→EVAL]** | LLM call needing quality eval, prompt template changes |
| **Unit** | Pure function, internal helper, edge case of single function |

### REGRESSION RULE (mandatory)

When the audit identifies a **regression** (code that worked before, broken by this diff, not covered by existing tests), a regression test is written immediately. No asking. No skipping. Format: `test: regression test for {what broke}`.

**4. Output ASCII coverage diagram:**

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

COVERAGE: 5/13 paths tested (38%)  |  Code paths: 3/5 (60%)  |  User flows: 2/8 (25%)
QUALITY: ★★★:2 ★★:2 ★:1  |  GAPS: 8 (2 E2E, 1 eval)
```

**Fast path:** All paths covered → "All new code paths have test coverage." Continue.

**5. Generate tests for uncovered paths.** Prioritize error handlers and edge cases first. Read 2-3 existing test files to match conventions. Mock external dependencies. Run each test, commit passing tests as `test: coverage for {feature}`, revert failures.

Caps: 30 code paths max, 20 tests max, 2-min per-test exploration.

**6. Coverage gate.** Read CLAUDE.md for `## Test Coverage` with Minimum/Target percentages. Defaults: Minimum=60%, Target=80%.

- **>= target:** Pass. Continue.
- **>= minimum, < target:** Ask:
  - A) Generate more tests (recommended)
  - B) Ship anyway — accept coverage risk
  - C) These paths don't need tests — mark intentionally uncovered
- **< minimum:** Ask:
  - A) Generate tests (recommended)
  - B) Override — ship with low coverage

Maximum 2 generation passes total.

---

## Step 8: Plan Completion Audit

**Dispatch as a subagent** (general-purpose). Parent gets only the conclusion.

The subagent:
1. Discovers the plan file (conversation context first, then `.plans/*.md`, `~/.claude/plans/*.md`)
2. Extracts actionable items (checkboxes, numbered steps, imperative statements, file specs, test requirements, data model changes). Caps at 50.
3. Classifies each item's verification mode:
   - **DIFF-VERIFIABLE** — cross-reference against `git diff`
   - **CROSS-REPO** — check `[ -f <path> ]` on reachable sibling roots
   - **EXTERNAL-STATE** — Always UNVERIFIABLE; cite manual check
   - **CONTENT-SHAPE in another repo** — try project-detected validator (`validate-*`, `lint-wiki`, `check-docs`) first
4. Classifies each item: DONE / PARTIAL / NOT DONE / CHANGED / UNVERIFIABLE
5. Path concreteness: concrete paths MUST be DONE or NOT DONE via `[ -f <path> ]`. UNVERIFIABLE only for genuinely abstract paths.
6. **Honesty rule:** Don't call something DONE just because related code shipped. Code that *handles* a deliverable is not the deliverable. When in doubt, prefer UNVERIFIABLE.

Output: `PLAN COMPLETION AUDIT` with sections per category and `COMPLETION: X/Y DONE, M PARTIAL, K NOT DONE, J CHANGED, L UNVERIFIABLE`.

### Gate Logic

1. **Any NOT DONE items:** Ask:
   - A) Stop — implement missing items
   - B) Ship anyway — defer to P1 TODOs
   - C) Intentionally dropped

2. **Any UNVERIFIABLE items:** Loop through one at a time, with the item's *specific* manual check. **Per-item confirmation is mandatory** — do NOT blanket-confirm. Options per item: Y (confirmed done, cite what you verified), N (not done — block ship), D (intentionally dropped). If more than 5 UNVERIFIABLE, present numbered list and offer: (1) confirm each, (2) stop and reduce scope, (3) blanket-confirm with explicit warning.

3. **Only PARTIAL items:** Continue with note in PR body. Not blocking.

4. **All DONE or CHANGED:** Pass.

---

## Step 8.1: Plan Verification

Automatically verify the plan's testing/verification steps using a headless browser.

1. Look for `## Verification`, `## Test plan`, `## Testing`, `## How to test`, or `## Manual testing` in the plan file.
2. Check for a running dev server on common ports (3000, 8080, 5173, 4000).
3. If found, run the plan's verification items against the dev server using a headless browser (Playwright, gstack browse CLI, or equivalent).
4. Gate:
   - All PASS → continue silently
   - Any FAIL → ask: A) Fix before shipping (recommended for functional issues), B) Ship anyway (cosmetic only)
   - No section / no server → skip non-blocking

Add `## Verification Results` to the PR body.

---

## Step 8.2: Scope Drift Detection

Same as `/review`'s scope drift check. Read TODOS.md, PR description, commit messages. Identify stated intent vs delivered. Report:

```
Scope Check: [CLEAN / DRIFT DETECTED / REQUIREMENTS MISSING]
Intent: <1-line summary>
Delivered: <1-line summary>
```

Informational — doesn't block.

---

## Step 9: Pre-Landing Review

Review the diff for structural issues. Two passes:
- **Pass 1 (CRITICAL):** SQL & Data Safety, LLM Output Trust Boundary, Shell Injection, Race Conditions, Enum Completeness
- **Pass 2 (INFORMATIONAL):** Async/Sync, Column Names, LLM Prompts, Type Coercion, View/Frontend, Time Windows, Distribution & CI/CD

Every finding requires a confidence score (1-10):

| Score | Display |
|-------|---------|
| 9-10 | Show normally |
| 7-8 | Show normally |
| 5-6 | Show with caveat |
| 3-4 | Appendix only |
| 1-2 | Suppress unless P0 |

### Design Review (conditional, frontend-only diffs)

If the diff touches frontend files, read DESIGN.md (or design-system.md), apply universal design principles, and flag mechanical CSS issues (`outline: none`, `!important`, `font-size < 16px`) as AUTO-FIX. Design judgment calls become ASK items.

### Step 9.1: Specialist Dispatch

For larger diffs (>50 lines), dispatch specialist reviewers in parallel as subagents. Each has fresh context. Specialists:

- **Testing** (always-on) — coverage gaps, missing edge cases
- **Maintainability** (always-on) — naming, complexity, dead code
- **Security** — if auth/backend touched
- **Performance** — if backend or frontend touched
- **Data Migration** — if migrations touched
- **API Contract** — if API touched
- **Design** — if frontend touched

Each specialist's prompt: "You are a specialist code reviewer. Run `git diff origin/<base>`. Apply the {domain} checklist. For each finding, output a JSON object per line: `{\"severity\":\"CRITICAL|INFORMATIONAL\",\"confidence\":N,\"path\":\"file\",\"line\":N,\"category\":\"...\",\"summary\":\"...\",\"fix\":\"...\",\"specialist\":\"name\"}`. If no findings: output `NO FINDINGS`."

**Merge findings:** Compute fingerprint `{path}:{line}:{category}`, deduplicate, boost confidence +1 for multi-specialist matches.

**PR Quality Score:** `max(0, 10 - (critical_count * 2 + informational_count * 0.5))`

### Red Team dispatch (conditional)

Activate if diff > 200 lines OR any specialist produced a CRITICAL finding. The Red Team subagent receives the merged findings and looks for what they MISSED.

### Step 9.3: Fix-First flow

1. Classify each finding as AUTO-FIX or ASK
2. Auto-fix AUTO-FIX items: `[AUTO-FIXED] [file:line] Problem → what you did`
3. If ASK items remain, present in ONE batched question
4. Apply user-approved fixes
5. If ANY fixes applied: commit and **STOP** — tell the user to run `/ship` again to re-test
6. If no fixes: continue to Step 12

---

## Step 10: Address review-bot comments (if PR exists)

**Dispatch as a subagent** to fetch and classify (Greptile, CodeRabbit, etc.). Classifications: VALID & ACTIONABLE, VALID BUT ALREADY FIXED, FALSE POSITIVE, SUPPRESSED.

For each VALID & ACTIONABLE comment: ask A) Fix now, B) Acknowledge and ship, C) False positive. If user chose Fix, apply, commit, reply with diff + explanation.

For FALSE POSITIVE: ask A) Reply explaining why, B) Fix anyway, C) Ignore.

For VALID BUT ALREADY FIXED: reply automatically with what was done and the fixing SHA.

If fixes applied, re-run tests (Step 5) before continuing.

---

## Step 11: Adversarial review (always-on)

Every diff gets adversarial review. LOC is not a proxy for risk.

### Claude adversarial subagent (always runs)

Dispatch via the Agent tool with fresh context. Prompt: "Read `git diff origin/<base>`. Think like an attacker and a chaos engineer. Find ways this code will fail in production: edge cases, race conditions, security holes, resource leaks, silent data corruption, error handling that swallows failures, trust boundary violations. No compliments — just the problems. End with `Recommendation: <action> because <one-line reason naming the most exploitable finding>`."

FIXABLE findings flow into the Fix-First pipeline. INVESTIGATE findings are informational.

### Cross-model adversarial (large diffs, 200+ lines)

If a second LLM (e.g., Codex) is available and the diff is >= 200 lines, run a structured cross-model review with a P1 gate. Check for `[P1]` markers — found → GATE: FAIL, not found → GATE: PASS.

On FAIL, ask:
- A) Investigate and fix now (recommended)
- B) Continue — review will still complete

---

## Step 12: Version bump (auto-decide)

**Idempotency check.** Compare `VERSION` against base branch and `package.json` version:
- **FRESH** → proceed with bump
- **ALREADY_BUMPED** → skip the bump (still verify against queue drift)
- **DRIFT_STALE_PKG** → sync package.json only, no re-bump
- **DRIFT_UNEXPECTED** → STOP and report manual reconciliation needed

### Auto-decide bump level

Based on the diff:
- **MICRO** (4th digit): < 50 lines changed, trivial tweaks, typos, config
- **PATCH** (3rd digit): 50+ lines changed, no feature signals
- **MINOR** (2nd digit): **ASK** if feature signals detected (new routes/pages, new DB migrations, new test files alongside new source) OR 500+ lines OR new modules
- **MAJOR** (1st digit): **ASK** — milestones or breaking changes only

Write the new version to both `VERSION` and `package.json`. Validate format: `MAJOR.MINOR.PATCH.MICRO`.

---

## Step 13: CHANGELOG (auto-generate)

1. Read `CHANGELOG.md` header for format.
2. Enumerate every commit on the branch: `git log <base>..HEAD --oneline`. Count them — this is your checklist.
3. Read the full diff: `git diff <base>...HEAD`.
4. Group commits by theme (features, performance, fixes, cleanup, infrastructure, refactoring).
5. Write the entry covering ALL groups. Categorize into `### Added`, `### Changed`, `### Fixed`, `### Removed`. Insert after the file header, dated today, format `## [X.Y.Z.W] - YYYY-MM-DD`. **Voice:** Lead with what the user can now **do** that they couldn't before. Plain language, no implementation details.
6. **Cross-check:** Every commit must map to at least one bullet. If unrepresented, add it now.

Do NOT ask the user to describe changes — infer from diff and commits.

---

## Step 14: TODOS.md (auto-update)

1. Check if `TODOS.md` exists. If not, ask A) Create it now or B) Skip.
2. Check structure (component groupings, P0-P4 priority fields, `## Completed` section at bottom). If disorganized, ask A) Reorganize (recommended) or B) Leave as-is.
3. **Detect completed TODOs** — fully automatic, no user interaction. For each TODO, check if commit messages match, files referenced appear in diff, or described work matches functional changes. **Be conservative** — only mark complete with clear evidence.
4. Move completed items to `## Completed` section. Append: `**Completed:** vX.Y.Z (YYYY-MM-DD)`
5. Output summary for PR body.

---

## Step 15: Commit (bisectable chunks)

### Step 15.0: WIP Commit Squash (continuous checkpoint mode only)

If the branch has `WIP:` auto-checkpoint commits, squash them INTO logical commits before bisectable grouping. Preserve non-WIP commits.

**Detection:**
```bash
WIP_COUNT=$(git log <base>..HEAD --oneline --grep="^WIP:" 2>/dev/null | wc -l)
```

**Non-destructive squash:** NEVER blind `git reset --soft` if there are non-WIP commits. Use `git rebase -i $(git merge-base HEAD origin/<base>) --exec 'true' -X ours` to squash WIP commits via fixup. Only use `reset --soft` if the entire branch is WIP commits.

### Step 15.1: Bisectable Commits

Group changes into logical commits — each represents ONE coherent change. Order earlier dependencies first:

1. **Infrastructure** — migrations, config, route additions
2. **Models & services** (with their tests)
3. **Controllers & views** (with their tests)
4. **VERSION + CHANGELOG + TODOS.md** — always in the final commit

**Rules:**
- A model and its test go in the same commit
- Migrations are their own commit (or grouped with their model)
- Each commit must be independently valid (no broken imports)
- If total diff is small (< 50 lines across < 4 files), a single commit is fine

Commit message format: `<type>: <summary>` (feat/fix/chore/refactor/docs). The final commit (VERSION + CHANGELOG) gets the version tag.

---

## Step 16: Verification Gate

**IRON LAW: NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

Before pushing, re-verify if code changed during Steps 4-11:

1. **Test verification:** If ANY code changed after Step 5's test run (review fixes, CHANGELOG edits don't count), re-run tests. Paste fresh output.
2. **Build verification:** If the project has a build step, run it.

**Rationalization prevention:**
- "Should work now" → RUN IT.
- "I'm confident" → Confidence is not evidence.
- "I already tested earlier" → Code changed. Test again.
- "It's a trivial change" → Trivial changes break production.

**If tests fail here:** STOP. Do not push.

---

## Step 17: Push

**Idempotency check:**

```bash
git fetch origin <branch-name> 2>/dev/null
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/<branch-name> 2>/dev/null || echo "none")
[ "$LOCAL" = "$REMOTE" ] && echo "ALREADY_PUSHED" || echo "PUSH_NEEDED"
```

If `ALREADY_PUSHED`, skip but continue to Step 18. Otherwise:

```bash
git push -u origin <branch-name>
```

You are NOT done. Documentation sync and PR creation are mandatory.

---

## Step 18: Documentation sync

Run a documentation sync workflow — update README, CHANGELOG cross-references, CLAUDE.md, ARCHITECTURE.md, and any other docs affected by the diff. This step ideally runs as a subagent with fresh context. The subagent should respect doc exclusion lists, risky-change gates, and clobber protection on CHANGELOG.

Output: list of files updated, the commit SHA, and a markdown block for the PR body's `## Documentation` section.

---

## Step 19: Create PR/MR

**Idempotency check:** if an open PR/MR exists, update the body and title instead of creating a new one.

**Title format:** ALWAYS starts with `v$NEW_VERSION`: `v<NEW_VERSION> <type>: <summary>`. No exceptions.

**PR/MR body structure:**

```markdown
## Summary
<Enumerate every substantive commit. Group by logical sections.>

## Test Coverage
<Coverage diagram from Step 7, or "All new code paths have test coverage.">
<Tests: {before} → {after} (+{delta} new)>

## Pre-Landing Review
<Findings from Step 9, or "No issues found.">

## Design Review
<Lite design check results, or skip if no frontend files>

## Eval Results
<Suite names, pass/fail counts. Skip if no prompt files.>

## Review Bot
<If Greptile/CodeRabbit comments: bullet list with [FIXED] / [FALSE POSITIVE] / [ALREADY FIXED] tags>

## Scope Drift
<If scope drift ran: "Scope Check: CLEAN" or list of findings>

## Plan Completion
<Completion checklist summary from Step 8>

## Verification Results
<Step 8.1 summary, or reason for skipping>

## TODOS
<Items marked complete with version, or "No TODO items completed">

## Documentation
<Documentation section from Step 18>

## Test plan
- [x] All tests pass (N runs, 0 failures)

🤖 Generated with Claude Code
```

**GitHub:**
```bash
gh pr create --base <base> --title "v$NEW_VERSION <type>: <summary>" --body "$(cat <<'EOF'
<PR body>
EOF
)"
```

**GitLab:**
```bash
glab mr create -b <base> -t "v$NEW_VERSION <type>: <summary>" -d "$(cat <<'EOF'
<MR body>
EOF
)"
```

**If neither CLI available:** Print branch name, remote URL, and instruct manual PR creation via the web UI. Do not stop — the code is pushed.

Output the PR/MR URL.

---

## Important Rules

- **Never skip tests.** If tests fail, stop.
- **Never skip the pre-landing review.**
- **Never force push.** Use regular `git push` only.
- **Never ask for trivial confirmations** (e.g., "ready to push?"). DO stop for version bumps (MINOR/MAJOR), pre-landing review ASK items, and cross-model [P1] findings.
- **Always use the 4-digit version format** from VERSION.
- **Date format in CHANGELOG:** `YYYY-MM-DD`
- **Split commits for bisectability** — each commit = one logical change.
- **TODOS.md completion detection must be conservative.**
- **Never push without fresh verification evidence.** If code changed after Step 5 tests, re-run before pushing.
- **Step 7 generates coverage tests.** They must pass before committing. Never commit failing tests.
- **The goal is:** user says `/ship`, next thing they see is the review + PR URL + auto-synced docs.
