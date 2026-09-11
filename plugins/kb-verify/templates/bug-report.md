# <Verb + object: "Refund window is 7 days in code; article says 10">
Status: needs-triage
Resolution: unset            <!-- human: confirmed | not-a-bug | duplicate | wontfix-low-priority -->
Labels: kb-verify, bug-candidate, area/<topic>
Source: kb-verify <run-id> · article: <article-id> · repo: <org/repo>@<commit>

<!-- Written once by kb-verify (verdict CODE_BUG). Humans own Status:, Resolution: and ## Comments.
     Status: uses the environment's triage labels (needs-triage, needs-info, ready-for-agent,
     ready-for-human, wontfix). The verifier never edits this file after creating it. -->

## Expected behavior (per the article)

> <verbatim quote from the article, <= 200 characters, in the article's language>
> <English translation of the quote, only when the article is not in English>

<One sentence: what the reader is promised.>

## Observed behavior (in code)

<One or two sentences: what the code does at the pinned commit, with the value or path.>

## Evidence (claim → code, intent witness)

| Claim | Article says | Code says | Evidence | Intent witness |
| --- | --- | --- | --- | --- |
| <c2 (limit, material)> | <10 days> | <7 days> | `<path>:<line>@<commit>` — `<snippet <= 200 chars, redacted>` | <test> `<path>:<line>@<commit>` agrees-with article |

Skeptic: <CONFIRMED> — <reason>

## Key Assumptions Check

| assumption | class | if_false | tested |
| --- | --- | --- | --- |
| <the locale served to the reader is the language of the article> | <solid> | <...> | <true> |
| <no feature flag diverts the code path that was read> | <solid> | <...> | <true> |
| <no tenant- or plan-level override changes the value> | <caveat> | <...> | <true> |
| <the pinned default-branch commit is what runs in production> | <caveat> | <...> | <true> |
| <two pieces of evidence from the same file are not corroboration> | <solid> | <...> | <true> |

## How a human confirms (≤5 steps)

1. <Open `<path>` at `<commit>` and read line <line>.>
2. <Run or read the test `<path>:<line>`; it asserts the article's value.>
3. <Check the deployed environment for the flag/override named in the KAC, if any.>

## What was NOT verified

- <other claims of the article and why (NOT_FOUND, non-material, deferred to another article)>
- <assumptions that stayed untested>

## Comments

<!-- humans append below; newest last -->
