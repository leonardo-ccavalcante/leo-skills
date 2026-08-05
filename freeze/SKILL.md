---
name: freeze
description: |
  Restrict file edits to a single directory for the rest of the session. Blocks Edit and
  Write outside the allowed path so the agent cannot "helpfully" fix unrelated code
  while focused on a specific module. Use this skill whenever the user says "freeze",
  "freeze edits", "lock edits to this folder", "only edit X", "restrict edits", "scope
  edits", "lock down edits", or is debugging in one corner of a repo and wants to be
  sure nothing else gets touched. Also triggers on /freeze.
---

# Freeze — Restrict Edits to One Directory

Lock file edits to a specific directory. Any Edit or Write targeting a file outside
the allowed path will be **refused** for the rest of the session (until `/unfreeze`).

## Setup

1. Ask the user which directory to restrict edits to. Use `AskUserQuestion` with a
   text input (no preset options) — they type a path. Phrase the question as:

   > "Which directory should I restrict edits to? Files outside this path will be
   > blocked from editing for the rest of the session."

2. Resolve the path to an absolute path and normalize the trailing slash:

   ```bash
   FREEZE_DIR=$(cd "<user-input>" 2>/dev/null && pwd)
   FREEZE_DIR="${FREEZE_DIR%/}/"
   ```

3. Persist it to `.freeze-dir` in the current working directory (or `~/.cache/freeze`
   if you want it user-scoped). State the boundary back to the user so they can
   confirm:

   > "Edits restricted to `<path>/`. Any Edit or Write outside this directory will be
   > refused. Run `/freeze` again to change the boundary or `/unfreeze` to remove it."

## How to behave under this skill

Before every Edit/Write tool call, compare the target `file_path` against
`$FREEZE_DIR`:

- If `file_path` starts with `$FREEZE_DIR`, the edit is allowed.
- Otherwise, refuse the edit and explain which boundary blocked it. Suggest either:
  - Widening the boundary (`/freeze` with a parent directory)
  - Removing the boundary (`/unfreeze`)
  - Or leaving the change unmade because it's out of scope.

The trailing slash matters — `/src/` should not match `/src-old/`. Always keep it.

## Why this exists

When you're deep in a bug fix, it's easy to drift: you see a typo in an adjacent
file, you "improve" something on the way past, and suddenly the diff covers three
modules instead of one. A scoped diff is faster to review, easier to revert, and
less likely to introduce regressions in code you weren't focused on. Freeze makes
the scope explicit.

## Notes

- Freeze applies only to Edit and Write. Read, Glob, Grep, and Bash are unaffected.
- Bash commands like `sed -i` can still modify files outside the boundary — this
  is a guardrail against accidental edits, not a security boundary. If you catch
  yourself reaching for `sed -i` to bypass freeze, that's a signal to lift the
  freeze deliberately rather than work around it.
- The boundary persists per-session. Starting a new conversation clears it.

## See also

- `/unfreeze` — clear the boundary
- `/guard` — combine freeze with destructive-command guardrails
