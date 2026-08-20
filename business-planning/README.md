# business-planning

A Claude Code skill that takes a business idea, model, or existing plan and
produces evidence-disciplined planning artifacts: full plans, single modules
(canvases, pricing, ICP, market sizing, GTM, pitch outlines, 90-day roadmaps),
and audits with a deterministic readiness verdict. Deterministic pieces run
through `scripts/bp.sh`; all financial math (LTV, CAC, P&L, runway, scenario
outcomes) is delegated to the financial-analysis skill's `fa.sh`.

## Routes

- **FULL-PLAN**: a complete 13-part business plan from an idea, with stage
  detection and a pre-revenue mode.
- **MODULE**: one artifact: canvas, revenue streams, pricing, ICP and anti-ICP,
  bottom-up TAM/SAM/SOM, GTM, scenarios, pitch outline, or 90-day roadmap.
- **EVALUATE**: audit of an existing model, plan, or org structure, ending in a
  HEALTHY / FRAGILE / UNSUSTAINABLE / INSUFFICIENT_DATA verdict from
  `bp.sh readiness`.

## The no-fabrication rule

Every number carries a tag: `user`, `public` (with source URL and access date),
`assumption` (with a stated basis), or `unknown`. The tooling enforces it: an
uncited public claim is downgraded to assumption at runtime and fails strict
validation; unknowns render as "Unknown", never as a plugged average; and
`INSUFFICIENT_DATA` is a legitimate verdict, not a failure to be papered over.

## Hooks (opt-in, never auto-installed)

`hooks/` contains two optional hardening hooks: `validate_hook.sh` validates
`.bp.json` state files and lints `bp_<slug>/` Markdown on every Write/Edit, and
`retro_hook.sh` blocks a session from ending once while a `.bp-session` marker
exists, pointing at the retrospective. Nothing installs them for you.

- Install: merge the `hooks` object from `hooks/settings-snippet.json` into
  `~/.claude/settings.json` (create the file if absent, or extend your existing
  PostToolUse/Stop arrays; the /update-config skill can do the merge).
- Uninstall: remove those two entries from `~/.claude/settings.json` again.

The skill's workflow runs validation, lint, and the retrospective as ordinary
steps whether or not the hooks are installed.

## Privacy

Two places accumulate real business context. `MEMORY.md` (in this folder)
stores calibration lessons and preferences across sessions; consider
`git update-index --skip-worktree MEMORY.md` before real use. Each engagement
writes a `bp_<slug>/` workspace into your working directory (state file,
sources, script outputs, decisions); treat those directories as confidential
project data and keep them out of public repositories.

## Attribution

Adapted concepts and structures, with license texts and details in
`references/third-party-licenses/`:

- [founder-os](https://github.com/vinicius91carvalho/founder-os) (MIT):
  founder-framework curation behind the market and GTM references.
- [codex-startup-business-planner](https://github.com/Kappaemme-git/codex-startup-business-planner)
  (MIT): readiness dimensions and weights; evidence-backed plan, pricing, and
  90-day roadmap shape.
- [pm-skills](https://github.com/phuryn/pm-skills) (MIT): discovery-to-strategy
  structures and the one-artifact-per-module route design.
- [ai-business-planner](https://github.com/shinpr/ai-business-planner) (MIT):
  guided multi-artifact workflow and the cross-project memory concept.
- [FISY](https://fisy.fr) (no published license, concepts only): the depth
  ladder (starter / essential / innovation) and the financial-plan line
  checklist concept. No FISY files, formulas, or sheet layouts are reproduced.
