# Verdict record

One JSON object per article per run, appended as one line to `<kb_root>/.kb-verify/verdicts.jsonl`
by `kbv append-verdict`. The main writes the same object (plus the inbox-only `mapping_delta`) to
`INBOX/verdict-<sha12>.json`; the script validates it, redacts snippets and appends it. Snippets are
<= 200 characters and always come from the cached file at the pinned commit.

## Example (DOC_OUTDATED)

```json
{
  "run": "20260912-1430-ab12",
  "commit": "abc123def4567890abc123def4567890abc123de",
  "article": {
    "id": "articles/billing/cancelar-assinatura.md",
    "sha256": "9f2c1e7a0b4d5c6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6",
    "title": "Cancelar assinatura"
  },
  "verdict": "DOC_OUTDATED",
  "claims": [
    {
      "id": "c1", "type": "step", "material": true,
      "text": "Acesse Configuracoes > Cobranca > Cancelar assinatura",
      "status": "SUPPORTED",
      "evidence": [
        {"file": "apps/web/src/i18n/pt-BR.json", "line": 88,
         "commit": "abc123def4567890abc123def4567890abc123de",
         "snippet": "\"billing.cancel.cta\": \"Cancelar assinatura\","}
      ]
    },
    {
      "id": "c2", "type": "limit", "material": true,
      "text": "O reembolso e concedido em ate 10 dias apos o cancelamento",
      "status": "CONTRADICTED",
      "evidence": [
        {"file": "apps/billing/src/refund.ts", "line": 42,
         "commit": "abc123def4567890abc123def4567890abc123de",
         "snippet": "export const REFUND_WINDOW_DAYS = 7;"}
      ],
      "intent": {"kind": "none"}
    },
    {
      "id": "c3", "type": "condition", "material": false,
      "text": "Planos anuais seguem a mesma regra",
      "status": "UNVERIFIED", "evidence": []
    }
  ],
  "kac": [
    {"assumption": "pt-BR is the locale served to the article's readers", "class": "solid",
     "if_false": "c1 evidence points at the wrong string table", "tested": true},
    {"assumption": "No feature flag wraps REFUND_WINDOW_DAYS", "class": "solid",
     "if_false": "7 days applies only to a cohort", "tested": true},
    {"assumption": "No tenant or plan override of the refund window", "class": "caveat",
     "if_false": "the article may be right for enterprise tenants", "tested": true},
    {"assumption": "Default-branch head is what runs in production", "class": "caveat",
     "if_false": "the article may describe the deployed version", "tested": true},
    {"assumption": "refund.ts is the single definition site (not corroboration)", "class": "solid",
     "if_false": "another module could define a different window", "tested": true}
  ],
  "investigator": {"layer": "e", "anchor_type": "symbol", "search_calls": 3, "fetch_calls": 6, "seconds": 41},
  "skeptic": {"result": "CONFIRMED",
              "reason": "apps/billing/src/refund.ts:42@abc123def456 is the only definition; no override within the module"},
  "actions": {"doc_diff": "articles/billing/cancelar-assinatura.kb-verify.diff"},
  "notes": [
    "c3 non-material, unverified (1 of 3 claims)",
    "tree_partial=false i18n_partial=false search_available=true"
  ]
}
```

An `INCONCLUSIVE` record adds `"inconclusive_reason": "NOT_LOCATED"` and has `"actions": {}`.
A `CODE_BUG` record has `"actions": {"bug_report": "kb-verify/triage/bugs/0007-refund-window-is-7-days-in-code-article-says-10.md"}`
and at least one material claim with `"intent": {"kind": "test", "file": "...", "line": 18, "commit": "...", "agrees_with": "article"}`.

## Fields

| field | type | required | rule |
| --- | --- | --- | --- |
| `run` | string | yes | run id from `run-begin` |
| `commit` | string | yes | full pinned commit sha of the run |
| `article.id` | string | yes | article path relative to `kb_root` (same value as in `mapping.json`) |
| `article.sha256` | string | yes | 64 hex, from `kbv frontmatter`; `pending` compares it with the file |
| `article.title` | string | yes | intake title |
| `verdict` | enum | yes | `CORRECT`, `DOC_OUTDATED`, `CODE_BUG`, `INCONCLUSIVE` |
| `inconclusive_reason` | enum | only when `INCONCLUSIVE` | `NOT_LOCATED`, `PARTIAL_EVIDENCE`, `AMBIGUOUS_INTENT`, `NEEDS_RUNTIME`, `ARTICLE_UNPARSEABLE`, `BUDGET_EXHAUSTED`, `RATE_LIMITED`, `GH_AUTH`, `SEARCH_UNAVAILABLE`, `DIFF_APPLY_FAILED`, `SKEPTIC_REFUTED`, `SKEPTIC_UNSURE`, `SCRIPT_ERROR`; omitted otherwise |
| `claims[]` | array | yes | <= 15; may be empty only for `ARTICLE_UNPARSEABLE` |
| `claims[].id` | string | yes | `c1`..`c15` |
| `claims[].type` | enum | yes | `step`, `condition`, `behavior`, `error_msg`, `limit`, `permission` |
| `claims[].material` | boolean | yes | see SKILL.md S2 |
| `claims[].text` | string | yes | verbatim claim, <= 200 chars, article language |
| `claims[].status` | enum | yes | `SUPPORTED`, `CONTRADICTED`, `NOT_FOUND`, `UNVERIFIABLE`, `NEEDS_RUNTIME`, `UNVERIFIED` (not checked: deferred to another article or non-material and skipped) |
| `claims[].evidence[]` | array | yes | >= 1 entry when `SUPPORTED` or `CONTRADICTED`; may be empty otherwise |
| `claims[].evidence[].file` | string | yes | repo path at the pinned commit (original name, not `_dot_`) |
| `claims[].evidence[].line` | integer | yes | 1-based line in the cached file |
| `claims[].evidence[].commit` | string | yes | the pinned commit |
| `claims[].evidence[].snippet` | string | yes | that line, trimmed, <= 200 chars; redacted by the script |
| `claims[].intent` | object | only when `CONTRADICTED` | `{"kind":"none"}` (no witness: `agrees_with` is omitted, and the validator accepts that) or `{kind, file, line, commit, agrees_with}` with `kind` in `test`, `typed_const`, `error_catalog`, `changelog` and `agrees_with` in `article`, `code` |
| `kac[]` | array | yes | <= 7 rows; may be empty only when no claim reached S5 |
| `kac[].assumption` | string | yes | one sentence |
| `kac[].class` | enum | yes | `solid`, `caveat`, `fragile` |
| `kac[].if_false` | string | yes | consequence for the verdict |
| `kac[].tested` | boolean | yes | see `key-assumptions-check.md` |
| `investigator.layer` | enum | yes | `a`..`e`, the layer that produced the deciding evidence; `a` when the investigator did not run |
| `investigator.anchor_type` | enum | yes | `i18n_key`, `error_code`, `symbol`, `literal`, `path`; `path` when the investigator did not run |
| `investigator.search_calls` | integer | yes | from `Stats:`; `0` when it did not run |
| `investigator.fetch_calls` | integer | yes | from `Stats:`; `0` when it did not run |
| `investigator.seconds` | integer | yes | wall-clock estimate of S4; `0` when unknown |
| `skeptic.result` | enum | yes | `CONFIRMED`, `REFUTED`, `UNSURE`, `NOT_RUN` |
| `skeptic.reason` | string | yes | first line of the skeptic, <= 200 chars; `"verdict did not require the skeptic"` when `NOT_RUN` |
| `actions.bug_report` | string | required for `CODE_BUG` | path of the bug MD relative to `kb_root` |
| `actions.doc_diff` | string | required for `DOC_OUTDATED` | path of the `.kb-verify.diff` relative to `kb_root` |
| `notes[]` | array of strings | yes | may be empty; unverified claims, injection-like content, partial index flags, script messages |

`append-verdict` rejects: a verdict outside the enum; `SUPPORTED`/`CONTRADICTED` without evidence
(`file`, integer `line`, `commit`); a missing or incomplete `investigator{}`; `CODE_BUG` without
`skeptic.result: "CONFIRMED"`, `actions.bug_report` and a material contradicted claim whose
`intent.agrees_with` is `"article"`; `DOC_OUTDATED` without `actions.doc_diff`; `INCONCLUSIVE` without
`inconclusive_reason`. On rejection nothing is written: fix the object once and resend.

## Inbox-only: `mapping_delta`

Present in `INBOX/verdict-<sha12>.json`, consumed by `kbv mapping-update`, not persisted in
`verdicts.jsonl`:

```json
"mapping_delta": {
  "topic": "cancel-subscription",
  "article": "articles/billing/cancelar-assinatura.md",
  "aliases": ["Cancelar assinatura", "billing.cancel.cta"],
  "hits": [{"path": "apps/billing/src/refund.ts", "symbols": ["REFUND_WINDOW_DAYS"]}],
  "stale": ["apps/billing/src/legacy/cancel.ts"]
}
```

`hits` are paths that yielded `SUPPORTED` or `CONTRADICTED` evidence (`hits += 1`, `last_verified`
and `commit` refreshed); `stale` are candidates that returned `NOT_FOUND` at the pinned commit
(`stale: true`, never deleted); `aliases` are titles and anchors that actually matched. The
`repo{}` block of `mapping.json` (`index_commit`, `tree_partial`, `i18n_partial`,
`search_available`) is maintained by `repo-index` and the transport, not by the main.
