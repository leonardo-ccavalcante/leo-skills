---
name: review
description: |
  Pre-landing PR review focused on structural issues that tests don't catch — scope
  drift, plan completion, SQL/data safety, race conditions, LLM trust boundaries,
  shell injection, enum completeness. Fix-first, not read-only: auto-fixes safe
  issues, asks before applying risky ones. Use this skill whenever the user says
  "review this", "review my PR", "check my diff", "review the branch", "what's
  wrong with this code", "code review", or wants a pre-merge sanity check. Also
  triggers on /review. Proactively invoke when the user finishes a feature and
  before they run /ship. Never commits or pushes — that's /ship's job.
---

# Pre-Landing PR Review

You are running the `/review` workflow. Analyze the current branch's diff against the base branch for structural issues that tests don't catch.

---

## Step 0: Detect platform and base branch

Detect the git hosting platform:

```bash
git remote get-url origin 2>/dev/null
```

- "github.com" → GitHub (`gh` CLI)
- "gitlab" → GitLab (`glab` CLI)
- Otherwise check `gh auth status` / `glab auth status`, fall back to git-native

Determine the base branch:

**GitHub:** `gh pr view --json baseRefName -q .baseRefName`, fall back to `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
**GitLab:** `glab mr view -F json` → `target_branch`, fall back to `glab repo view -F json` → `default_branch`
**Git-native fallback:** `git symbolic-ref refs/remotes/origin/HEAD | sed 's|refs/remotes/origin/||'`, then `main`, then `master`.

Print the detected base branch. Substitute it everywhere subsequent steps say "the base branch" or `<base>`.

---

## Step 1: Check branch

1. Run `git branch --show-current` to get the current branch.
2. If on the base branch, output: **"Nothing to review — you're on the base branch or have no changes against it."** and stop.
3. Run `git fetch origin <base> --quiet && git diff origin/<base> --stat`. If no diff, output the same message and stop.

---

## Step 1.5: Scope Drift Detection

Before reviewing code quality, check: **did they build what was requested — nothing more, nothing less?**

1. Read `TODOS.md` (if it exists). Read PR description (`gh pr view --json body --jq .body 2>/dev/null || true`). Read commit messages (`git log origin/<base>..HEAD --oneline`). **If no PR exists:** rely on commit messages and TODOS.md.
2. Identify the **stated intent** — what was this branch supposed to accomplish?
3. Run `git diff origin/<base>...HEAD --stat` and compare the files changed against the stated intent.

4. Evaluate with skepticism:

   **SCOPE CREEP detection:**
   - Files changed that are unrelated to the stated intent
   - New features or refactors not mentioned in the plan
   - "While I was in there..." changes that expand blast radius

   **MISSING REQUIREMENTS detection:**
   - Requirements from TODOS.md/PR description not addressed in the diff
   - Test coverage gaps for stated requirements
   - Partial implementations (started but not finished)

5. Output (before the main review begins):
   ```
   Scope Check: [CLEAN / DRIFT DETECTED / REQUIREMENTS MISSING]
   Intent: <1-line summary of what was requested>
   Delivered: <1-line summary of what the diff actually does>
   [If drift: list each out-of-scope change]
   [If missing: list each unaddressed requirement]
   ```

6. This is **INFORMATIONAL** — does not block the review. Proceed to the next step.

---

### Plan File Discovery

If the conversation has an active plan file path, use it directly.

Otherwise search by content:

```bash
BRANCH=$(git branch --show-current 2>/dev/null | tr '/' '-')
for PLAN_DIR in ".plans" "$HOME/.claude/plans" "$HOME/.codex/plans"; do
  [ -d "$PLAN_DIR" ] || continue
  PLAN=$(ls -t "$PLAN_DIR"/*.md 2>/dev/null | xargs grep -l "$BRANCH" 2>/dev/null | head -1)
  [ -n "$PLAN" ] && break
done
[ -n "$PLAN" ] && echo "PLAN_FILE: $PLAN" || echo "NO_PLAN_FILE"
```

Validate: if found via content search, read the first 20 lines to confirm it relates to the current branch.

### Actionable Item Extraction

Read the plan file. Extract every actionable item:

- **Checkbox items:** `- [ ] ...` or `- [x] ...`
- **Numbered steps:** "1. Create ...", "2. Add ..."
- **Imperative statements:** "Add X to Y", "Create a Z service"
- **File-level specifications:** "New file: path/to/file.ts"
- **Test requirements:** "Test that X", "Add test for Y"
- **Data model changes:** "Add column X to table Y"

**Ignore:** Context/Background sections, Questions/TBD/TODO-to-decide, Review report sections, explicit "Future:" / "Out of scope:" items, decision records.

**Cap at 50 items.** For each item, note its text and category: CODE | TEST | MIGRATION | CONFIG | DOCS.

### Verification Mode

Classify how each item can be verified:

- **DIFF-VERIFIABLE** — A code change in this repo would show in `git diff`. Cross-reference against diff.
- **CROSS-REPO** — Item names a file in a sibling repo. Try `[ -f <path> ]` on reachable sibling roots. File exists → DONE. Missing → NOT DONE. Path unreachable → UNVERIFIABLE.
- **EXTERNAL-STATE** — Names state in an external system (Cloudflare DNS, OAuth allowlists, etc.). Always UNVERIFIABLE; cite what the user must check.
- **CONTENT-SHAPE** — File-must-follow-convention. If in another repo, scan for a project-detected validator (`validate-*`, `lint-wiki`, `check-docs`) before falling back to UNVERIFIABLE.

**Path concreteness rule.** If a plan item names a concrete filesystem path, classify DONE or NOT DONE based on `[ -f <path> ]`. UNVERIFIABLE is only valid for genuinely abstract paths or unreachable sibling roots.

**Honesty rule.** Do NOT classify an item as DONE just because related code shipped. Code that *handles* a deliverable is not the deliverable. When in doubt, prefer UNVERIFIABLE.

### Cross-Reference Against Diff

Run `git diff origin/<base>...HEAD` and `git log origin/<base>..HEAD --oneline`.

For each plan item, classify:

- **DONE** — Clear evidence the item shipped. Cite the file(s) or verified path.
- **PARTIAL** — Some work toward this item exists but is incomplete.
- **NOT DONE** — Verification ran and produced negative evidence.
- **CHANGED** — Implemented differently than planned but the goal is achieved. Note the difference.
- **UNVERIFIABLE** — Diff and sibling-repo checks can't prove or disprove. Cite the manual verification the user must perform.

**Be conservative with DONE.** **Be generous with CHANGED.** **Be honest with UNVERIFIABLE.**

### Output Format

```
PLAN COMPLETION AUDIT
═══════════════════════════════
Plan: {plan file path}

## Implementation Items
  [DONE]         Create UserService — src/services/user_service.rb (+142 lines)
  [PARTIAL]      Add validation — model validates but missing controller checks
  [NOT DONE]     Add caching layer — no cache-related changes in diff
  [CHANGED]      "Redis queue" → implemented with Sidekiq instead

## Test Items
  [DONE]         Unit tests for UserService — test/services/user_service_test.rb

## Migration Items
  [DONE]         Create users table — db/migrate/20240315_create_users.rb

## Cross-Repo / External Items
  [DONE]         sibling-repo has /docs/dashboard.md — verified at ~/Development/sibling-repo/docs/dashboard.md
  [UNVERIFIABLE] Cloudflare DNS-only on api.example.com — external system, manual check required

─────────────────────────────────
COMPLETION: 5/9 DONE, 1 PARTIAL, 1 NOT DONE, 1 CHANGED, 2 UNVERIFIABLE
─────────────────────────────────
```

### Fallback Intent Sources (when no plan file found)

1. **Commit messages:** Actionable verbs ("add", "implement", "fix", "create"). Skip noise: "WIP", "tmp", "squash", "merge", "chore", "typo", "fixup".
2. **TODOS.md** — items related to this branch or recent dates.
3. **PR description** — intent context.

### Investigation Depth

For each PARTIAL or NOT DONE item, determine the likely reason:
- **Scope cut** — evidence of intentional removal
- **Context exhaustion** — work started but stopped mid-way
- **Misunderstood requirement** — built something that doesn't match the plan
- **Blocked by dependency**
- **Genuinely forgotten** — no evidence of any attempt

Output:
```
DISCREPANCY: {PARTIAL|NOT_DONE} | {plan item} | {what was actually delivered}
INVESTIGATION: {likely reason with evidence from git log / code}
IMPACT: {HIGH|MEDIUM|LOW} — {what breaks if this stays undelivered}
```

**HIGH-impact discrepancies** trigger a stop-and-ask:
- A) Stop and implement missing items
- B) Ship anyway + create P1 TODOs
- C) Intentionally dropped

---

## Step 2: Read the checklist

Read your project's review checklist (often `CHECKLIST.md`, `docs/review-checklist.md`, or similar). If no checklist exists, use the CRITICAL categories listed in Step 4 below.

---

## Step 2.5: Check for automated review comments

If a code review bot (Greptile, CodeRabbit, etc.) is configured and a PR exists, fetch its comments. Classify each as VALID & ACTIONABLE, VALID BUT ALREADY FIXED, FALSE POSITIVE, or SUPPRESSED. You will reply to them in Step 5.

If no PR exists or no bot is configured, skip silently.

---

## Step 3: Get the diff

Fetch the latest base branch to avoid false positives from stale local state:

```bash
git fetch origin <base> --quiet
git diff origin/<base>
```

This includes both committed and uncommitted changes.

---

## Step 4: Critical pass (core review)

Apply the CRITICAL categories against the diff:

- **SQL & Data Safety** — string interpolation in queries, missing parameterization, unsafe transactions
- **Race Conditions & Concurrency** — shared state without locks, time-of-check/time-of-use, missing transactions
- **LLM Output Trust Boundary** — raw LLM output written to DB/eval/exec/auth decisions without validation
- **Shell Injection** — user input in `exec`, `system`, `Open3`, backticks, `subprocess.run(shell=True)`
- **Enum & Value Completeness** — new enum value added; are all switch/case sites and DB constraints updated?

Also apply INFORMATIONAL categories: Async/Sync Mixing, Column/Field Name Safety, LLM Prompt Issues, Type Coercion, View/Frontend, Time Window Safety, Completeness Gaps, Distribution & CI/CD.

**Enum & Value Completeness requires reading code OUTSIDE the diff.** When the diff introduces a new enum value, Grep to find all sibling-value references, then Read those files to check if the new value is handled.

**Search-before-recommending:** When recommending a fix pattern, verify it's current best practice for the framework version in use. Check if a built-in solution exists in newer versions. Verify API signatures against current docs.

---

## Confidence Calibration

Every finding MUST include a confidence score (1-10):

| Score | Meaning | Display rule |
|-------|---------|-------------|
| 9-10 | Verified by reading specific code. Concrete bug or exploit demonstrated. | Show normally |
| 7-8 | High confidence pattern match. Very likely correct. | Show normally |
| 5-6 | Moderate. Could be a false positive. | Show with caveat "Medium confidence, verify" |
| 3-4 | Low confidence. Pattern is suspicious but may be fine. | Suppress from main report. Appendix only. |
| 1-2 | Speculation. | Only report if severity would be P0. |

**Finding format:**

`[SEVERITY] (confidence: N/10) file:line — description`

Examples:
`[P1] (confidence: 9/10) app/models/user.rb:42 — SQL injection via string interpolation in where clause`
`[P2] (confidence: 5/10) app/controllers/api/v1/users_controller.rb:18 — Possible N+1 query, verify with production logs`

---

## Step 4.5: Specialist Dispatch (optional)

For larger diffs (>50 lines), consider dispatching specialist reviewers in parallel via independent subagent calls. Each subagent has fresh context — no prior review bias. Suggested specialists:

- **Testing** — coverage gaps, missing edge cases, brittle tests
- **Maintainability** — naming, complexity, dead code
- **Security** — auth, authz, input validation (dispatch if diff touches auth or backend >100 lines)
- **Performance** — N+1, unbounded loops, missing indexes
- **Data Migration** — backwards compatibility, downtime, data loss risk
- **API Contract** — breaking changes, versioning, deprecation
- **Design** — visual polish, accessibility, responsive behavior

**Each specialist prompt template:**

"You are a specialist code reviewer. Run `git diff origin/<base>` to get the full diff. Apply the {domain} checklist. For each finding, output a JSON object on its own line:

```json
{"severity":"CRITICAL|INFORMATIONAL","confidence":N,"path":"file","line":N,"category":"category","summary":"description","fix":"recommended fix","specialist":"name"}
```

If no findings: output `NO FINDINGS` and nothing else. Do not output anything else — no preamble, no summary, no commentary."

**Merge findings:** Compute fingerprints (`path:line:category`), deduplicate, boost confidence by +1 for findings caught by multiple specialists.

**Confidence gates:**
- 7+: show normally
- 5-6: show with caveat
- 3-4: appendix only
- 1-2: suppress

**PR Quality Score:** `max(0, 10 - (critical_count * 2 + informational_count * 0.5))`

---

## Step 5: Fix-First Review

**Every finding gets action — not just critical ones.**

### Step 5a: Classify each finding

For each finding, classify as AUTO-FIX (mechanical, safe) or ASK (user judgment required). Critical findings lean toward ASK; informational findings lean toward AUTO-FIX.

### Step 5b: Auto-fix all AUTO-FIX items

Apply each fix directly. Output one line per fix: `[AUTO-FIXED] [file:line] Problem → what you did`

### Step 5c: Batch-ask about ASK items

If there are ASK items remaining, present them in ONE batched question:

```
I auto-fixed 5 issues. 2 need your input:

1. [CRITICAL] app/models/post.rb:42 — Race condition in status transition
   Fix: Add `WHERE status = 'draft'` to the UPDATE
   → A) Fix  B) Skip

2. [INFORMATIONAL] app/services/generator.rb:88 — LLM output not type-checked before DB write
   Fix: Add JSON schema validation
   → A) Fix  B) Skip

RECOMMENDATION: Fix both — #1 is a real race condition, #2 prevents silent data corruption.
```

### Step 5d: Apply user-approved fixes

Apply fixes for items where the user chose "Fix." Output what was fixed.

### Verification of claims

Before producing the final review output:
- If you claim "this pattern is safe" → cite the specific line proving safety
- If you claim "this is handled elsewhere" → read and cite the handling code
- If you claim "tests cover this" → name the test file and method
- Never say "likely handled" or "probably tested" — verify or flag as unknown

**Rationalization prevention:** "This looks fine" is not a finding. Either cite evidence it IS fine, or flag it as unverified.

### Reply to review-bot comments

After your own findings, reply to any external review-bot comments classified in Step 2.5:

1. **VALID & ACTIONABLE** — already in your findings (Fix-First flow). If user chose Fix, reply with inline diff + explanation.
2. **FALSE POSITIVE** — ask the user: A) Reply to bot explaining why it's incorrect, B) Fix it anyway (low-effort), C) Ignore. If A, post a reply with evidence.
3. **VALID BUT ALREADY FIXED** — reply with what was done and the fixing commit SHA.
4. **SUPPRESSED** — skip silently.

---

## Step 5.5: TODOS cross-reference

Read `TODOS.md` (if it exists). Cross-reference the PR against open TODOs:

- **Does this PR close any open TODOs?** Note them: "This PR addresses TODO: <title>"
- **Does this PR create work that should become a TODO?** Flag it as informational.
- **Are there related TODOs that provide context for this review?** Reference them.

---

## Step 5.6: Documentation staleness check

For each `.md` file in the repo root (README.md, ARCHITECTURE.md, CONTRIBUTING.md, CLAUDE.md, etc.):

1. Check if code changes in the diff affect features/components/workflows described in that doc file.
2. If the doc file was NOT updated but the code it describes WAS changed, flag it as INFORMATIONAL:
   "Documentation may be stale: [file] describes [feature] but code changed in this branch."

Informational only — never critical.

---

## Step 5.7: Adversarial review (always-on)

Every diff gets adversarial review. LOC is not a proxy for risk — a 5-line auth change can be critical.

Dispatch an adversarial subagent with fresh context — no checklist bias.

Subagent prompt:
"Read the diff for this branch with `git diff origin/<base>`. Think like an attacker and a chaos engineer. Your job is to find ways this code will fail in production. Look for: edge cases, race conditions, security holes, resource leaks, failure modes, silent data corruption, logic errors that produce wrong results silently, error handling that swallows failures, and trust boundary violations. Be adversarial. Be thorough. No compliments — just the problems. For each finding, classify as FIXABLE (you know how to fix it) or INVESTIGATE (needs human judgment). End your output with ONE line: `Recommendation: <action> because <one-line reason naming the most exploitable finding>`."

Present findings under an `ADVERSARIAL REVIEW:` header. FIXABLE findings flow into the Fix-First pipeline. INVESTIGATE findings are informational.

For diffs over 200 lines, also run a structured cross-model review if a second LLM is available. Check for `[P1]` markers — found means GATE: FAIL; not found means GATE: PASS. On FAIL, ask:
```
Cross-model review found N critical issues.
A) Investigate and fix now (recommended)
B) Continue — review will still complete
```

---

## Output Format

```
Pre-Landing Review: N issues (X critical, Y informational)

[For each finding]
[SEVERITY] (confidence: N/10) path:line — summary
  Fix: recommended fix
  [Action: AUTO-FIXED | FIXED | SKIPPED]

PR Quality Score: X/10
```

---

## Important Rules

- **Read the FULL diff before commenting.** Do not flag issues already addressed in the diff.
- **Fix-first, not read-only.** AUTO-FIX items are applied directly. ASK items are only applied after user approval. Never commit, push, or create PRs — that's /ship's job.
- **Be terse.** One line problem, one line fix. No preamble.
- **Only flag real problems.** Skip anything that's fine.
- **Verify every claim.** Cite file:line evidence.
