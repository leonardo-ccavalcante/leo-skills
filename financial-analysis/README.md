# financial-analysis

A Claude Code skill for interactive financial analysis with one governing rule:
**Python does all calculations; reasoning, research, and interpretation happen in
conversation.** The model never states a number it didn't read from script output.

Built from patterns in: OpenBusiness (evidence labels), codex-startup-business-planner
(tagged inputs, driver-only scenarios), alirezarezvani/claude-skills CFO suite
(`_missing` accumulator, benchmark bands), pm-skills (framework self-critique),
Fisy (accrual + cash two-track model), Foresight runway tool (trailing-average burn).

## Domains

1. **Business viability** — unit economics, multi-year P&L + cash projection,
   break-even, runway, scenarios (`references/viability.md`)
2. **Company analysis** — statement ratios, DuPont, trend analysis
   (`references/company-analysis.md`)
3. **SaaS metrics** — ARR bridge, churn, NRR/GRR, cohorts, Rule of 40, benchmarks
   by segment/stage (`references/saas-metrics.md`)
4. **Operational finance** — cost per ticket/project, cost-to-serve, capacity and
   headcount sizing, initiative ROI, budget variance
   (`references/operational-finance.md`)

## Quick start

```bash
FA=~/.claude/skills/financial-analysis/scripts/fa.sh
$FA doctor      # environment check (pandas/openpyxl only needed for file inputs)
$FA selftest    # golden-number tests for every formula module
$FA unit-economics --inputs '{"arpa": 99, "gross_margin_pct": 0.8, "monthly_churn_rate": 0.04}' --json
```

In Claude Code, just describe the analysis ("is this idea viable?", "what's our
cost per ticket?") — the skill triggers on the request.

## Key conventions

- **Tagged inputs**: every number is `user` / `public` (with URL) / `assumption`
  (with basis) / `unknown` (null). Computed values are `calculation`.
- **State files**: multi-input analyses persist as `<name>.fa.json` in your working
  directory — resumable and validatable (`fa.sh validate <file>`).
- **Exit codes**: 0 OK/PARTIAL · 2 INSUFFICIENT_DATA · 3 validation failure · 1 bug.
- **MEMORY.md**: the skill's own memory — calibration lessons, preferences,
  recurring analyses. Written by the end-of-session retrospective
  (`references/retrospective.md`).

## Optional hooks (hardening)

Two Claude Code hooks ship in `hooks/` — **not installed by default**:

- `validate_hook.sh` (PostToolUse on Write|Edit): auto-validates any `*.fa.json`
  file Claude writes; violations are fed back to Claude immediately.
- `retro_hook.sh` (Stop): if an analysis session is open (`.fa-session` marker)
  and the retrospective hasn't run, blocks the stop once with instructions.

To install: merge `hooks/settings-snippet.json` into `~/.claude/settings.json`
(back it up first), or ask Claude to do it via the `/update-config` skill. Both
behaviors also run as ordinary workflow steps without the hooks.

## Dependencies

None for conversation-input analyses (pure stdlib). CSV/Excel inputs need
`pip install pandas openpyxl`.

## Privacy note (if you version this skill publicly)

`MEMORY.md` is designed to accumulate real calibration baselines from your
analyses (actual costs, churn, headcount numbers). Version only the generic
seed: after the initial commit run
`git update-index --skip-worktree financial-analysis/MEMORY.md` in your skills
repo (a plain .gitignore does not cover already-tracked files), and keep
`*.fa.json` / `.fa-session` ignored — analysis state files contain real inputs.
