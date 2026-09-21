# Setup: installing the skill in a workspace

Setup runs once per workspace, ideally with the team lead, and again whenever something changes (a new teammate, a new inbox, new tiers). It takes about 20 minutes. The goal is a completed `workspace-config.md` baked into a `.skill` package that every teammate installs, so nobody has to answer these questions again.

Conduct Setup in the installer's language. Write the config in English.

Tell the installer up front what will happen: a quick check of the environment, a read-only check of the Intercom connection, a few questions about inboxes, tiers and thresholds, a test run on real conversations, and a packaged skill at the end. Nothing is written to Intercom during Setup unless they explicitly ask to test one internal note.

If the config already says `CONFIGURED`, this is an update. Show the current values, ask what changed, touch only that, raise `config_version`, and bake again.

## Contents

1. Probe the environment
2. Probe the Intercom MCP
3. Discover the people and the inboxes
4. Capture tiers, effort criteria and thresholds
5. Capture taxonomy, escalation map and handoff preferences
6. Smoke test on real data
7. Optional synthetic dry run
8. Bake and distribute

## 1. Probe the environment

Find out what this surface can do and record it in config section 2. The team uses the skill in more than one place (Claude Desktop / Cowork and claude.ai in the cloud), so ask which surfaces they plan to use and, if possible, repeat this step in each.

- **Code execution.** Try `python3 scripts/inbox_metrics.py --self-test` from the skill folder. `SELF-TEST PASS` means exact metrics are available. If there is no way to run code, record that and tell the installer plainly what it means: counts and orderings still work, durations become approximate and will be labeled as such. If code execution is a setting they can switch on, recommend switching it on for everyone who will use the skill.
- **Files.** Can you write a file, and will it still be there in a later session? Cowork with a working folder usually says yes; claude.ai usually keeps files only within a conversation. This decides whether Handoff can reuse the morning's review or re-reads from scratch.
- **Subagents.** If you can spawn them, large inboxes can be read in parallel slices without flooding the main context.
- **Slack and email connectors.** If present, Handoff can offer to create drafts. Sending still needs an explicit yes every time.

## 2. Probe the Intercom MCP

Read-only. Record results in config section 3.

1. List the Intercom tools available and their exact names here. Note any tool beyond the official set (`search`, `fetch`, `search_conversations`, `get_conversation`, `search_contacts`, `get_contact`, `list_companies`, `get_company`, `list_articles`, `search_articles`, `get_article`, `create_article`, `update_article`, `add_internal_note`). A tool that lists admins or teams would make step 3 trivial, so use it if it exists.
2. Read the descriptions of `search` and `search_conversations` carefully. They list supported fields and operators and they outrank anything written in this skill.
3. Run `object_type:conversations state:open limit:5`. Confirm results come back. Check whether the response carries `pages.total_pages`, because cheap counting depends on it. Try `limit:1` to learn the smallest page size.
4. Test the filters the daily workflow needs, one small query each: by `admin_assignee_id`, by `team_assignee_id`, by `state:snoozed` and `state:closed`, by a date bound on `updated_at` or `created_at` (pattern `field:operator:value`, for example `updated_at:gt:<epoch>`), by tag, by priority. The search tool validates field names and answers with specific errors, so let the errors teach you the syntax. Record what worked, literally, so daily runs can copy it.
5. Look at the order results come back in (newest first or not) and which fields a list result already includes: state, timestamps, `waiting_since`, assignee IDs, tags, statistics. Every field present in list results is a `get_conversation` call saved later.
6. Fetch one conversation and note the URL format and region. Fill in the link pattern in config section 1.
7. Check that `add_internal_note` exists. Do not call it. If the installer wants to verify write access, ask them to name one conversation of their own, show the exact note text, get a yes, and post that single note. A 401 means the connection predates the write permission: disconnect and reconnect the Intercom connector.

Remind the installer that every teammate must connect the Intercom connector with their own Intercom login. The MCP inherits that person's permissions, and notes are signed by whoever authorized the connection.

## 3. Discover the people and the inboxes

The official MCP has no tool that lists teammates, teams or views, so combine two sources.

**Fast path: URLs.** Ask the installer to open each inbox they care about in Intercom and paste the URLs. A teammate inbox URL ends in `/inbox/admin/<admin_id>`, a team inbox in `/inbox/team/<team_id>`, and the code after `/a/inbox/` is the workspace app ID. This is the most reliable source for team names, which conversation data does not carry.

**Discovery path: read the data.** Pull a few pages of recent conversations (open first, then recently closed) and tally the distinct `admin_assignee_id` and `team_assignee_id` values with how many conversations each holds. Admin names come for free: `get_conversation` returns conversation parts whose authors include the admin's ID and name, so a handful of reads names most of the roster. Team IDs arrive without names, so show each one with its volume and two example conversation titles and ask the installer what they call it.

Then, with the installer:

- Confirm the roster: first name, admin ID, role, time zone if different from the team's, preferred language with the coach.
- For each team inbox: name, team ID, what lands there, and its size. Get the size with the cheap count from `references/intercom-mcp.md` and assign the size class (S up to 40 open, M up to 300, L up to 1,000, XL beyond).
- Ask which inboxes to offer by default when a teammate is asked "any other inboxes?".
- Ask about the views people rely on and rebuild each as a query. Test the query and compare the count with what the installer sees in Intercom.

## 4. Capture tiers, effort criteria and thresholds

The team lead provides the tier list. Ask for it directly and capture it in their words: each tier's definition, how to recognize it in a conversation (tags, attributes, signals), who resolves it, and whether it can be a quick win. If they have a document, ask them to paste the relevant part rather than retyping it.

Then walk through config sections 7 and 8. Read out each DEFAULT and ask whether it matches how the team works: the quick-win test, the needs-evaluation triggers, and the time thresholds (at risk, breach, stale, customer silent, lookback). Where service levels differ by tier or inbox, record the overrides. Where the team has not decided yet, keep the DEFAULT and leave it marked, so reports can say which conclusions rest on a placeholder.

## 5. Capture taxonomy, escalation map and handoff preferences

- **Taxonomy (section 9).** Conversations arrive already tagged. Look at the tags on the conversations you have read and ask the installer to explain the scheme: which prefix or attribute carries cause, reason, priority, tier, and how high-value customers are marked.
- **Escalation map (section 10).** For each kind of help, who it goes to, how to ask, and the usual turnaround. This is what turns "needs help" into a specific ask.
- **Handoff (section 11).** Slack channel, email recipients or alias, the shift pattern, and the note header convention.

## 6. Smoke test on real data

This is the test that matters, because it uses the team's real conversations. No notes are posted.

1. **Small inbox, end to end.** Pick the installer's own inbox or the smallest team inbox and run the full Inbox Review. Show the report and ask three things: are the verdicts right, are the quick wins really quick, and do the reply drafts sound like the team? Record every correction as a calibration note in config section 12, phrased as a rule the skill can follow next time.
2. **Large inbox, sizing only.** Pick the biggest inbox and run just the sizing and sampling steps. Confirm that counting by slices works, that the context stays manageable, and that the coverage statement is honest. Adjust the deep-read caps if needed.
3. **Handoff dry run.** Produce the Slack message, the email and the note previews for the installer's inbox. Post nothing. Ask whether a colleague could pick up from this cold.
4. Compare two or three script numbers with what Intercom shows for the same inbox (open count, oldest waiting conversation). A mismatch usually means a filter or field behaves differently from what the probe assumed. Fix the recipe in config section 3.

## 7. Optional synthetic dry run

`assets/sample_inbox.json` holds twelve fictitious conversations that cover the usual situations: a double charge, a sync bug waiting on engineering, a takedown request with legal weight, a customer who stopped answering, a delicate refund refusal, a duplicate, a misrouted sales question, a reopened ticket with a bad rating. Use it to demo the skill to the team, to train a new teammate, or to check behavior after editing the skill, all without touching real customer data. Run the metrics with `--self-test`, or point the script at the file and do a full review from its `parts`.

## 8. Bake and distribute

1. Write the completed config to a file, set `status: CONFIGURED`, fill in `configured_by` and `configured_on`, and raise `config_version`.
2. Show the installer the whole config and get their confirmation. It contains names and internal IDs, so they should know exactly what will be shared with the team.
3. Run `python3 scripts/bake_config.py --config <completed-config.md>`. It copies the skill, swaps in the config, checks the package and writes `intercom-inbox-coach.skill`.
4. Present the file. The installer installs it in place of the unconfigured copy and shares it with the team the way their organization distributes skills.
5. If baking is not possible on this surface (no code execution), hand over the completed config as a file and explain the two ways forward: bake it on a surface that can run code, or paste the config at the start of a session so the skill can work in session-only mode.

Finish by telling the installer how the team starts using it: "review my inbox", "help me with this conversation", "write my handoff".
