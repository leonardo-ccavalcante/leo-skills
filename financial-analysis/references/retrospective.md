# Retrospective — the reinforcement loop

Run this after the report is delivered, or when the user signals the session is
done. Its purpose is compounding: each session should leave the skill measurably
better calibrated than it found it. Skipping it throws away the session's learning.

Keep it proportional: a quick sanity-check session gets a 2-minute retro; a full
viability study gets the complete protocol.

## 1. SAT audit (structured challenge)

If the `/sat` skill is available, invoke it in **solo mode** against the delivered
analysis, requesting three techniques:

- **Key Assumptions Check** — list the tagged assumptions that drove the verdict.
  Was any of them effectively treated as fact in the narrative? Would the verdict
  survive each assumption being wrong?
- **Devil's Advocacy** — the best countercase to the recommendation, argued
  seriously, from the same script outputs.
- **Premortem** — it is six months later and the analysis proved wrong. What is the
  most likely reason?

**Fallback (no /sat available)** — answer those three questions directly, in
writing, before moving on. The discipline is the checklist, not the skill.

## 2. Problem-solving audit (structure check)

If the `/problem-solving` skill is available, invoke it to review:

- Was the problem framed as the decision actually faced (not the analysis that was
  easiest to run)?
- Was the issue breakdown MECE — or did two "issues" overlap while a third driver
  went unexamined?
- Was the report Pyramid-Principle-clean — governing thought first, support after?

**Fallback** — check those three directly.

## 3. Self-audit rubric (deterministic)

Answer each with evidence from this session, not vibes:

**Accuracy**
- Did every number in the final report trace to script JSON output? (Scan the
  report for figures; each must exist in a script run.)
- Were any guard reasons or invariant warnings ignored or papered over?
- Were benchmarks cited with their date and segment?

**Reliability**
- Was `INSUFFICIENT_DATA` ever routed around instead of relayed?
- Did any `assumption` get upgraded to fact in the narrative?
- Were tags preserved end-to-end (input table → report table)?

**Efficiency**
- Were scripts rerun redundantly with identical inputs?
- Was any question asked whose answer could not have changed the verdict?
- Was a reference file read that the domain didn't need?

## 4. Write lessons to MEMORY.md

Append to the matching section of `MEMORY.md` (skill root), format:

```markdown
- [YYYY-MM-DD · <domain>] <one-line lesson>. Apply: <one-line how>.
```

Write only lessons that change future behavior — a session with nothing worth
recording is a legitimate outcome; don't pad. Candidates:

- **Calibration lessons** — an assumption the user corrected (e.g., their market's
  churn runs higher than the benchmark anchor used).
- **Preferences** — currency, language, depth, report format choices the user
  expressed.
- **Recurring analyses** — an analysis likely to repeat (monthly cost-per-ticket),
  with its input file shapes and this period's baseline numbers.
- **Process fixes** — a workflow stumble and its fix (e.g., "ask for employer
  burden before projecting payroll").

Consolidation rule: when MEMORY.md exceeds ~150 lines, merge duplicates and prune
superseded entries — oldest first, calibration lessons last (they age best).

If a lesson implies changing SKILL.md, a reference, or a script: **propose the edit
to the user explicitly and wait for agreement. Never silently self-modify the
skill.** Note the proposal in MEMORY.md either way.

## 5. Close out

Delete the `.fa-session` marker from the working directory. If a `<name>.fa.json`
state file was built, confirm it's saved and mention it to the user as the resume
point for a future session.
