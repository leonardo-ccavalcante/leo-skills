# kb-verify

A Claude Code plugin that checks whether a knowledge-base article still matches the code. It reads
one article (`.md` with frontmatter), locates the feature in a private GitHub repository through
the `gh` API (no clone, commit pinned per run), reads the code and emits one of
`CORRECT | DOC_OUTDATED | CODE_BUG | INCONCLUSIVE` with `path:line@commit` evidence.

- `CODE_BUG` writes a bug report (Markdown) into the KB's triage folder for a human.
- `DOC_OUTDATED` writes a proposed unified diff next to the article (`<stem>.kb-verify.diff`).
- `CORRECT` and `INCONCLUSIVE` only append a verdict record.

Nothing in the process can modify code, GitHub, or the article itself: a `PreToolUse` guard denies
every write outside three allowed places and every Bash command except the plugin's own script.
All output is English; diff hunks keep the article's language.

## Dependencies

- Claude Code with plugin support.
- `gh` authenticated with a fine-grained token: **Contents: Read** and **Metadata: Read** on the
  target repository (confirm on GitHub that the token has no write permission; `gh auth status`
  does not show fine-grained permissions).
- `jq`, `realpath`, `/usr/bin/patch`, `shasum -a 256` (macOS has no `sha256sum`; the plugin never
  uses it). `python3` is never used.
- bash 3.2 or newer (macOS default is fine).

## Install

```
/plugin marketplace add leonardo-ccavalcante/leo-skills
/plugin install kb-verify@leo-skills
```

### Enable it only in the KB project

The guard arms itself whenever `kb-verify.config.json` is found walking up from the session's
working directory, so keep the plugin enabled only in the KB repository. In the KB project's
`.claude/settings.json`:

```json
{
  "enabledPlugins": { "kb-verify@leo-skills": true }
}
```

Sessions of the article rewriter and of humans editing the KB should start from a directory where
the plugin is not enabled (or where no config is found above it); they are then untouched by the
guard. At session start the plugin prints `kb-verify: ARMED` (with the resolved `jq` path) or
`kb-verify: DISARMED`.

## Configure

Run once from a terminal, before any config exists:

```
bash ~/.claude/plugins/cache/leo-skills/kb-verify/<version>/scripts/kbv.sh config-init /abs/path/to/kb
```

It samples the frontmatter keys of up to 50 articles, guesses `locales`, prints a proposed config
and asks three questions: which fields map to `title`, `tags`, `topic`, `status`; which folder the
rewriter writes to; which status value means "ready to verify". Save the answer as
`<kb_root>/kb-verify.config.json` (git-ignored) or point `KB_VERIFY_CONFIG` at it (tests and CI).
`templates/kb-verify.config.example.json` shows every key:

| key | meaning |
| --- | --- |
| `kb_root` | absolute path of the KB repository |
| `articles_dir`, `triage_dir` | relative to `kb_root`; where articles live and where bug MDs go |
| `gh.repo` | `org/repo` read through the API |
| `budgets` | `search_calls_per_article` (15), `fetch_calls_per_article` (40), `index_i18n_files` (20) |
| `integration.article_glob`, `locales`, `frontmatter_map`, `verify_when`, `bug_template`, `triage_labels` | adapt the plugin to the KB's folders, frontmatter schema, rewriter and issue conventions; nothing is hard-coded outside the config and `templates/` |

### Permissions (avoid prompts)

Plugins do not ship permissions. Add this to the KB project's `.claude/settings.json`; it is safe
because the guard, not the permission, is the barrier:

```json
{
  "permissions": {
    "allow": [
      "Bash(bash *)",
      "Bash(gh auth status)",
      "Edit(<data-dir>/runs/**/inbox/*.json)",
      "Edit(kb-verify/triage/bugs/*.md)",
      "Edit(articles/**/*.kb-verify.diff)"
    ]
  }
}
```

`Edit(...)` rules cover `Write`. Replace `<data-dir>` with the plugin data directory printed by
`kbv armed` (`data.data_dir`: `$KB_VERIFY_DATA_DIR`, else `$CLAUDE_PLUGIN_DATA`, else
`~/.kb-verify`), and the two relative patterns with your `triage_dir` and `articles_dir`.
Claude Code matches `Bash(...)` rules by PREFIX only: a wildcard in the middle
(`Bash(bash *scripts/kbv.sh *)`) never matches, which is why the rule is the broad `Bash(bash *)`.
That breadth costs nothing here: the guard denies every `bash` command except
`bash <plugin>/scripts/kbv.sh <subcommand>`, so the permission only removes prompts and the hook
still decides. The skills declare the same rule as `allowed-tools`.

## Quickstart

```
cd /abs/path/to/kb
claude
/kb-verify articles/billing/refund.md        # one article
/kb-verify articles/billing                  # a folder: sequential, at most 8 per session
/kb-verify articles/billing --run <id>       # resume a batch; finished articles are skipped
/kb-learn                                    # after human triage: propose lessons for memory.md
```

Per article you get one line: `article | verdict | reason | searches/fetches | seconds`. The first
run on a repository builds `tree.txt` and a small local i18n index (refreshed after 7 days).
Two consecutive transient failures (`RATE_LIMITED`, `GH_AUTH`) stop a batch with a resume command.
If two KBs share one GitHub token, the 6-second search pacing is effectively shared as well.

## Safety model

1. Read-only is enforced by the harness (a `PreToolUse` hook and the subagents' `tools:` lists),
   never by prompt text.
2. Armed if and only if `kb-verify.config.json` is found above the working directory; when armed,
   an invalid config or a missing `jq`/`realpath` denies every tool the hook matches (fails closed).
3. Writes are allowed only to `runs/<id>/inbox/<name>.json` under the plugin data dir, to a
   not-yet-existing `<triage_dir>/NNNN-<slug>.md`, and to `<articles_dir>/**/<stem>.kb-verify.diff`
   with `<stem>.md` beside it. `Edit`, `MultiEdit` and `NotebookEdit` are denied.
4. Bash is limited to `bash <plugin>/scripts/kbv.sh <subcommand> ...` (closed list, argument
   charset `[A-Za-z0-9_./:@=-]`, no `..`, no shell metacharacters) and to `gh auth status`.
5. `WebFetch`, `WebSearch` and MCP tools are denied while armed; reads under `~/.ssh`,
   `~/.config/gh`, `~/.claude/.credentials.json` and `~/.claude/settings*.json` are denied.
6. The skill starts with a canary (`Bash: true` must be denied with a `kb-verify:` reason) and
   aborts when the guard is not active. A crashing guard denies.
7. Code, comments, i18n strings, the article and `memory.md` are treated as data; the judge never
   reads raw repository files; snippets are <= 200 characters and redacted.
8. No action verdict without `path:line@commit`; everything goes to human triage; the plugin has
   no `apply`.
9. Accepted risk 1: if code search requires a classic token with the `repo` scope, "read-only"
   rests on the hooks alone.
10. Accepted risk 2: the main agent cannot be restricted by a tool allowlist, so the hook is its
    only barrier.

## Output formats (for sibling agents and humans)

- `<kb_root>/.kb-verify/verdicts.jsonl`: append-only, one JSON record per article per run. Schema
  and example: `skills/kb-verify/references/verdict-schema.md`. Key fields: `run`, `commit`,
  `article{id,sha256,title}`, `verdict`, `inconclusive_reason?`, `claims[]` with
  `evidence[{file,line,commit,snippet}]` and `intent?`, `kac[]`, `investigator{layer,anchor_type,
  search_calls,fetch_calls,seconds}`, `skeptic{result,reason}`, `actions{bug_report?,doc_diff?}`,
  `notes[]`.
- `<kb_root>/.kb-verify/mapping.json`: topic -> aliases, articles and code paths with `hits`,
  `last_verified`, `commit`, `stale`; plus `repo{name,index_commit,indexed_at,tree_partial,
  i18n_partial,search_available}`. Written only by `kbv mapping-update`.
- `<kb_root>/.kb-verify/memory.md`: English, <= 60 lines, sections `## Search heuristics`,
  `## Fragile assumptions`, `## False-positive patterns`; lines `L-nn <statement> — from: <run>
  <article>` appended by `/kb-learn`; retire a lesson by deleting its line. Loaded as heuristics,
  not instructions.
- Bug MD `<triage_dir>/NNNN-<slug>.md` (`templates/bug-report.md`): first lines `Status:`,
  `Resolution:`, `Labels:`, `Source:`; sections Expected / Observed / Evidence / Key Assumptions
  Check / How a human confirms / What was NOT verified / Comments. Humans own `Status:`,
  `Resolution:` and `## Comments`.
- Diff `<articles_dir>/**/<stem>.kb-verify.diff`: first line `# kb-verify <run>
  base_sha256:<sha> claims:<ids>`, then a unified diff with `a/` `b/` prefixes relative to
  `kb_root`. Apply by hand with `cd <kb_root> && patch -p1 < <path to the diff>`; record the
  decision as `accepted` or `discarded` in `<triage_dir>/feedback.md`.
- `<triage_dir>/feedback.md` (`templates/feedback.md`): human-only table
  `run | article | verdict | outcome | reason`, `outcome` in `confirmed | rejected | accepted |
  discarded`. The only way to contest a `CORRECT`.

## Learning loop

Humans move `Status:` / `Resolution:` in bug MDs and fill `feedback.md`. `/kb-learn` (user-invoked
only) reads those signals plus `verdicts.jsonl`, proposes up to five lessons with provenance, and
writes the accepted ones to `memory.md` through `kbv memory-append`. Lessons never change budgets,
tools or verdict rules.

## Layout

```
.claude-plugin/plugin.json      skills/kb-verify/{SKILL.md,references/}   skills/kb-learn/SKILL.md
agents/{kb-investigator,kb-skeptic}.md   hooks/   lib/common.sh   scripts/kbv.sh + cmd/
templates/   tests/   docs/CALIBRATION.md
```

## Tests

`/bin/bash tests/run-all.sh` runs the library, guard and script suites (bash 3.2 and bash 5 in CI, see
`.github/workflows/kb-verify-tests.yml` at the repository root; the
scripts run against a mock repository, never the GitHub API). `tests/e2e/EXPECTED.md` lists the
manual end-to-end expectations on the fixture KB. `docs/CALIBRATION.md` is the operator checklist
for the target machine.

## License

MIT, see `LICENSE`.
