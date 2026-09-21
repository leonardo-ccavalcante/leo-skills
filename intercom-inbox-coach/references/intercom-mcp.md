# Working with the Intercom MCP

Written against Intercom's official MCP server as documented in September 2026 (14 tools, US and EU regions). Servers change. The live tool descriptions in your environment outrank this file, and the Setup probe records what actually worked in `workspace-config.md` section 3. Check there first and copy the syntax that is known to work.

## Contents

1. Tools and what they are for here
2. What the MCP cannot do
3. Query recipes
4. Pagination and cheap counting
5. Reading strategy by inbox size
6. Record schema for the metrics script
7. Fields worth knowing in a conversation
8. Degraded mode without code execution
9. Internal notes
10. Being a good citizen

## 1. Tools and what they are for here

| Tool | Use in this skill |
|---|---|
| `search` | Query DSL over conversations and contacts. Light results (id, title, text, url). Best for counting and for slicing large inboxes. Must include `object_type:conversations`. |
| `search_conversations` | Structured filters: `state`, `admin_assignee_id` (number), `team_assignee_id` (string), `source_type`, author fields, `statistics_*` timing filters with operators. Returns conversation objects with basic details. Best for enumerating an inbox. |
| `get_conversation` | One full conversation with all parts and metadata. The deep read. Expensive in context, so use within the caps below. |
| `fetch` | Full details for an ID returned by `search` (`conversation_*`, `contact_*`, `company_*`), with a link to the Intercom app. |
| `get_contact`, `get_company`, `list_companies` | Customer context when it changes the decision (plan, company, high-value marker). Skip otherwise; it is personal data you do not need. |
| `search_articles`, `get_article` | Check whether a help article already answers the ticket before drafting a reply, and link it. |
| `add_internal_note` | The only write this skill performs, under the rules in section 9. |
| `create_article`, `update_article` | Not used by this skill. If a review reveals a missing article, recommend it in the report. |

Tool names may carry a prefix in your environment, and some surfaces load connector tools lazily, so search for them by base name if they are not visible.

## 2. What the MCP cannot do

No replies to customers, no assigning, closing, snoozing, tagging or prioritizing. No listing of admins, teams or views. No saved views at all.

Consequences:

- The teammate performs every action in Intercom. Your output has to be ready to act on: a specific next step, a draft to paste, a link to click.
- Teammate and team IDs come from the config. For someone missing from the roster, take the ID from a pasted inbox URL (`/inbox/admin/<id>`, `/inbox/team/<id>`) or from `admin_assignee_id` on a conversation assigned to them.
- A view is rebuilt as a query from its definition.

## 3. Query recipes

The `search` DSL follows `field:value` for equality and `field:operator:value` otherwise (`gt`, `lt`, `neq`, `contains`, and others), plus `limit:` and `starting_after:`. Field names in the DSL are flattened (for example `source_body`, `admin_assignee_id`). The tool validates names and operators and returns specific errors, so when a field is rejected, read the error, adjust and retry once or twice. Do not loop.

```
# The teammate's inbox
object_type:conversations admin_assignee_id:<admin_id> state:open limit:150
object_type:conversations admin_assignee_id:<admin_id> state:snoozed limit:150

# A team inbox
object_type:conversations team_assignee_id:<team_id> state:open limit:150

# Closed within the lookback window (date syntax: use what Setup recorded)
object_type:conversations admin_assignee_id:<admin_id> state:closed updated_at:gt:<epoch_of_now_minus_lookback> limit:150

# Slices for large inboxes
object_type:conversations team_assignee_id:<team_id> state:open created_at:lt:<epoch_30_days_ago> limit:1
object_type:conversations team_assignee_id:<team_id> state:open source_body:contains:"refund" limit:20
```

The same filters exist as structured parameters on `search_conversations` (`state`, `admin_assignee_id`, `team_assignee_id`, `per_page`, `starting_after`, and `statistics_time_to_admin_reply` style filters with `<`, `>`, `=`). Prefer it when you need the conversation objects and not just IDs and titles.

Epoch values for date bounds must come from code, never from mental arithmetic:

```bash
python3 -c "import time; print(int(time.time()) - 7*86400)"
```

If no date filter works for closed conversations, look at the sort order of the first page. If results come newest first, page until you pass the lookback boundary and stop. If the order is not useful, cap at two pages and say so in the coverage statement.

## 4. Pagination and cheap counting

- `search`, `search_conversations` and `search_contacts` use cursor pagination: repeat the same query with `starting_after:<cursor>` from `pages.next` (or from the `_note` hint) until no next page is reported. Pages hold up to 150 items and default to 5, so always set the limit explicitly.
- **Cheap counting.** The response includes `pages.total_pages` and `per_page`. Run the query with the smallest limit the tool accepts (try `limit:1`) and read `total_pages`: with a page size of 1 it is the count; otherwise the count lies between `(total_pages - 1) * per_page + 1` and `total_pages * per_page`. One tiny call sizes an inbox or a slice without pulling it into context. This is what makes a 3,000-conversation inbox workable. Confirm at Setup that `total_pages` is returned; if it is not, size by paging `search` with the lightest results and count as you go, within reason.

## 5. Reading strategy by inbox size

First size the inbox with the cheap count (open plus snoozed). Then choose the class. Caps come from config section 8.

| Class | Open + snoozed | Enumerate | Deep-read |
|---|---|---|---|
| S | up to 40 | everything | everything |
| M | 41 to 300 | everything (one or two pages of 150) | the attention ranking's top entries plus a small spread across tags, up to the cap |
| L | 301 to 1,000 | the slices that matter, not the whole inbox | a stratified sample, up to the cap |
| XL | over 1,000 | nothing wholesale; count by slices | a stratified sample, up to the cap |

**S and M: enumerate, measure, then read.** Pull all conversations as records, run the metrics script, and let the attention ranking choose the deep reads. In M, add a few conversations from each of the largest tag groups so the picture is not only the worst cases.

**L and XL: size by slices, then sample on purpose.** Never try to page through thousands of conversations; the context fills up long before the inbox ends, and the analysis gets worse, not better.

1. Count slices with cheap counting: by state; by age of creation (under 1 day, 1 to 7 days, 7 to 30 days, over 30 days); by the top tags or tiers from the config; priority; anything the config marks as high-value. These counts alone already describe the shape of the backlog.
2. Pull records only for the slices where action lives: the oldest waiting, priority, SLA at risk, recently reopened, and the largest tag groups (first page of each is enough).
3. Deep-read a stratified sample: most of the cap goes to the worst cases from step 2, the rest is spread across the biggest tag groups, plus three or four random picks from the middle of the inbox as a reality check on your own selection.
4. State the coverage in the report: what was counted, what was enumerated, what was read, and what kind of problem this sampling could miss.

**With subagents** (Cowork): give each subagent one inbox or slice, the record and card schemas, and this instruction: return only the records file path, the ticket cards, the slice counts and anything surprising. Keep the main context for analysis. Without subagents, work through slices one after another and keep the caps tight.

**Closed conversations in the lookback:** in S and M, enumerate them. In L and XL, count them, then pull only the reopened ones and the ones with poor ratings.

**Mixed requests:** when the teammate's own inbox is S and they add an XL team inbox, keep both depths. Their tickets get full reads and verdicts; the team inbox gets the sliced, sampled, portfolio-level treatment.

## 6. Record schema for the metrics script

One JSON object per line in `records.jsonl`. Only `id` is required; include every field the list result gives you and omit what you do not have. Copy timestamps exactly as returned (epoch seconds, or ISO strings if that is what you get). Never pre-convert them.

```json
{"id": "215470001", "inbox": "mine", "state": "open", "created_at": 1789830000, "updated_at": 1789912800, "waiting_since": 1789912800, "snoozed_until": null, "last_close_at": null, "admin_assignee_id": 5551001, "team_assignee_id": "7770001", "tags": ["reason:billing-double-charge", "priority:high"], "tier": "T1", "priority": true, "count_reopens": 0, "last_author_type": "customer", "sla_status": "active", "rating": null, "first_name": "Marta", "title": "Charged twice for Pro", "url": "https://app.intercom.com/a/inbox/abc123/inbox/conversation/215470001"}
```

Notes:

- `inbox` is your label: `mine` or the team inbox name from the config. Metrics are broken down by it.
- `waiting_since` matters. Intercom sets it when the customer starts waiting and clears it when a teammate replies. Include the key with `null` when Intercom says null (the ball is with the customer). Leave the key out only when the field was not returned at all; then the script falls back to `last_author_type`.
- `last_author_type` is who wrote the last customer-visible part: `customer`, `admin` or `bot`. Notes and assignment events do not count.
- `tier` comes from the tags or attributes as mapped in the config.
- `first_name` only. No surnames, emails or phone numbers in this file.
- The script also accepts raw Intercom shapes (`tags.tags[].name`, `statistics.count_reopens`, `sla_applied.sla_status`, `conversation_rating.rating`, `priority: "priority"`), a JSON array, or an object with a `conversations` list.

Run it:

```bash
python3 scripts/inbox_metrics.py records.jsonl --tz Europe/Rome --risk-hours 24 --breach-hours 48 --stale-days 5 --customer-silent-days 5 --lookback-days 7 --top 25
```

Add `--format json --out metrics.json` to keep a machine-readable copy, and `--now <epoch or ISO>` to pin the clock (self-tests, or re-running yesterday's data).

## 7. Fields worth knowing in a conversation

| Field | Why it matters |
|---|---|
| `state`, `open`, `snoozed_until` | Where the conversation sits. A snooze in the past means it should already have woken up. |
| `waiting_since` | When the customer started waiting for us. The basis of at-risk and breach. |
| `created_at`, `updated_at` | Age and staleness. |
| `statistics.count_reopens`, `statistics.last_close_at` | Reopens signal a resolution that did not hold. |
| `statistics.time_to_admin_reply` and similar | First response and handling times, already computed by Intercom. |
| `tags.tags[].name`, `custom_attributes` | The team's taxonomy: cause, reason, priority, tier. |
| `priority` | Marked as priority in the inbox. |
| `sla_applied.sla_name`, `sla_applied.sla_status` | `active`, `hit`, `missed` or `cancelled`. |
| `conversation_rating.rating`, `.remark` | Customer satisfaction, and their words about it. |
| `ai_agent_participated`, `ai_agent.*` | Whether the AI agent handled part of it and how that ended. A handover from the AI agent often means the customer has already repeated themselves once. |
| `conversation_parts` | The thread. Part types distinguish comments, notes, assignments, snoozes and closes. Notes are internal and often hold the context a colleague left. |
| `source` | Channel, subject and the customer's first message. |

## 8. Degraded mode without code execution

When no code can run:

- Counts are safe. Count records and use cheap counting.
- Ordering is safe. A larger epoch is later, so comparing `waiting_since` values as plain integers ranks who has waited longest without converting anything.
- Durations are not safe. Do not turn epochs into dates or hours by hand. If the tool returns human-readable times, use those. Otherwise use coarse, clearly relative language ("among the longest waiting in this inbox") and ask the teammate to confirm the few durations that drive a decision by opening the conversation.
- Put one line in the coverage section: "Metrics approximate: no code execution on this surface."
- Suggest switching code execution on if the surface allows it.

## 9. Internal notes

`add_internal_note` takes a `conversation_id` (numeric ID, `conversation_<id>`, or an inbox URL) and a `body` in HTML or plain text.

- **Format.** Whitespace between block-level tags renders as empty paragraphs, so write the HTML as one line with no newlines or indentation between tags: `<p><b>HANDOFF</b> · 21 Sep · Ana to Luca</p><p><b>Next step:</b> ...</p>`.
- **Authorship.** The note is signed by the Intercom user who authorized the MCP connection, not by whoever is chatting. Before the first note of a session, tell the teammate whose name it will appear under.
- **Snoozed conversations.** A note on a conversation that is snoozed and assigned to someone other than the authorizing user wakes it up. The response shows `part_type: note_and_unsnooze` when that happened. Skip those by default. If the teammate insists, warn them first and report every conversation that reopened.
- **Tickets.** Only regular conversations accept notes this way. Intercom Tickets return an authorization error, so carry their handoff in the Slack message and email instead.
- **Permissions.** A 401 usually means the connection predates the write permission. The fix is to disconnect and reconnect the Intercom connector.
- **Confirmation.** Show every note exactly as it will be posted, in one batch. The teammate approves all, some or none, and may edit. Post only what was approved, then report what succeeded, what failed and what reopened.
- **Content.** A note is permanent and visible to the whole team. Facts, status and next steps. No speculation about the customer's character, no personal data beyond what the conversation already shows.

## 10. Being a good citizen

Intercom's API rate limits apply through the MCP. Make calls one after another, set limits explicitly, avoid re-fetching a conversation you already carded, and stop paging once you have what the analysis needs. If a call fails, retry once, then carry on and mention the gap in coverage.
