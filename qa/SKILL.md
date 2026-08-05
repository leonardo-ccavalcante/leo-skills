---
name: qa
description: |
  Full test-fix-verify QA loop. Acts as both QA engineer and bug-fix engineer —
  tests web applications like a real user, fixes any bugs found with atomic commits,
  then re-verifies and writes regression tests. Use this skill whenever the user says
  "qa this", "run qa", "test and fix", "test the site", "does this work?", asks to
  verify a feature works in the browser, or wants end-to-end testing with fixes
  applied. Also triggers on /qa. Proactively invoke when the user just shipped code
  on a feature branch and wants to verify it works. For report-only (no fixes), use
  /qa-only instead.
---

# QA: Test → Fix → Verify

You are a QA engineer AND a bug-fix engineer. Test web applications like a real user — click everything, fill every form, check every state. When you find bugs, fix them in source code with atomic commits, then re-verify. Produce a structured report with before/after evidence.

This skill requires a headless browser tool. Use Playwright, the gstack `browse` CLI, or any equivalent that can navigate, click, fill, screenshot, and read the console. Throughout this document, `$B` represents the browser command — substitute your tool's actual invocation.

---

## Step 0: Detect platform and base branch

Detect the git hosting platform from the remote URL:

```bash
git remote get-url origin 2>/dev/null
```

- If the URL contains "github.com" → platform is **GitHub** (`gh` CLI)
- If the URL contains "gitlab" → platform is **GitLab** (`glab` CLI)
- Otherwise check `gh auth status` / `glab auth status`, fall back to git-native commands

Determine the base branch:

**GitHub:** `gh pr view --json baseRefName -q .baseRefName`, fall back to `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
**GitLab:** `glab mr view -F json` → `target_branch`, fall back to `glab repo view -F json` → `default_branch`
**Git-native fallback:** `git symbolic-ref refs/remotes/origin/HEAD | sed 's|refs/remotes/origin/||'`, then `main`, then `master`.

In every subsequent `git diff`, `git log`, `git fetch`, `git merge`, and PR/MR command, substitute the detected branch name wherever the instructions say "the base branch".

---

## Setup

**Parse the user's request for these parameters:**

| Parameter | Default | Override example |
|-----------|---------|-----------------:|
| Target URL | (auto-detect or required) | `https://myapp.com`, `http://localhost:3000` |
| Tier | Standard | `--quick`, `--exhaustive` |
| Mode | full | `--regression baseline.json` |
| Output dir | `.qa-reports/` | `Output to /tmp/qa` |
| Scope | Full app (or diff-scoped) | `Focus on the billing page` |
| Auth | None | `Sign in to user@example.com`, `Import cookies from cookies.json` |

**Tiers determine which issues get fixed:**
- **Quick:** Fix critical + high severity only
- **Standard:** + medium severity (default)
- **Exhaustive:** + low/cosmetic severity

**If no URL is given and you're on a feature branch:** Automatically enter **diff-aware mode** (see Modes below).

**Check for clean working tree:**

```bash
git status --porcelain
```

If the output is non-empty (working tree is dirty), **STOP** and ask:

"Your working tree has uncommitted changes. /qa needs a clean tree so each bug fix gets its own atomic commit."

- A) Commit my changes — commit all current changes with a descriptive message, then start QA
- B) Stash my changes — stash, run QA, pop the stash after
- C) Abort — I'll clean up manually

RECOMMENDATION: Choose A because uncommitted work should be preserved as a commit before QA adds its own fix commits.

---

## Test Framework Bootstrap

**Detect existing test framework and project runtime:**

```bash
setopt +o nomatch 2>/dev/null || true  # zsh compat
# Detect project runtime
[ -f Gemfile ] && echo "RUNTIME:ruby"
[ -f package.json ] && echo "RUNTIME:node"
[ -f requirements.txt ] || [ -f pyproject.toml ] && echo "RUNTIME:python"
[ -f go.mod ] && echo "RUNTIME:go"
[ -f Cargo.toml ] && echo "RUNTIME:rust"
[ -f composer.json ] && echo "RUNTIME:php"
[ -f mix.exs ] && echo "RUNTIME:elixir"
# Detect sub-frameworks
[ -f Gemfile ] && grep -q "rails" Gemfile 2>/dev/null && echo "FRAMEWORK:rails"
[ -f package.json ] && grep -q '"next"' package.json 2>/dev/null && echo "FRAMEWORK:nextjs"
# Check for existing test infrastructure
ls jest.config.* vitest.config.* playwright.config.* .rspec pytest.ini pyproject.toml phpunit.xml 2>/dev/null
ls -d test/ tests/ spec/ __tests__/ cypress/ e2e/ 2>/dev/null
```

**If test framework detected:** Print "Test framework detected: {name}. Skipping bootstrap." Read 2-3 existing test files to learn conventions (naming, imports, assertion style). Use these conventions when writing regression tests.

**If NO runtime detected:** Ask the user what runtime they use; if they say "this project doesn't need tests", note that and continue without tests.

**If runtime detected but no test framework — bootstrap:**

### B2. Research best practices

WebSearch for current best practices for the detected runtime, or use this built-in table:

| Runtime | Primary recommendation | Alternative |
|---------|----------------------|-------------|
| Ruby/Rails | minitest + fixtures + capybara | rspec + factory_bot + shoulda-matchers |
| Node.js | vitest + @testing-library | jest + @testing-library |
| Next.js | vitest + @testing-library/react + playwright | jest + cypress |
| Python | pytest + pytest-cov | unittest |
| Go | stdlib testing + testify | stdlib only |
| Rust | cargo test (built-in) + mockall | — |
| PHP | phpunit + mockery | pest |
| Elixir | ExUnit (built-in) + ex_machina | — |

### B3-B4. Framework selection and install

Ask user A) Primary B) Alternative C) Skip. If C, write a `.no-test-bootstrap` marker and continue without tests.

Install the chosen packages (pnpm/npm/gem/pip/etc.), create config, create test directory, create one example test verifying setup works.

### B4.5. First real tests

Generate 3-5 real tests for existing code:

1. **Find recently changed files:** `git log --since=30.days --name-only --format="" | sort | uniq -c | sort -rn | head -10`
2. **Prioritize by risk:** Error handlers > business logic with conditionals > API endpoints > pure functions
3. **For each file:** Write one test that tests real behavior with meaningful assertions. Never `expect(x).toBeDefined()` — test what the code DOES.
4. Run each test. Passes → keep. Fails → fix once. Still fails → delete silently.

Never import secrets, API keys, or credentials in test files.

### B5. Verify

```bash
{detected test command}
```

If tests fail → debug once. If still failing → revert all bootstrap changes and warn user.

### B5.5. CI/CD pipeline

Check CI provider:
```bash
ls -d .github/ 2>/dev/null && echo "CI:github"
```

If `.github/` exists (or no CI detected — default to GitHub Actions): Create `.github/workflows/test.yml` with the appropriate setup action for the runtime and the verified test command.

### B6-B7. Document

Update or create `TESTING.md` with framework, run command, conventions. Append a `## Testing` section to `CLAUDE.md` if it doesn't already have one.

### B8. Commit

```bash
git status --porcelain
git commit -m "chore: bootstrap test framework ({framework name})"
```

---

## Modes

### Diff-aware (automatic when on a feature branch with no URL)

The **primary mode** for developers verifying their work. Same as /qa-only's diff-aware mode:

1. Analyze the branch diff (`git diff main...HEAD --name-only`, `git log main..HEAD --oneline`)
2. Identify affected pages/routes from the changed files
3. Detect the running app (try localhost:3000, :4000, :8080)
4. Test each affected page/route — navigate, screenshot, check console, test interactions
5. Cross-reference with commit messages and PR description for *intent*
6. Check TODOS.md for known bugs related to changed files
7. Report findings scoped to the branch

**If no obvious pages/routes are identified from the diff:** Fall back to Quick mode — navigate to homepage, follow top 5 navigation targets, check console, test interactive elements. Always verify the app still works.

### Full (default when URL is provided)
Systematic exploration. Visit every reachable page. Document 5-10 well-evidenced issues. 5-15 minutes.

### Quick (`--quick`)
30-second smoke test. Homepage + top 5 nav targets. Page loads? Console errors? Broken links?

### Regression (`--regression <baseline>`)
Run full mode, then diff against a previous baseline.json. Health score delta, fixed vs new issues.

---

## Phases 1-6: QA Baseline

Same as /qa-only. Initialize, authenticate (if needed), orient, explore, document each issue immediately with screenshots, wrap up with health score.

Use the health score rubric from /qa-only (Console 15%, Links 10%, Visual 10%, Functional 20%, UX 15%, Performance 10%, Content 5%, Accessibility 15%).

Record baseline health score at end of Phase 6.

---

## Phase 7: Triage

Sort all discovered issues by severity, then decide which to fix based on the selected tier:

- **Quick:** Fix critical + high only. Mark medium/low as "deferred."
- **Standard:** Fix critical + high + medium. Mark low as "deferred."
- **Exhaustive:** Fix all, including cosmetic/low severity.

Mark issues that cannot be fixed from source code (e.g., third-party widget bugs, infrastructure issues) as "deferred" regardless of tier.

---

## Phase 8: Fix Loop

For each fixable issue, in severity order:

### 8a. Locate source

```bash
# Grep for error messages, component names, route definitions
# Glob for file patterns matching the affected page
```

- Find the source file(s) responsible for the bug
- ONLY modify files directly related to the issue

### 8b. Fix

- Read the source code, understand the context
- Make the **minimal fix** — smallest change that resolves the issue
- Do NOT refactor surrounding code, add features, or "improve" unrelated things

### 8c. Commit

```bash
git add <only-changed-files>
git commit -m "fix(qa): ISSUE-NNN — short description"
```

- One commit per fix. Never bundle multiple fixes.

### 8d. Re-test

- Navigate back to the affected page
- Take **before/after screenshot pair**
- Check console for errors
- Use `snapshot -D` to verify the change had the expected effect

```bash
$B goto <affected-url>
$B screenshot "$REPORT_DIR/screenshots/issue-NNN-after.png"
$B console --errors
$B snapshot -D
```

### 8e. Classify

- **verified**: re-test confirms the fix works, no new errors introduced
- **best-effort**: fix applied but couldn't fully verify (e.g., needs auth state, external service)
- **reverted**: regression detected → `git revert HEAD` → mark issue as "deferred"

### 8e.5. Regression Test

Skip if: classification is not "verified", OR the fix is purely visual/CSS with no JS behavior, OR no test framework was detected AND user declined bootstrap.

**1. Study the project's existing test patterns:**

Read 2-3 test files closest to the fix. Match exactly: file naming, imports, assertion style, describe/it nesting, setup/teardown patterns. The regression test must look like it was written by the same developer.

**2. Trace the bug's codepath, then write a regression test:**

Before writing the test, trace the data flow through the code you just fixed:
- What input/state triggered the bug? (the exact precondition)
- What codepath did it follow? (which branches, which function calls)
- Where did it break? (the exact line/condition that failed)
- What other inputs could hit the same codepath? (edge cases around the fix)

The test MUST:
- Set up the precondition that triggered the bug
- Perform the action that exposed the bug
- Assert the correct behavior (NOT "it renders" or "it doesn't throw")
- If you found adjacent edge cases while tracing, test those too
- Include full attribution comment:
  ```
  // Regression: ISSUE-NNN — {what broke}
  // Found by /qa on {YYYY-MM-DD}
  ```

Test type decision:
- Console error / JS exception / logic bug → unit or integration test
- Broken form / API failure / data flow bug → integration test with request/response
- Visual bug with JS behavior (broken dropdown, animation) → component test
- Pure CSS → skip (caught by QA reruns)

Mock all external dependencies (DB, API, Redis, file system).

Use auto-incrementing names to avoid collisions: check existing `{name}.regression-*.test.{ext}` files, take max number + 1.

**3. Run only the new test file:**

```bash
{detected test command} {new-test-file}
```

**4. Evaluate:**
- Passes → commit: `git commit -m "test(qa): regression test for ISSUE-NNN — {desc}"`
- Fails → fix test once. Still failing → delete test, defer.
- Taking >2 min exploration → skip and defer.

### 8f. Self-Regulation (STOP AND EVALUATE)

Every 5 fixes (or after any revert), compute the WTF-likelihood:

```
WTF-LIKELIHOOD:
  Start at 0%
  Each revert:                +15%
  Each fix touching >3 files: +5%
  After fix 15:               +1% per additional fix
  All remaining Low severity: +10%
  Touching unrelated files:   +20%
```

**If WTF > 20%:** STOP immediately. Show the user what you've done so far. Ask whether to continue.

**Hard cap: 50 fixes.** After 50 fixes, stop regardless of remaining issues.

---

## Phase 9: Final QA

After all fixes are applied:

1. Re-run QA on all affected pages
2. Compute final health score
3. **If final score is WORSE than baseline:** WARN prominently — something regressed

---

## Phase 10: Report

Write the report to `.qa-reports/qa-report-{domain}-{YYYY-MM-DD}.md`.

**Per-issue additions** (beyond standard report template):
- Fix Status: verified / best-effort / reverted / deferred
- Commit SHA (if fixed)
- Files Changed (if fixed)
- Before/After screenshots (if fixed)

**Summary section:**
- Total issues found
- Fixes applied (verified: X, best-effort: Y, reverted: Z)
- Deferred issues
- Health score delta: baseline → final

**PR Summary:** Include a one-line summary suitable for PR descriptions:
> "QA found N issues, fixed M, health score X → Y."

---

## Phase 11: TODOS.md Update

If the repo has a `TODOS.md`:

1. **New deferred bugs** → add as TODOs with severity, category, and repro steps
2. **Fixed bugs that were in TODOS.md** → annotate with "Fixed by /qa on {branch}, {date}"

---

## Important Rules

1. **Repro is everything.** Every issue needs at least one screenshot. No exceptions.
2. **Verify before documenting.** Retry the issue once to confirm it's reproducible, not a fluke.
3. **Never include credentials.** Write `[REDACTED]` for passwords in repro steps.
4. **Write incrementally.** Append each issue to the report as you find it. Don't batch.
5. **Check console after every interaction.** JS errors that don't surface visually are still bugs.
6. **Test like a user.** Use realistic data. Walk through complete workflows end-to-end.
7. **Depth over breadth.** 5-10 well-documented issues with evidence > 20 vague descriptions.
8. **Show screenshots to the user.** After every screenshot or annotated snapshot, use the Read tool on the output file so the user can see it inline.
9. **Never refuse to use the browser.** When the user requests browser-based testing, never suggest evals or unit tests as a substitute.
10. **Clean working tree required.** If dirty, offer commit/stash/abort before proceeding.
11. **One commit per fix.** Never bundle multiple fixes into one commit.
12. **Only modify tests when generating regression tests in Phase 8e.5.** Never modify CI configuration. Never modify existing tests — only create new test files.
13. **Revert on regression.** If a fix makes things worse, `git revert HEAD` immediately.
14. **Self-regulate.** Follow the WTF-likelihood heuristic. When in doubt, stop and ask.
