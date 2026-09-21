# Handoff

A handoff lets a colleague continue the teammate's work tomorrow morning with zero context and without having to ask anything. It runs on its own at the end of a shift, often in a fresh conversation hours after any review, so it never depends on earlier analysis. It reuses that analysis when it is available.

All handoff artifacts are in English. Talk with the teammate in their own language while preparing them.

## Contents

1. Workflow
2. The handoff entry
3. Writing rules
4. Slack message
5. Email
6. Internal notes
7. Delivering and posting

## 1. Workflow

1. **Orient** as in SKILL.md Step 0: Intercom tools, config, who the teammate is.
2. **Ask two things, together:** who takes over (a named colleague, or "next shift"), and whether anything is on their mind that Intercom will not show (a call they had, a verbal promise, a worry about a ticket). What lives only in their head is the most valuable part of a handoff.
3. **Reuse or re-read.** If a review from today is in this conversation or saved under `inbox-coach/<date>/`, reuse its cards, then re-check the state of each ticket, because things moved since the morning. Otherwise read from scratch:
   - open and snoozed conversations assigned to the teammate, read in full up to the deep-read cap, ordered by the metrics script's attention ranking
   - conversations they closed today, as records only, for the "resolved today" line
   - beyond the cap, give the remaining tickets a one-line entry from their metadata and say that they were not read in full
4. **Write one entry per ticket** (section 2) and order them: act first thing, then due during the shift, then on track and parked.
5. **Produce the three artifacts:** Slack message, email, internal note previews.
6. **Review with the teammate.** They correct, add what only they know, and approve.
7. **Deliver and post** (section 7).

Team inboxes are not handed off ticket by ticket. If the teammate was watching one, add a short "inbox watch" paragraph: volume, anything unusual, anything at risk.

## 2. The handoff entry

| Field | Content |
|---|---|
| Ticket | Link, customer first name, short topic, main tag or tier |
| State | Open or snoozed (until when), who has the ball, verdict |
| Done so far | What has happened, in one or two sentences. Facts only. |
| Promised | Anything the customer was told would happen, with the date. Never omit a promise. |
| Pending | What is missing to resolve it |
| Next step | One imperative sentence the colleague can act on without asking anything. Include the draft or the macro name when there is one. |
| Due / risk | When it must happen and what goes wrong if it does not |
| Who can help | Role or team, and whether they have already been contacted (link to the internal ticket if one exists) |
| Tone tip | Only when the human side matters: one line from the Carnegie lens. "Marco felt ignored for three days. Use his name, own the delay, keep it short." |

## 3. Writing rules

- **Write for someone with zero context at 8 am.** No "as discussed", no "the usual issue", no abbreviations the newest teammate would not know.
- **A next step is an action.** "Check whether the refund posted. If yes, close with the confirmation macro. If not, escalate to Billing with the transaction ID from the note." Never "monitor".
- **Facts and guesses apart.** "Engineering confirmed the bug" is a fact. "Probably fixed in Thursday's release" is a guess and should read like one.
- **Promises first.** The colleague inherits the team's word. A broken promise they did not know about is the worst outcome a handoff can produce.
- **Short.** The colleague reads this while their own inbox fills up. Urgent entries get full detail, on-track entries get one line.
- **Minimal personal data.** First names and links. The conversation holds the rest.
- **It is a request to a colleague,** and the Carnegie principles apply to it as much as to customers: ask instead of ordering (25), make each step easy (29), show trust in their judgment (9), and thank them honestly and briefly (2). No flattery and no guilt.

## 4. Slack message

Compact enough to read in a channel. Details go in a thread reply or in the email. For copy and paste use plain URLs; the `<url|text>` link form only works when a message is sent through the Slack API or a connector.

```
*Handoff · <date> · <from> to <to / next shift>*
Open <n> · Snoozed <n> · Resolved today <n>

*Act first thing*
• <Customer> · <topic> · <next step in one line> · due <when>
  <url>
• ...

*During the shift*
• <Customer> · <topic> · <next step> · <when>
  <url>

*On track / parked* (<n>): nothing needed unless they reply. Notes are in each conversation.

*Heads-up:* <the one thing to know: a pattern, a risky ticket, a pending answer from another team>

Thanks, <name>. <One honest, specific line.>
```

Details in thread, one block per urgent ticket:

```
*<Customer> · <topic>*
Done: <...>
Promised: <... by date>
Pending: <...>
Next: <...>
Help: <who / internal ticket link>
Tone: <one line, if relevant>
```

## 5. Email

```
Subject: Handoff <date> · <from> to <to> · <n> to act on first

Hi <name>,

<Two sentences: the overall state and the single most important thing.>

ACT FIRST THING
1. <Customer> · <topic>
   Link: <url>
   Done so far: <...>
   Promised: <...>
   Pending: <...>
   Next step: <...>
   Due / risk: <...>
   Who can help: <...>
   Tone tip: <...>

DURING THE SHIFT
<same structure, shorter>

ON TRACK / PARKED
- <Customer> · <topic> · <state, and when it wakes or what is awaited> · <url>

RESOLVED TODAY
<count, and anything that might reopen>

INBOX WATCH
<only if relevant>

Thank you, <one honest line>.
<from>
```

## 6. Internal notes

One note per conversation that needs action or carries a promise. Skip conversations that are on track with nothing to add; a note that says nothing is noise for everyone who opens the ticket later.

HTML on a single line, with no whitespace between block tags (it renders as blank paragraphs otherwise):

```html
<p><b>HANDOFF</b> · 21 Sep 2026 · Ana to next shift</p><p><b>State:</b> Open, ball with us. Customer has waited 3 days.</p><p><b>Done so far:</b> Second charge confirmed in billing.</p><p><b>Promised:</b> Nothing yet.</p><p><b>Next step:</b> Refund the second charge and reply with the 5 to 7 business day timeline.</p><p><b>Risk:</b> Customer mentioned a bank dispute.</p><p><b>Tone:</b> Use his name, own the delay, keep it short.</p>
```

Use the header convention from the config if the team has one. Rules that matter (full detail in `references/intercom-mcp.md` section 9):

- The note appears under the Intercom user who authorized the connector. Say whose name that is before posting the first note of the session.
- A note on a conversation that is snoozed and assigned to someone else wakes it up. The teammate's own snoozed conversations are fine. Skip the others unless they insist, and warn them first.
- Intercom Tickets do not accept notes through the MCP. Carry those in the Slack message and the email.
- Notes are permanent and visible to the whole team. Facts, state and next steps only.

## 7. Delivering and posting

1. Show the Slack message and the email in full, ready to copy. If a Slack or email connector is available, offer to create a draft. Sending needs an explicit yes, naming the channel or recipient, every time.
2. Show all note previews in one batch as a numbered list: ticket, customer, and the exact text as it will be posted. Ask which to post: all, some by number, or none. Accept edits.
3. Post only the approved notes, one at a time. Afterwards report in a small table which were posted, which failed and why, and whether any conversation reopened (`part_type: note_and_unsnooze`).
4. If there is a working folder, save the handoff as `inbox-coach/<date>/handoff.md`.
5. Close with what the MCP cannot do for them: reassigning conversations to the colleague is theirs to do in Intercom. List the conversations to reassign so it takes one pass.
