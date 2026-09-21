# Cards, verdicts and report templates

All artifacts are in English. Customers appear by first name, conversations by link or ID.

## Contents

1. Ticket card
2. Verdict rules
3. Inbox Review report
4. Quick answer
5. Ticket Deep-Dive
6. Writing the report well

## 1. Ticket card

Write one right after each deep read and work from cards afterwards. Keep it compact: a card replaces a thread that may be fifty messages long. With a working folder, append cards to `inbox-coach/<date>/cards.jsonl`.

```json
{
  "id": "215470001",
  "url": "https://app.intercom.com/a/inbox/abc123/inbox/conversation/215470001",
  "inbox": "mine",
  "customer": "Marta",
  "language": "it",
  "state": "open",
  "tags": ["reason:billing-double-charge"],
  "tier": "T1",
  "ball": "us",
  "ask": "Refund of the second charge for the Pro annual plan.",
  "status": "Wrote three times in three days. Only the automated reply so far.",
  "promises": "None yet.",
  "pending": "Issue the refund and confirm the timeline.",
  "human_dimension": "frustrated",
  "effort": "quick_win",
  "verdict": "needs_nudge",
  "verdict_detail": "Refund is within policy. Nothing blocks the reply.",
  "next_step": "Refund the second charge and reply with the 5 to 7 business day timeline.",
  "risk": "Bank dispute and a public review, likely within a day.",
  "confidence": "high"
}
```

Field values:

- `ball`: `us`, `customer`, `internal:<team>`, `external:<who>`
- `human_dimension`: `none`, `frustrated`, `repeat_contact`, `our_mistake`, `delicate_no`, `escalation_threat`, `long_silence`, `customer_wrong`, `unresponsive`, `internal_coordination`, `high_value`
- `effort`: `quick_win`, `needs_evaluation`, `batchable`, `park`
- `verdict`: `on_track`, `needs_nudge`, `needs_help`, `blocked`
- `confidence`: `high`, `medium`, `low`. Add the reason when it is not high, for example "thread references a call I cannot see".
- `promises`: anything a teammate told the customer would happen, with the date. Promises are what a handoff most often drops, so capture them every time.

## 2. Verdict rules

Every ticket the teammate owns gets exactly one verdict. Decide in this order and stop at the first that fits.

1. **Blocked.** Progress depends on an event outside the support team's control that has not happened yet: a bug fix release, a legal or rights review, a payment provider, a customer who has been asked repeatedly and has not answered. Give the blocker, what would unblock it, when to check again, and what to tell the customer meanwhile. A blocked ticket with a silent customer is two problems; say both.
2. **Needs help (from whom).** The teammate cannot finish alone but someone reachable can move it: a policy decision, an approval, knowledge they lack, a tier escalation, another team's input. Name the role or team from the escalation map in the config and write the specific ask, ready to send.
3. **Needs a nudge.** The ball is with the teammate and they can move it alone, now: a reply that is due, a follow-up whose date arrived, a snooze that expired, a promise coming due, a customer gone quiet who deserves one more try or a graceful close.
4. **On track.** The ball is where it should be, nothing is at risk within the thresholds, and the next step and its date are known.

Low confidence does not change the verdict. It changes the next step into "open the conversation and confirm X".

Effort class (`quick_win`, `needs_evaluation`, `batchable`, `park`) is a separate dimension, defined in `workspace-config.md` section 7 and in the problem-solving lens. A ticket can need a nudge and be a quick win; it can need help and need evaluation.

## 3. Inbox Review report

Lead with the answer. Keep sections short, and drop any section that has nothing to say.

```markdown
# Inbox Review: <first name> · <date and time, time zone>

## Bottom line
<Governing thought: two or three sentences that answer the problem question. The "so what", never a list of counts.>

1. <Key line 1>
2. <Key line 2>
3. <Key line 3>

## Coverage
<Inboxes included and their size class. What was counted, enumerated and read in full. Sampling method when used. Approximate numbers and config DEFAULTs the conclusions rest on.>

## The numbers
<From the metrics script: totals by inbox and state, who has the ball, at risk and breached, stale, snoozes overdue, reopens, top tags and tiers. A small table or a few lines.>

## Where the difficulty is
<Issue tree as an indented list, each branch with its count and two or three example tickets. One or two sentences on which branches hold most of the pain and why.>

## Do now: quick wins
| Ticket | Customer | What | Why it is quick | Next step |
|---|---|---|---|---|

## Needs evaluation
| Ticket | Customer | What is unclear | What to find out | Who can help |
|---|---|---|---|---|

## Solve once: batches
<Groups of near-identical tickets, the single action that resolves them, and the upstream fix worth raising.>

## Your tickets: verdicts
| Ticket | Customer | Verdict | Detail | Next step | Risk if nothing happens |
|---|---|---|---|---|---|

## The human side
<For the few tickets where it matters most: point of view, Carnegie diagnosis with principles, two or three paths with trade-offs and drafts, and a question to decide. For other human-dimension tickets, one line each: principle and move.>

## Assumptions and blind spots
<Key Assumptions Check and Quality of Information Check in a few bullets. The high-impact, low-probability ticket, if there is one.>

## Watch next
<Two to four signposts for the next shift that would confirm or overturn this picture.>

## Questions for you
<Two or three coaching questions.>
```

For a team inbox reviewed at portfolio level, replace "Your tickets: verdicts" with "Tickets to flag", listing conversations that need their owner's or a lead's attention, with the reason.

## 4. Quick answer

When they only asked what to do first:

```markdown
**Start with these five:**
1. <Customer> · <one-line what> · <why now> · <link>
...
<One sentence on what can wait and why.>
Want the full review?
```

## 5. Ticket Deep-Dive

```markdown
# <Customer> · <short topic> · <link>

**Where it stands:** <ask, status, promises, pending, in three or four sentences>
**Verdict:** <verdict> · <detail>
**Next step:** <specific action>
**Risk:** <what happens if nothing happens, and by when>

## Thinking it through
<Only when the knot is analytical: problem question, small tree, the assumption to verify.>

## The human side
<Only when there is one: point of view, diagnosis, paths with drafts, question to decide.>
```

## 6. Writing the report well

- Every number comes from the script output or a tool response. If you did not compute it, do not state it.
- Link every ticket you mention. A recommendation the teammate cannot click is friction.
- Next steps are imperative and specific. "Reply with the refund confirmation and the bank timeline", never "follow up".
- Separate what you read from what you infer: "the thread shows" versus "this suggests".
- Long inbox, short report. Twenty lines they act on beat two hundred they skim. Offer depth on request.
- Tables for tickets, prose for thinking. Do not turn the bottom line into bullets.
- No blame. A review that makes a teammate feel audited will not be asked for twice. Describe the state of the tickets, never the quality of the person.
