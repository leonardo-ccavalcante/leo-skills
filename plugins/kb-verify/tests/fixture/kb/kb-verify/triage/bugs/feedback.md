# kb-verify feedback

Written by humans only; the verifier never edits this file. One row per decision about a verdict.
`outcome` is one of `confirmed` (a CODE_BUG held), `rejected` (a CODE_BUG or a CORRECT was wrong),
`accepted` (a DOC_OUTDATED diff was applied), `discarded` (a DOC_OUTDATED diff was thrown away).
This table is the only channel to contest a `CORRECT`. `/kb-learn` reads it.

| run | article | verdict | outcome | reason |
| --- | --- | --- | --- | --- |
