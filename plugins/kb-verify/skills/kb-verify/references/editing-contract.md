# Editing contract for the DOC_OUTDATED diff

Vendored from the karpathy guidelines ("think before coding, simplicity first, surgical changes,
goal-driven execution"), reoriented for prose. The diff is a proposal that a human accepts or
discards with one line in `feedback.md`; it must be boring to review. If any rule below cannot be
met, do not write a diff: record `INCONCLUSIVE` with the doubt in `notes[]`. A wrong diff costs more
than a missing one.

## 1. Think before editing: every changed line traces to evidence

- A hunk exists only because a material claim is `CONTRADICTED` with `path:line@commit` and the
  skeptic said `CONFIRMED`. If you cannot name the claim id and the evidence line for a changed line,
  leave the line alone.
- The header line `# kb-verify <run> base_sha256:<sha256> claims:<c2,c5>` lists every claim the hunks
  rely on; every hunk maps to at least one listed claim, and every listed claim has at least one hunk.
- State the fact you are correcting in the S9 line and in `notes[]` (`c2: 10 days -> 7 days per
  apps/billing/src/refund.ts:42@<commit>`). Do not guess a value the code does not show.

## 2. Simplicity first: change the fact, not the article

- The minimum characters that make the sentence true at the pinned commit. A number, a menu label, an
  error text, a condition. Not a rewrite of the paragraph.
- No caveats the code does not force, no "note that", no extra explanation, no new sections, no
  reordering, no "while I was here" improvements to adjacent sentences.
- One hunk per corrected passage. Two claims in the same sentence may share a hunk; two claims far
  apart never do.

## 3. Surgical changes: preserve everything else byte for byte

- Never touch the frontmatter block (between the first two `---` lines), including unknown fields.
- Preserve headings and their levels, step numbering, list markers, indentation, blank lines, links,
  image references, code fences, HTML comments, typographic quotes, trailing spaces and line endings.
- Preserve tone, person, register and language. Hunks are written in the language of the article;
  only the header line is English. Never translate, never fix typos outside the corrected sentence,
  never renumber, never change a heading's wording.
- Never delete a section or a step. If a step no longer exists in the code, replace its text with the
  current behavior and keep its number; if the correct replacement is unknown, do not write a diff.
- Do not merge or split paragraphs; keep the line structure so `patch` applies cleanly.

## 4. Goal-driven: the diff is done when it applies and is checkable

- Success = `KBV diff-check` returns `OK` (the diff applies with `/usr/bin/patch --dry-run` to a temp
  copy of the article at `base_sha256`) and a reviewer can verify each hunk against one
  `path:line@commit` shown in the bug of the verdict record.
- If `diff-check` fails once, re-derive the hunk from the article you read in S1 (context lines must
  be verbatim) and resend once; a second failure is `INCONCLUSIVE (DIFF_APPLY_FAILED)`.

## Format

```
# kb-verify <run> base_sha256:<64 hex> claims:c2
--- a/<article-id>
+++ b/<article-id>
@@ -12,3 +12,3 @@
 context line (verbatim)
-old line (verbatim)
+new line
 context line (verbatim)
```

- Unified diff, 3 lines of context, `a/` and `b/` prefixes on the article path relative to
  `kb_root`, LF line endings, final newline; the file ends with a newline.
- The header comment is the first line; `patch` ignores it. Humans apply the proposal with
  `cd <kb_root> && patch -p1 < <article-dir>/<stem>.kb-verify.diff` (the plugin never applies it).
- The file name is `<stem>.kb-verify.diff` next to `<stem>.md`; the guard allows that name only.
