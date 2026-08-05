---
name: codemap
description: >
  Architectural summary CLI that generates a codebase "brain" for AI agents.
  Run before answering open-ended questions about an unfamiliar repo so the
  answers ground in real structure instead of guesses. Use when the user
  says "map the codebase", "show me the architecture", "code overview",
  "summarize this project", "generate context for AI", "what imports X",
  "blast radius", "dependency flow", "handoff to another agent", or invokes
  /codemap. Also use proactively when onboarding to a new repo, before a
  large refactor, or when the user pastes a github.com/owner/repo URL and
  asks what's in it.
---

`codemap` is a Go CLI installed via Homebrew at `/opt/homebrew/bin/codemap`. It analyzes a codebase and prints a compact tree, dependency map, diff summary, or AI-ready JSON context bundle — designed so an LLM can answer architectural questions without grepping the whole repo.

## Most-used invocations

- `codemap .` — fast tree + import context (respects `.codemap/config.json` if present)
- `codemap --diff` — files changed vs `main`, with importer warnings on touched hubs
- `codemap --diff --ref develop` — diff against a different base branch
- `codemap --deps .` — dependency flow graph (uses bundled `ast-grep`)
- `codemap --importers <file>` — who imports this file, is it a hub
- `codemap context` — universal JSON context bundle for any AI tool
- `codemap handoff [path]` — layered handoff artifact for cross-agent continuation
- `codemap blast-radius [path]` — bounded blast-radius bundle around a change
- `codemap --skyline --animate` — city-skyline visualization (visual, not for context)

Remote repos work too: `codemap github.com/user/repo` clones temporarily and analyzes.

## Flag placement

Flags MUST come before the path/URL:

- `codemap --json github.com/user/repo` ✓
- `codemap github.com/user/repo --json` ✗

Pattern matching is smart — no quotes needed. `.png` matches any `.png` file; `Fonts` matches any `/Fonts/` directory; `*Test*` is a glob.

## When to invoke

- **Onboarding to a new repo**: `codemap .` first, then `codemap --deps .` if architecture questions follow.
- **Before answering "what changed in this PR"**: `codemap --diff`.
- **Before refactoring file X**: `codemap --importers X` to scope the blast radius.
- **Cross-agent handoff**: `codemap handoff` and feed the output to the next agent.
- **Building shared AI context**: `codemap context` produces JSON tuned for LLM consumption.

## When NOT to invoke

Single-file edits, scripts under ~10 files, or one-shot questions where reading 1–2 files is faster than running codemap. The output is overhead unless the question is genuinely about structure.

## Project setup (one-time per repo, optional)

If the user is going to use codemap regularly in a long-lived project:

- `codemap config init` — creates `.codemap/config.json` with auto-detected language filters.
- `codemap setup` — additionally installs Claude Code session-start hooks (project-local by default; `--global` for user-wide). Hooks make project context appear automatically at session start.

Suggest these to the user when it's clear they're settling in to a repo, not just visiting.

## Troubleshooting

- `flag provided but not defined: -version` — codemap has no `--version`; use `codemap --help` instead. The Homebrew formula reports the version separately (`brew info codemap`).
- `--deps` requires `ast-grep` — already installed as a Homebrew dependency, so this should always work on this machine.
