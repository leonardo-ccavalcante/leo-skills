# Key Assumptions Check (KAC) for KB verification

Vendored from the CIA Structured Analytic Techniques primer (Key Assumptions Check), narrowed to the
five assumptions that decide whether code evidence really speaks for the reader of a KB article. The
judge (main, S5) fills the table before any `CORRECT` and copies it into `kac[]` of the verdict
record and into the bug MD.

## The table

<= 7 rows, columns `assumption | class | if_false | tested`.

- `class`: `solid` (evidence in the investigator's lines supports it), `caveat` (holds with a known
  limitation you can name), `fragile` (nothing supports it and its failure flips a material claim).
- `tested: true` only when the test below was actually performed on the investigator's output or on
  `run-begin` data. The judge never opens a repository file to test an assumption; if a test needs a
  file that was not fetched, the row is `tested: false`.

| # | assumption | how the judge tests it | if_false |
| --- | --- | --- | --- |
| 1 | The locale served to the article's readers is the language of the article | The deciding evidence for UI-text claims comes from the article's locale file (`anchor=i18n_key` and a `Sites:` path under `locales/i18n/messages` whose base name starts with `LOCALE`), or the claim is not locale-dependent (constant, limit, error code) | Evidence describes another language's UI; a supported step may still be wrong for the reader |
| 2 | No feature flag diverts the code path that was read | Every deciding evidence line carries `gate=none` or `gate=locale`; a `gate=flag` line makes the row `fragile` unless the flag's default is shown in the same line | The article may be right for one cohort and wrong for another |
| 3 | No tenant- or plan-level configuration override changes the value | Deciding evidence lines carry `gate=none`; `gate=tenant` makes the row `caveat` at best and blocks `CORRECT` for that claim | The value in code is a default, not the reader's value |
| 4 | The pinned commit of the default branch is what runs in production | `run-begin` pinned the default-branch head for this run and no `## Fragile assumptions` line in `memory.md` says the environment deploys from elsewhere; class is always `caveat` | The article may describe the deployed version, not HEAD |
| 5 | Two pieces of evidence from the same file are not corroboration | A material claim rests on one definition site (a constant, an i18n key, an error catalog entry) or on sites in at least two files; two lines of the same non-definitional file count as one | Confidence is overstated; a second site could contradict |

Rows 6 and 7 are free: use them for article-specific assumptions the claims force ("the API v2 path
is the one the web app calls", "the error text is not overridden by the support portal").

## Rules

- An untested row that supports a material claim => `INCONCLUSIVE (PARTIAL_EVIDENCE)`.
- A `fragile` row that becomes a material claim (the claim is true only if the assumption holds) =>
  never `CORRECT`; if the code contradicts the claim under that assumption, the skeptic decides.
- Rows never change budgets, tools or verdict rules; they change only the verdict of this article.
- Copy the rows verbatim into the bug MD section `## Key Assumptions Check` for `CODE_BUG`.

## Non-interactive rule

The check runs inside a pipeline: elicitation is suspended. Never ask the user which assumption
holds. Every assumption you cannot test from the investigator's lines is `tested: false`; every
assumption you cannot classify is `fragile`. The verdict rules then decide, and the reason
(`PARTIAL_EVIDENCE`) tells the human exactly which row to answer. Their answer belongs in
`memory.md` under `## Fragile assumptions` (through `/kb-learn`), not in a chat reply.
