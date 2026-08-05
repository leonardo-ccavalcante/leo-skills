# GStack Skill Map — Long Reference

Read this file from `gstack-router/SKILL.md` only when the embedded MECE tree
isn't sufficient — typically when two leaves both seem to apply, or the user's
situation doesn't map cleanly to any leaf.

Each of the 32 skills below has:
- **What it does** — one paragraph focused on the *outcome*, not the trigger list.
- **Use when** — bullets that trigger the skill.
- **Don't use when** — the negative space; usually the most useful part.
- **Common next** — what typically follows.

---

## Planning & strategy (6)

### office-hours
**What it does.** YC-style product diagnostic for pre-code ideas. Asks six
forcing questions (demand reality, status quo, desperate specificity,
narrowest wedge, observation, future-fit) and produces a design doc, not code.
- **Use when.** No code exists yet; user is exploring whether to build at all.
- **Don't use when.** Code exists, or the user already knows what they're
  building and just wants a plan reviewed.
- **Common next.** `/plan-ceo-review` (then design/eng/devex), or `/autoplan`.

### plan-ceo-review
**What it does.** Founder-mode plan review — rethinks the problem, challenges
premises, expands scope when it creates a better product.
- **Use when.** A plan file exists; want to stress-test the *what* and *why*.
- **Don't use when.** No plan file; or the plan is already locked and you're
  reviewing execution (use `/plan-eng-review`).
- **Common next.** `/plan-eng-review`, `/plan-design-review`, `/plan-devex-review`.

### plan-eng-review
**What it does.** Eng-manager-mode plan review — locks the execution plan:
architecture, data flow, edge cases, test coverage, performance.
- **Use when.** Plan content is good; need to lock the *how*.
- **Don't use when.** Plan content isn't agreed yet (do `/plan-ceo-review` first).
- **Common next.** `/ship` (after building).

### plan-design-review
**What it does.** Designer's-eye plan review — rates each design dimension 0-10
and rewrites the plan to push toward 10.
- **Use when.** Plan has UI/UX components needing critique before build.
- **Don't use when.** Plan is backend-only; or you have implemented UI to
  audit (use `/design-review`).
- **Common next.** `/design-consultation` or `/design-shotgun`.

### plan-devex-review
**What it does.** DX plan review — explores developer personas, benchmarks
competitors, designs magical moments, traces friction.
- **Use when.** Plan is for a developer tool, SDK, API, or CLI.
- **Don't use when.** Product is end-user-facing without dev surface.
- **Common next.** `/ship`.

### autoplan
**What it does.** Sequential CEO → design → eng → DX pass with auto-decisions
using six principles. One command, fully reviewed plan out.
- **Use when.** Want speed; willing to accept auto-decisions on close calls.
- **Don't use when.** Plan touches a strategic bet — run the four reviews
  interactively.
- **Common next.** `/ship`.

---

## Design (4)

### design-consultation
**What it does.** Generates a complete design system (typography, color, layout,
spacing, motion) and writes `DESIGN.md`.
- **Use when.** Fresh project, no design language yet.
- **Don't use when.** A design system exists — use `/design-shotgun` for
  variants instead.
- **Common next.** `/design-shotgun` or `/design-html`.

### design-shotgun
**What it does.** Generates multiple AI mockup variants in parallel, opens a
comparison board, collects feedback, iterates.
- **Use when.** Design system exists; need visual options for a specific screen.
- **Don't use when.** No design system yet (`/design-consultation` first); or
  user wants to audit existing UI (`/design-review`).
- **Common next.** `/design-html`.

### design-html
**What it does.** Converts an approved mockup PNG (or plan description) into
production-quality self-contained HTML/CSS.
- **Use when.** A variant is approved and ready to implement.
- **Don't use when.** No approved mockup yet (`/design-shotgun` first).
- **Common next.** `/qa` (verify works in browser).

### design-review
**What it does.** Designer's-eye QA of *implemented* UI — finds visual slop,
inconsistency, spacing/hierarchy/contrast issues and fixes them in code.
- **Use when.** UI exists in the browser; want to audit and fix it.
- **Don't use when.** Reviewing a plan (use `/plan-design-review`); or no UI
  shipped yet.
- **Common next.** `/qa`, then `/ship`.

---

## Development & testing (6)

### review
**What it does.** Pre-landing diff review focused on structural issues tests
miss: SQL safety, LLM trust, race conditions, shell injection, scope drift.
Fix-first.
- **Use when.** Feature is built; before opening a PR.
- **Don't use when.** Behaviour bugs (use `/qa`); root-cause unclear (use
  `/investigate`).
- **Common next.** `/ship`.

### qa
**What it does.** Full test-fix-verify loop. Tests as a real user in a browser,
fixes bugs found with atomic commits, re-verifies, adds regression tests.
- **Use when.** Feature built on a branch; want it verified and bugs fixed.
- **Don't use when.** User wants a report only (use `/qa-only`); root cause
  unclear (use `/investigate`).
- **Common next.** `/review`, then `/ship`.

### qa-only
**What it does.** Same testing as `/qa`, but report-only — never modifies code.
- **Use when.** User wants a triage report, will decide what to fix.
- **Don't use when.** User wants bugs fixed in the same loop.
- **Common next.** `/investigate` (if bugs found), or `/ship`.

### investigate
**What it does.** Systematic debugging — investigate / analyse / hypothesise /
implement. Iron law: no fixes without root cause.
- **Use when.** Bug reported, root cause unclear; or "it was working yesterday".
- **Don't use when.** Cause is obvious — just fix it.
- **Common next.** `/qa` (verify the fix), then `/ship`.

### ship
**What it does.** Fully automated ship: merge base, run tests, audit coverage,
bump VERSION, write CHANGELOG, atomic commits, push, open PR.
- **Use when.** Branch is clean and verified; want a PR.
- **Don't use when.** Not yet verified (`/qa` first); PR exists (use
  `/land-and-deploy`).
- **Common next.** `/land-and-deploy`.

### land-and-deploy
**What it does.** Merge the PR, wait for CI/deploy, verify production via
canary; revert on failure.
- **Use when.** PR is green and you want it in prod.
- **Don't use when.** No PR exists (`/ship` first); deploy platform not yet
  configured (`/setup-deploy` first).
- **Common next.** `/canary`, then `/document-release`.

---

## Documentation & monitoring (5)

### document-release
**What it does.** Post-ship docs update. Reads docs, cross-references the diff,
builds Diataxis coverage map, updates README/ARCHITECTURE/CONTRIBUTING, detects
diagram drift, polishes CHANGELOG voice.
- **Use when.** Just shipped — sync docs to the diff.
- **Don't use when.** No diff to sync (use `/document-generate` for greenfield).
- **Common next.** `/retro` (weekly).

### document-generate
**What it does.** Generates missing docs from scratch using the Diataxis
framework (tutorial / how-to / reference / explanation).
- **Use when.** A feature or module has no docs at all.
- **Don't use when.** Docs exist and need updating (use `/document-release`).
- **Common next.** `/document-release` (on next ship).

### retro
**What it does.** Weekly engineering retro from git history + metrics, with
trend tracking and per-person breakdown.
- **Use when.** Weekly cadence; or after a notable incident or shipping cycle.
- **Don't use when.** Mid-feature; or no meaningful history yet.
- **Common next.** Next planning cycle (`/office-hours` or `/plan-ceo-review`).

### canary
**What it does.** Post-deploy live-app monitoring — periodic screenshots,
console errors, perf, comparison to pre-deploy baseline.
- **Use when.** Just deployed; want a sustained watch.
- **Don't use when.** Not deployed yet; or one-off perf check (use `/benchmark`).
- **Common next.** `/document-release`, then `/retro`.

### benchmark
**What it does.** Performance regression detection — baselines for page load,
Core Web Vitals, resource sizes; before/after diff on every PR.
- **Use when.** Frontend or build-config change; want a perf gate.
- **Don't use when.** Not a performance concern (skip); or want a sustained
  watch (use `/canary`).
- **Common next.** `/ship` (if perf gate passes).

---

## Security & advanced (3)

### cso
**What it does.** Chief Security Officer mode — secrets archaeology, dependency
supply chain, CI/CD security, LLM/AI security, skill supply chain, OWASP Top 10,
STRIDE. Two modes: daily (8/10 confidence gate) and comprehensive (2/10 bar).
- **Use when.** Pre-deploy of public-facing code; new deps; auth changes; LLM
  feature added; quarterly review.
- **Don't use when.** Specific narrow check (write a targeted query); the
  finding's at the diff level (use `/review` or `/codex`).
- **Common next.** `/codex` (for adversarial second-opinion on a fix), then
  `/ship`.

### codex
**What it does.** OpenAI Codex CLI wrapper — three modes: code review (diff
review with pass/fail gate), challenge (adversarial), consult (Q&A with
session continuity).
- **Use when.** Want a second-opinion from a different AI before merging; or
  on a stubborn bug.
- **Don't use when.** Just need a Claude-internal review (use `/review`).
- **Common next.** `/ship` (after passing).

### pair-agent
**What it does.** Pair a remote AI agent with your browser via a short-lived
setup key + optional ngrok tunnel. Scoped tabs, read+write default, admin
on request.
- **Use when.** Want a second AI to see/drive your browser session
  (Codex/Cursor/another Claude).
- **Don't use when.** Solo browser work — just use the local browser.
- **Common next.** Continue work; revoke the pairing when done.

---

## Power tools (8)

### careful
**What it does.** Warns before destructive commands (rm -rf, DROP TABLE,
force-push, git reset --hard, kubectl delete, etc.). User can override each
warning.
- **Use when.** Touching prod, debugging live, shared environment.
- **Don't use when.** Pure dev work in isolation.
- **Common next.** End session, or `/unfreeze` if also frozen.

### freeze
**What it does.** Restricts Edit/Write to a chosen directory for the session.
- **Use when.** Want to be sure unrelated code isn't touched.
- **Don't use when.** Refactor genuinely spans modules.
- **Common next.** `/unfreeze` when widening scope.

### guard
**What it does.** `/careful` + `/freeze` together.
- **Use when.** Maximum-blast-radius work (prod hotfix, infra change).
- **Don't use when.** Either protection alone is sufficient.
- **Common next.** `/unfreeze` (releases freeze; careful auto-clears at
  session end).

### unfreeze
**What it does.** Clears the freeze boundary without ending the session.
- **Use when.** Mid-session decision to widen edit scope.
- **Don't use when.** Done for the day — just end session.
- **Common next.** Continue work, or re-`/freeze` with a wider directory.

### open-gstack-browser
**What it does.** Launches a visible AI-controlled Chromium window with the
gstack sidebar; anti-bot stealth patched in.
- **Use when.** Want to watch the agent work in real time; demo; or sites
  block headless.
- **Don't use when.** Headless is fine and faster.
- **Common next.** `/qa` or `/canary`.

### setup-deploy
**What it does.** Detects deploy platform (Fly/Render/Vercel/Netlify/Heroku/
GitHub Actions/custom), records URL + health-check endpoint to `.deploy-config.json`.
- **Use when.** First-time deploy setup; or platform changed.
- **Don't use when.** Already configured — `.deploy-config.json` exists.
- **Common next.** `/land-and-deploy`.

### setup-gbrain
**What it does.** Installs and configures gstack's gbrain knowledge base
(local PGLite or Supabase), registers as MCP. gstack-specific.
- **Use when.** First-time gstack user wants persistent knowledge.
- **Don't use when.** Not using gstack proper.
- **Common next.** Continue work; gbrain auto-captures learnings.

### gstack-upgrade
**What it does.** Upgrades gstack itself to the latest version. gstack-specific.
- **Use when.** A skill preamble flagged `UPGRADE_AVAILABLE`; or user asks.
- **Don't use when.** Not using gstack proper.
- **Common next.** Whatever the user came to do.

---

## Disambiguation quick reference

| Pair | Choose A when… | Choose B when… |
|---|---|---|
| `/qa` vs `/qa-only` | Fix bugs in the same loop | Report-only triage |
| `/design-consultation` vs `/design-shotgun` | No design system yet | System exists, screen needs options |
| `/ship` vs `/land-and-deploy` | Local branch, no PR | PR exists, ready to merge |
| `/document-release` vs `/document-generate` | Sync to a diff | Greenfield docs |
| `/review` vs `/codex` | Internal Claude review | Need a different-AI second opinion |
| 4 plan reviews vs `/autoplan` | Control each pass | Speed + auto-decisions |
| `/design-review` vs `/plan-design-review` | UI is implemented | Plan is in writing |
| `/investigate` vs `/qa` | Root cause unclear | Behaviour symptom in browser |
| `/canary` vs `/benchmark` | Sustained watch post-deploy | One-off perf gate pre-merge |
| `/careful` vs `/freeze` | Bash blast radius | File-edit blast radius |
