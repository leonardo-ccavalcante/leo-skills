# Calibration on the target machine (operator order)

Dependencies: Claude Code with plugins; `gh` authenticated with a fine-grained token (Contents: Read, Metadata: Read); `jq`; `realpath`; `/usr/bin/patch`; `shasum -a 256`; `plugin.json` with `"hooks": "./hooks/hooks.json"`.

1. Spike (three commands, record the answers here): does `gh api search/code` answer for the repo? Does the fine-grained token work with search? Does `git/trees/<sha>?recursive=1` truncate?
   - search/code: `<yes|no|needs classic token>` · token with search: `<yes|no>` · trees truncated: `<yes|no, size>`
2. Manual: confirm on GitHub that the token has no write permission (`gh auth status` does not show fine-grained permissions).
3. `/plugin marketplace add <owner>/kb-verify` · `claude plugin install kb-verify@<marketplace>` · `enabledPlugins` only in the KB project's `.claude/settings.json`.
4. `bash <plugin>/scripts/kbv.sh config-init <kb_root>`; answer the three questions (frontmatter fields for title/tags/topic/status; rewriter output folder; "ready" status value); save `<kb_root>/kb-verify.config.json`; add the `permissions.allow` snippet from the README.
5. Start `claude` in `<kb_root>`: `SessionStart` prints `ARMED` and the `jq` path. Start it outside: `DISARMED`.
6. S0 canary: in the armed session ask for `Bash: true`; it must be denied with a reason starting `kb-verify:`.
7. Guard matrix with real paths: `Write` to inbox / new triage MD / `<stem>.kb-verify.diff` allowed; `Write`/`Edit` on an article, `.kb-verify/`, the config, `~/.claude/settings.json` denied; `gh api`, `git`, `curl` denied; `WebFetch` denied.
8. `/kb-verify <articles folder>`; `repo-index` runs by itself on the first article (note `tree_partial` / `i18n_partial`).
9. Measure per article: searches, fetches, seconds to the first `path:line@commit`, 429s, verdict and reason (the S9 line and `investigator{}` in `verdicts.jsonl`).
10. Targets after ten articles: right file among the first three candidates >= 70%; INCONCLUSIVE <= 40%; NOT_LOCATED <= 20%; zero false CODE_BUG; >= 80% human agreement on CORRECT and DOC_OUTDATED; >= 1 CODE_BUG confirmed by an engineer or diff accepted by the KB owner.
11. Triage: humans move `Status:` and `Resolution:` in the bug MDs and fill `<triage_dir>/feedback.md` (`confirmed | rejected | accepted | discarded`).
12. `/kb-learn`; after the first triage `memory.md` should hold at least one `Search heuristics` line.
13. Decide the open questions, record the answers here:
   - Q1 Does the rewriter regenerate articles and overwrite edits? `<answer, owner, date>` (blocks any `apply`; if yes, the only return channel is mapping + verdict)
   - Q2 May redacted code snippets (<= 200 chars) live in the KB repo (bug MD, `verdicts.jsonl`)? `<answer>` (if no, bug MDs cite `path:line@commit` only)
   - Q3 If the fine-grained token does not work with `search/code`: classic token with write power, or drop layer (c)? `<answer>`
   - Q4 Who moves `Status:`/`Resolution:` and fills `feedback.md`, and how often? `<answer>` (without it `/kb-learn` has no signal)
14. Only then consider `apply`, kb-learn v2 (automation) and discovery beyond tree + i18n.

Accepted risks, recorded: (1) if search requires a classic token with `repo` scope, "read-only" rests on the hooks alone; (2) the main agent cannot be restricted by an allowlist, so the hook is its only barrier.
