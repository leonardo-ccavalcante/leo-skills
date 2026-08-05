---
name: guard
description: |
  Maximum safety mode — combines destructive-command warnings (/careful) with
  directory-scoped edit restrictions (/freeze) in a single skill. The agent will pause
  before destructive bash commands AND refuse Edit/Write outside a chosen directory.
  Use this skill whenever the user says "guard mode", "lock it down", "full safety",
  "maximum safety", "production mode", or is about to touch a live system and wants
  every available guardrail engaged. Also triggers on /guard.
---

# Guard Mode — Full Safety

Combines two protections in one skill:

1. **Destructive command warnings** — see `/careful` for the full pattern list
   (rm -rf, DROP TABLE, force-push, git reset --hard, kubectl delete, etc.).
2. **Edit boundary** — see `/freeze`. The user picks a directory; Edit/Write outside
   it is refused for the rest of the session.

## Setup

Ask the user which directory to restrict edits to. Use `AskUserQuestion` with a
text input (no preset options). Phrase it as:

> "Guard mode: which directory should edits be restricted to? Destructive command
> warnings are always on; files outside the chosen path will be blocked from editing."

Then resolve the path to an absolute path with a trailing slash and persist it
(see `/freeze` for details). Tell the user both protections are active:

> **Guard mode active.** Two protections are now running:
> 1. **Destructive command warnings** — rm -rf, DROP TABLE, force-push, etc. will
>    pause for confirmation before executing.
> 2. **Edit boundary** — file edits restricted to `<path>/`. Edits outside are
>    refused. Run `/unfreeze` to lift just the boundary, or end the session to
>    clear everything.

## How to behave under this skill

Apply the rules from both `/careful` and `/freeze`:

- Before every Bash tool call, check the command against the destructive patterns
  in `careful/SKILL.md`. If matched, pause and confirm.
- Before every Edit/Write, check `file_path` against the freeze boundary. If
  outside, refuse and suggest widening or removing the boundary.

## Why this exists

Production touches and debugging in live systems carry the highest blast radius.
Guard mode pairs both common-mistake categories — accidental destructive shell
commands and accidental edits in the wrong place — in one toggle so you don't
have to remember to enable each one separately.

## See also

- `/careful` — destructive-command warnings only
- `/freeze` — edit boundary only
- `/unfreeze` — clear the edit boundary
