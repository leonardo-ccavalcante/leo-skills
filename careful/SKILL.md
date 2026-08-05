---
name: careful
description: |
  Safety guardrails for destructive commands. Activates a defensive posture where the agent
  pauses and warns before running rm -rf, DROP TABLE, TRUNCATE, git push --force,
  git reset --hard, kubectl delete, docker rm -f / system prune, and similar
  destructive operations — the user can override each warning. Use this skill whenever
  the user says "be careful", "careful mode", "prod mode", "safety mode", "guard rails on",
  "warn before destructive", or is about to touch production, debug a live system, work
  in a shared environment, or do anything where a single typo could destroy data or rewrite
  history. Also triggers when the user explicitly invokes /careful.
---

# Careful Mode — Destructive Command Guardrails

Safety mode is now **active**. Every bash command you propose will be vetted against the
destructive-pattern list below before execution. If a destructive command is detected,
stop, surface the risk plainly, and ask the user to confirm — do not auto-run.

## What's protected

| Pattern | Example | Risk |
|---------|---------|------|
| `rm -rf` / `rm -r` / `rm --recursive` | `rm -rf /var/data` | Recursive delete |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` | Data loss |
| `TRUNCATE` | `TRUNCATE orders;` | Data loss |
| `git push --force` / `-f` | `git push -f origin main` | History rewrite |
| `git reset --hard` | `git reset --hard HEAD~3` | Uncommitted work loss |
| `git checkout .` / `git restore .` | `git checkout .` | Uncommitted work loss |
| `git branch -D` | `git branch -D feature` | Branch deleted with no merge check |
| `kubectl delete` | `kubectl delete pod` | Production impact |
| `docker rm -f` / `docker system prune` | `docker system prune -a` | Container/image loss |
| `dd if=` over a device | `dd if=/dev/zero of=/dev/sda` | Disk wipe |

## Safe exceptions (no prompt needed)

These are routine cleanup paths — running them in build/dev contexts is normal and benign:

- `rm -rf node_modules`
- `rm -rf .next` / `.turbo` / `.cache` / `coverage` / `build` / `dist` / `__pycache__`
- `rm -rf <tempdir>` where `<tempdir>` is clearly scoped (e.g. `/tmp/<unique-name>`)

## How to behave under this skill

1. Before running any Bash tool call, scan the command string for the patterns above.
2. If matched and not in the safe-exceptions list, **do not execute**. Instead:
   - State plainly what the command will destroy, in concrete terms ("this will delete
     all rows in `users` and cannot be undone").
   - Suggest a safer alternative when one exists (e.g. `git revert` instead of
     `git reset --hard`; `DELETE ... LIMIT` with WHERE for sample checks).
   - Ask the user to confirm before proceeding.
3. If the user explicitly confirms, run it. A confirmation applies only to that one
   command — re-prompt on the next destructive operation.
4. Never bypass these checks because "the user clearly wants it" — that's exactly the
   moment when an explicit confirmation has the highest value.

## Why this exists

The cost of an unwanted destructive action (lost work, dropped table, force-pushed
history) is high and often irreversible. The cost of pausing to confirm is low.
Careful mode tilts the default toward the cheaper option.

## Turning off

This mode applies for the current session. The user can disable it by saying
"stop being careful", "exit careful mode", or "normal mode".
