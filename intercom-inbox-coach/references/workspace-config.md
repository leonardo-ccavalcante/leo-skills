# Workspace config

status: NOT_CONFIGURED
configured_by:
configured_on:
config_version: 0

This file is the memory of the skill for one Intercom workspace. It ships empty. `references/setup.md` fills it in, and `scripts/bake_config.py` writes the completed copy into a fresh `.skill` package so the whole team gets the same configuration.

Anything still marked `DEFAULT` is a working assumption of the skill, not a team decision. Say so when a conclusion leans on it.

## 1. Workspace

| Field | Value |
|---|---|
| Workspace name | |
| Intercom region | (US: app.intercom.com / EU: app.eu.intercom.com) |
| Workspace app ID | (the code after `/a/inbox/` in any inbox URL) |
| Conversation link pattern | (copy one real conversation URL and replace the ID with `{id}`) |
| Team time zone | (IANA name, for example `Europe/Rome`) |
| Working languages with customers | |

## 2. Environment capabilities

Recorded by the Setup probe, per surface where the team runs the skill. The skill reads this to choose between the exact path and the degraded path.

| Surface | Code execution | Files persist between sessions | Subagents | Slack connector | Email connector |
|---|---|---|---|---|---|
| Claude Desktop / Cowork | | | | | |
| claude.ai (cloud) | | | | | |

## 3. MCP capabilities

Recorded by the Setup probe so daily runs do not rediscover them.

| Check | Result |
|---|---|
| Intercom tool names as exposed here | |
| `search` returns `pages.total_pages` (cheap counting works) | |
| Smallest `limit` accepted by `search` | |
| Date filter syntax that worked (for example `updated_at:gt:<epoch>`) | |
| Tag filter syntax that worked | |
| Priority / SLA filters that worked | |
| Default sort order of results | |
| Fields present in list results (without `get_conversation`) | |
| `add_internal_note` available and authorized | |
| Extra tools beyond the official 14 (for example list admins or teams) | |

## 4. Roster

Who uses the skill. The admin ID is what `admin_assignee_id` filters on. Each teammate connects the Intercom connector with their own Intercom login, because internal notes are attributed to whoever authorized the connection.

| First name | Intercom admin ID | Role | Time zone (if different) | Preferred language with the coach |
|---|---|---|---|---|
| | | | | |

## 5. Team inboxes

| Inbox name | Team ID | What lands there | Typical open volume | Size class (S/M/L/XL) | Offer by default? |
|---|---|---|---|---|---|
| | | | | | |

Views the team uses, rebuilt as queries (views themselves are not readable through the MCP):

| View name | Equivalent query |
|---|---|
| | |

## 6. Tiers

Provided by the team lead during Setup. Tiers drive who resolves a ticket and whether it can be a quick win.

| Tier | Definition | How to recognize it (tags, attributes, signals) | Who resolves | Quick-win eligible? |
|---|---|---|---|---|
| | | | | |

## 7. Effort criteria

DEFAULT until the team lead replaces them.

- **Quick win:** the policy or macro is clear, nothing depends on anyone else, it takes under 15 minutes, and being wrong is cheap.
- **Needs evaluation:** depends on engineering, product, legal, rights or billing; policy is ambiguous or missing; high-value customer; part of a recurring pattern; legal, security or reputation risk; conflicting information.
- **Batchable:** several near-identical tickets that one decision, macro or fix would resolve together.
- **Park:** nothing useful to do until a known date or event. A snooze and a customer expectation must both be set.

Team overrides:

## 8. Time thresholds

Passed to `scripts/inbox_metrics.py` as flags. DEFAULT values shown.

| Threshold | Value | Flag |
|---|---|---|
| Customer waiting on us: at risk after | 24 hours | `--risk-hours` |
| Customer waiting on us: breach after | 48 hours | `--breach-hours` |
| Open with no update: stale after | 5 days | `--stale-days` |
| Waiting on customer: follow-up or close after | 5 days | `--customer-silent-days` |
| Closed-conversation lookback | 7 days | `--lookback-days` |
| Deep-read cap per session (no subagents) | 30 conversations | |
| Deep-read cap per session (with subagents) | 80 conversations | |

Per-tier or per-inbox overrides:

## 9. Taxonomy in Intercom

Conversations arrive already tagged by the team's tagging pipeline. Record here how that shows up so the skill groups by it instead of inventing categories.

| Dimension | Where it lives (tag prefix, attribute name) | Example values |
|---|---|---|
| Cause | | |
| Reason | | |
| Priority | | |
| Tier | | |
| High-value or VIP marker | | |

## 10. Escalation map

Who helps with what. Roles are enough; names are optional.

| Kind of help | Goes to | How to ask (channel, ticket type) | Usual turnaround |
|---|---|---|---|
| Bug or outage | | | |
| Product decision or missing feature | | | |
| Rights, legal, takedown | | | |
| Billing or payment provider | | | |
| Policy exception or refund approval | | | |
| Security or account takeover | | | |

## 11. Handoff preferences

| Field | Value |
|---|---|
| Slack channel(s) for handoffs | |
| Email recipients or alias | |
| Shift pattern (who usually follows whom) | |
| Internal note header convention | `HANDOFF · <date> · <from> to <to>` (DEFAULT) |
| Post internal notes by default? | Offer every time, post only after approval (fixed rule) |

## 12. Calibration notes

What the smoke test and the team's feedback taught the skill. Short, dated, specific. Examples: "Refund tickets under 14 days are always quick wins", "The Labels inbox is mostly rights questions, never sample fewer than 15", "Drafts for Italian customers should use the formal Lei".

-
