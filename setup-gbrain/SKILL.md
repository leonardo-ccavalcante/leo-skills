---
name: setup-gbrain
description: |
  Install gbrain (a persistent knowledge base for coding agents — github.com/garrytan/gbrain)
  on this Mac, initialize a local PGLite or Supabase brain, register it as a Claude Code MCP
  server, and capture per-remote trust policy. One command from zero to "gbrain is running
  and this agent can call it." This is the gstack-specific setup — gstack users only. Use
  this skill whenever the user says "setup gbrain", "install gbrain", "connect gbrain", "start
  gbrain", "configure gbrain for this machine", or "wire up the brain". Triggers on
  /setup-gbrain. Proactively invoke when the user mentions gbrain CLI not being on PATH.
---

# Set up gbrain for this coding agent

You are setting up [gbrain](https://github.com/garrytan/gbrain), a persistent knowledge
base, on the user's local Mac so this coding agent (typically Claude Code) can call it as
both a CLI and an MCP tool.

**Scope honesty:** the MCP registration step uses `claude mcp add` and targets Claude Code
specifically. Other local hosts (Cursor, Codex CLI, etc.) get the gbrain CLI on PATH but
must register `gbrain serve` in their own MCP config manually.

**Audience:** local-Mac gstack users. Cloud agents (openclaw, hermes) typically run in cloud
docker containers with their own gbrain — sharing a brain between them and local Claude Code
is only possible through a shared Postgres (Supabase).

## Invocation modes

- `/setup-gbrain` — full flow (default)
- `/setup-gbrain --repo` — only flip per-remote policy for the current repo
- `/setup-gbrain --switch` — only migrate the engine (PGLite ↔ Supabase)
- `/setup-gbrain --resume-provision <ref>` — re-enter an interrupted Supabase auto-provision
- `/setup-gbrain --cleanup-orphans` — list and delete in-flight Supabase projects

Parse args yourself — they are prose hints to this skill, not a dispatcher binary.

## Step 1: Detect current state

Check whether gbrain is on PATH, what engine it uses, and whether the local config and DB
are healthy.

```bash
# Probe gbrain
GBRAIN_ON_PATH=$(command -v gbrain >/dev/null 2>&1 && echo true || echo false)
GBRAIN_VERSION=$(gbrain --version 2>/dev/null | awk '{print $2}' || echo "")
GBRAIN_CONFIG_EXISTS=$([ -f "$HOME/.gbrain/config.json" ] && echo true || echo false)
GBRAIN_ENGINE=""
if [ "$GBRAIN_CONFIG_EXISTS" = "true" ]; then
  GBRAIN_ENGINE=$(jq -r '.engine // empty' "$HOME/.gbrain/config.json" 2>/dev/null)
fi
GBRAIN_DOCTOR_OK=$(gbrain doctor --json 2>/dev/null | jq -r '.status' 2>/dev/null || echo "fail")

# Detect MCP mode (remote-http vs local-stdio)
GBRAIN_MCP_MODE="none"
if [ -f "$HOME/.claude.json" ] && command -v jq >/dev/null 2>&1; then
  TYPE=$(jq -r '.mcpServers.gbrain.type // .mcpServers.gbrain.transport // empty' "$HOME/.claude.json" 2>/dev/null)
  case "$TYPE" in
    url|http|sse) GBRAIN_MCP_MODE="remote-http" ;;
    stdio) GBRAIN_MCP_MODE="local-stdio" ;;
  esac
fi

echo "GBRAIN_ON_PATH=$GBRAIN_ON_PATH"
echo "GBRAIN_VERSION=$GBRAIN_VERSION"
echo "GBRAIN_CONFIG_EXISTS=$GBRAIN_CONFIG_EXISTS"
echo "GBRAIN_ENGINE=$GBRAIN_ENGINE"
echo "GBRAIN_DOCTOR_OK=$GBRAIN_DOCTOR_OK"
echo "GBRAIN_MCP_MODE=$GBRAIN_MCP_MODE"
```

Skip downstream steps that are already done. Report in one line:

> "Detected: gbrain v0.18.2 on PATH, engine=postgres, doctor=ok. Nothing to install; jumping
> to the policy check."

Branch on `--repo`, `--switch`, `--resume-provision`, `--cleanup-orphans` flags here.

## Step 1.5: Broken-engine remediation

If the local engine config exists but doctor fails (broken-db or broken-config) AND no
shortcut flag was passed, ask before continuing:

> Your local gbrain engine isn't responding. How do you want to fix it?
>
> A) Retry — re-probe the engine (recommended; ~80ms; preserves state)
> B) Switch to local PGLite (one-way — moves existing config to .bak)
> C) Switch brain mode (continue to Step 2 path picker)
> D) Quit (do nothing)

**If A**: re-run the Step 1 detection. If still broken, ask again.

**If B**: rollback-safe init:

```bash
BACKUP="$HOME/.gbrain/config.json.bak-$(date +%s)"
mv "$HOME/.gbrain/config.json" "$BACKUP"
if ! gbrain init --pglite --json; then
  mv "$BACKUP" "$HOME/.gbrain/config.json"
  echo "gbrain init failed. Previous config restored at $HOME/.gbrain/config.json." >&2
  echo "PGLite directory at ~/.gbrain/pglite/ may be partial — \`rm -rf ~/.gbrain/pglite\` if needed before retrying." >&2
  exit 1
fi
echo "Switched to local PGLite. Previous config saved at $BACKUP — review before deleting."
```

Then jump to Step 5a (MCP registration).

**If C**: continue to Step 2.

**If D**: STOP cleanly.

## Step 2: Pick a path

Only fire if Step 1 shows no working config AND no shortcut flag was passed. Special case:
if `GBRAIN_MCP_MODE=remote-http`, an HTTP MCP is already registered — skip to Step 5a
verification and onward.

Ask: "Where should your brain live?"

- **1 — Supabase, I already have a connection string.** For users whose cloud agent
  provisioned one. Paste the Session Pooler URL from the Supabase dashboard (Settings →
  Database → Connection Pooler → Session). **Trust-surface caveat:** "Pasting this URL gives
  your local Claude Code full read/write access to every page your cloud agent can see. If
  that's not the trust level you want, pick PGLite local and accept the brains are disjoint."
- **2a — Supabase, auto-provision a new project.** Needs a Supabase Personal Access Token
  (~90s). Best for a shared team brain.
- **2b — Supabase, create manually.** Walk through supabase.com signup yourself; paste the
  URL back.
- **3 — PGLite local.** Zero accounts, ~30s. Isolated brain on this Mac only. Best for
  try-first.
- **4 — Remote gbrain MCP.** Someone else (or another machine of yours) is running
  `gbrain serve` with HTTP transport. Paste the MCP URL + a bearer token; this skill
  registers it as your MCP. No local brain DB, no local install needed. Best when the brain
  is shared across machines or run by a teammate.
- **Switch** (only if Step 1 detected an existing engine): "You already have a `<engine>`
  brain. Migrate it to the other engine?" → runs `gbrain migrate --to <other>` with a 180s
  timeout.

Do not silently pick — actually ask the user.

## Step 3: Install gbrain CLI (if missing)

**SKIP entirely on Path 4 (Remote MCP).** Path 4 doesn't need a local gbrain binary — all
calls go through MCP to the remote server. Jump to Step 4.

For Paths 1, 2a, 2b, 3, switch — only if `GBRAIN_ON_PATH=false`:

```bash
# Detect a local source checkout first; otherwise install from npm
GBRAIN_SRC=""
[ -d "$HOME/git/gbrain" ] && GBRAIN_SRC="$HOME/git/gbrain"
[ -z "$GBRAIN_SRC" ] && [ -d "$HOME/gbrain" ] && GBRAIN_SRC="$HOME/gbrain"

if [ -n "$GBRAIN_SRC" ]; then
  cd "$GBRAIN_SRC" && pnpm install && pnpm build && pnpm link --global
else
  pnpm add -g gbrain
fi

# Validate the install — gbrain --version must match the installed package
gbrain --version
```

If the post-install `gbrain --version` doesn't match the package version, the PATH is
shadowed by a stale install — surface the error and STOP.

## Step 4: Initialize the brain

Path-specific.

### Path 1 (Supabase, existing URL)

Collect the URL securely (don't echo, redact in logs):

```bash
read -s -p "Paste Session Pooler URL: " GBRAIN_POOLER_URL
echo ""
# Validate it's a pooler URL (port 6543), not a direct connection (port 5432)
if echo "$GBRAIN_POOLER_URL" | grep -qE ':5432/'; then
  echo "ERROR: that's a direct connection URL. You need the Session Pooler URL (port 6543)." >&2
  echo "Get it from Supabase dashboard → Settings → Database → Connection Pooler → Session." >&2
  exit 1
fi

GBRAIN_DATABASE_URL="$GBRAIN_POOLER_URL" gbrain init --non-interactive --json
unset GBRAIN_POOLER_URL GBRAIN_DATABASE_URL
```

The URL is now persisted in `~/.gbrain/config.json` at mode 0600 by gbrain itself.

### Path 2a (Supabase, auto-provision)

Show this disclosure verbatim BEFORE collecting the token:

> *This Supabase Personal Access Token grants full read/write/delete access to every project
> in your Supabase account, not just the `gbrain` one we're about to create. Supabase doesn't
> currently support scoped tokens. We use this PAT only to: create one project, poll it until
> healthy, read the Session Pooler URL — then discard it from process memory. The token
> remains valid on Supabase's side until you manually revoke it at
> https://supabase.com/dashboard/account/tokens — we recommend revoking immediately after
> setup completes.*

Then:

```bash
read -s -p "Paste PAT: " SUPABASE_ACCESS_TOKEN
echo ""
```

Ask for tier (Free vs Pro), org (list via API), and region (default `us-east-1`).

Generate a DB password (never shown):

```bash
export DB_PASS=$(openssl rand -base64 24)
```

Set up a SIGINT trap so Ctrl-C reports the in-flight project ref:

```bash
trap 'echo ""; echo "Interrupted. In-flight ref: $INFLIGHT_REF"; \
      echo "Resume: /setup-gbrain --resume-provision $INFLIGHT_REF"; \
      echo "Delete: https://supabase.com/dashboard/project/$INFLIGHT_REF"; \
      unset SUPABASE_ACCESS_TOKEN DB_PASS; exit 130' INT TERM
```

Create the Supabase project via the Management API, poll until healthy, fetch the pooler URL,
init gbrain with that URL, then clean up:

```bash
# Use the Supabase Management API directly:
# - POST /v1/projects to create
# - GET /v1/projects/{ref}/health to poll
# - GET /v1/projects/{ref}/config/database/pooler for the URL
# Capture INFLIGHT_REF before the wait loop so the trap can recover.
# Then: GBRAIN_DATABASE_URL="$pooler_url" gbrain init --non-interactive --json
unset SUPABASE_ACCESS_TOKEN DB_PASS GBRAIN_DATABASE_URL INFLIGHT_REF
trap - INT TERM
```

After success, remind the user to revoke the PAT.

### Path 2b (Supabase, manual)

Walk through supabase.com:
1. Login at https://supabase.com/dashboard
2. New Project → name `gbrain`, pick region
3. Wait ~2 min for the project to initialize
4. Settings → Database → Connection Pooler → Session → copy URL (port 6543)

Then follow Path 1's collect + init flow.

### Path 3 (PGLite local)

```bash
gbrain init --pglite --json
```

Done. No network, no secrets.

### Path 4 (Remote gbrain MCP — HTTP + bearer token)

For users whose brain runs on another machine (Tailscale, ngrok, internal LAN, teammate's
server). No local gbrain CLI install, no local DB.

**4a. Collect MCP URL.** Prompt for it; require `https://` for non-localhost hosts.

**4b. Collect bearer token.**

```bash
read -s -p "Paste bearer token: " GBRAIN_MCP_TOKEN
echo ""
```

**4c. Verify.** Hit the MCP server's `/tools/list` endpoint with the bearer to confirm the
URL is reachable, the token works, and the server is on a compatible MCP version. On
failure, surface a one-line remediation and STOP — do NOT continue to Step 5a on a failed
verify.

Capture two values for later:
- `SERVER_VERSION` (e.g., `0.27.1`) — written to CLAUDE.md in Step 8.
- `URL_FORM_SUPPORTED` (`true|false`) — controls Step 7's brain-admin hookup command.

**4d. Optionally install local PGLite for code-symbol queries.** Ask:

> Want symbol-aware code search on this machine?
>
> The remote brain at `<MCP_URL>` is great for cross-machine knowledge, but symbol queries
> (`gbrain code-def`, `code-refs`, `code-callers`) need a local index of THIS machine's
> code. We can spin up an isolated PGLite database (~30s, no accounts, ~120 MB disk) just
> for code, separate from your remote brain.
>
> A) Yes, set up local PGLite for code (recommended)
> B) No, remote MCP only — symbol queries fall back to Grep

**If A**: install gbrain (Step 3) + `gbrain init --pglite --json` with rollback-safe
backup. **If B**: skip — `/sync-gbrain` will skip the code stage cleanly.

Continue to Step 5a with `GBRAIN_MCP_TOKEN` still in env.

### Switch (between engines)

```bash
# PGLite → Supabase: collect URL first, then:
timeout 180s gbrain migrate --to supabase --url "$URL" --json
# Supabase → PGLite:
timeout 180s gbrain migrate --to pglite --json
```

If timeout exits 124: "Migration didn't complete in 3 minutes. Another session may hold a
lock on the source brain. Close other workspaces and re-run `/setup-gbrain --switch`. Your
original brain is untouched." STOP.

## Step 5: Verify gbrain doctor

**SKIP entirely on Path 4** — the brain host runs its own doctor; Step 4c already verified
the server is reachable.

For Paths 1, 2a, 2b, 3:

```bash
doctor=$(gbrain doctor --json)
status=$(echo "$doctor" | jq -r .status)
```

If `ok` or `warnings`, proceed. Anything else → surface the full output and STOP.

## Step 5a: Register gbrain as Claude Code MCP

Only if `which claude` resolves. Ask: "Give Claude Code a typed tool surface for gbrain?
(recommended yes)"

### Path 4 (Remote MCP)

Tear down any prior registration, then register HTTP + bearer at user scope:

```bash
claude mcp remove gbrain -s user 2>/dev/null || true
claude mcp remove gbrain 2>/dev/null || true
claude mcp add --scope user --transport http gbrain "$MCP_URL" \
  --header "Authorization: Bearer $GBRAIN_MCP_TOKEN"
unset GBRAIN_MCP_TOKEN
claude mcp list | grep gbrain  # verify: should show "Connected"
```

**Token-storage note:** `claude mcp add --header "Authorization: Bearer ..."` puts the
bearer on argv briefly visible to `ps` for ~10ms. The token's resting state is
`~/.claude.json` at mode 0600.

### Paths 1, 2a, 2b, 3 (Local stdio)

Register at **user scope** with an **absolute path** to the gbrain binary:

```bash
GBRAIN_BIN=$(command -v gbrain)
claude mcp remove gbrain -s user 2>/dev/null || true
claude mcp remove gbrain 2>/dev/null || true
claude mcp add --scope user gbrain -- "$GBRAIN_BIN" serve
claude mcp list | grep gbrain
```

**Heads-up:** an already-open Claude Code session won't see the new MCP tools until
restart. Tell the user: "Restart any open Claude Code sessions to see `mcp__gbrain__*`
tools — they load at session start, not mid-session."

If `claude` isn't on PATH: "MCP registration skipped — this skill is Claude-Code-targeted;
register `gbrain serve` in your agent's MCP config manually." Continue to step 6.

## Step 6: Per-remote trust policy

If we're in a git repo with an `origin` remote, set the policy for that remote:

- `read-write` → import this repo: `gbrain import "$(pwd)" --no-embed` then
  `gbrain embed --stale &` in the background
- `read-only` → skip import (the agent can search but never write)
- `deny` → no interaction at all
- `unset` → ask the user which tier, then persist

For `/setup-gbrain --repo`, execute ONLY this step and exit.

## Step 7: Offer artifacts sync

Ask: "Sync your project artifacts (plans, designs, reports, retros) to a private git repo
that gbrain can index across machines?"

- Yes, full sync (everything allowlisted)
- Yes, artifacts-only (plans, designs, retros — skip behavioral data)
- No thanks

If yes, the artifacts-init helper creates a private repo (via `gh` or `glab`) named
`gstack-artifacts-$USER` and writes the canonical HTTPS URL to
`~/.gstack-artifacts-remote.txt`.

The helper always prints a "Send this to your brain admin" block at the end with the exact
`gbrain sources add` command. The skill never auto-executes server-side gbrain commands —
even if the user IS the brain admin, copy-pasting the printed command is the consistent UX.

For Paths 1, 2a, 2b, 3, also wire the artifacts repo into local gbrain so its content is
searchable from any gbrain client. This creates a `git worktree`, registers it as a
federated source via `gbrain sources add --path --federated`, and runs an initial
`gbrain sync`.

## Step 7.5: Transcript ingest (Local stdio only)

**SKIP on Path 4** — remote-mode users rely on the brain server's ingest cadence.

For Paths 1, 2a, 2b, 3: offer to ingest this Mac's coding-agent transcripts so the
retrieval surface has data. Default scope is **current repo only, last 90 days**. Show
counts and ask:

- A) Yes — this repo, last 90 days (recommended)
- B) Yes — this repo, ALL history
- C) Yes — this repo + other repos on this machine
- D) Skip historical, track new from now (`incremental`)
- E) Never ingest transcripts (`off`)

## Step 8: Persist GBrain Configuration in CLAUDE.md

Find-and-replace (or append) the section. The block format depends on mode.

### Path 4 (Remote MCP)

```markdown
## GBrain Configuration

- Mode: remote-http
- MCP URL: {MCP_URL}
- Server version: gbrain v{SERVER_VERSION}
- Setup date: {today}
- MCP registered: yes (user scope)
- Token: stored in ~/.claude.json (do not commit; never written here)
- Artifacts repo: {URL or "none"}
- Artifacts sync: {off|artifacts-only|full}
- Current repo policy: {read-write|read-only|deny|unset}
```

The bearer token is **never** written to CLAUDE.md — CLAUDE.md is often checked into git.

### Paths 1, 2a, 2b, 3 (Local stdio)

```markdown
## GBrain Configuration

- Mode: local-stdio
- Engine: {pglite|postgres}
- Config file: ~/.gbrain/config.json (mode 0600)
- Setup date: {today}
- MCP registered: {yes/no}
- Artifacts sync: {off|artifacts-only|full}
- Current repo policy: {read-write|read-only|deny|unset}
```

After Step 9 passes, also append a search-guidance block so the coding agent learns when to
prefer `gbrain` over Grep:

```markdown
## GBrain Search Guidance

GBrain is set up and synced. Prefer gbrain over Grep when the question is semantic or you
don't know the exact identifier yet.

Prefer gbrain when:
- "Where is X handled?" / semantic intent: `gbrain search "<terms>"` or `gbrain query "<question>"`
- "Where is symbol Y defined?": `gbrain code-def <symbol>` / `gbrain code-refs <symbol>`
- "What calls Y?": `gbrain code-callers <symbol>` / `gbrain code-callees <symbol>`
- "What did we decide last time?": `gbrain search "<terms>" --source gstack-brain-<user>`

Grep is still right for known exact strings, regex, multiline patterns, and file globs. Run
`/sync-gbrain` to force-refresh, `/sync-gbrain --full` for full reindex.
```

## Step 9: Smoke test

### Path 4 (Remote MCP)

The `mcp__gbrain__*` tools aren't visible mid-session. Print the curl-equivalent the user
can run after restarting Claude Code, with `<YOUR_TOKEN>` as a placeholder (don't print the
actual token).

### Paths 1, 2a, 2b, 3 (Local stdio)

```bash
SLUG="setup-gbrain-smoke-test-$(date +%s)"
echo "Set up on $(date). Smoke test for /setup-gbrain." | gbrain put "$SLUG"
gbrain search "smoke test" | grep -i "$SLUG"
```

Confirms the round trip. On failure, surface `gbrain doctor --json` and STOP with a
NEEDS_CONTEXT escalation.

## Step 10: GREEN/YELLOW/RED verdict

Summarize. Re-running `/setup-gbrain` on a configured Mac is a first-class doctor path —
every step detects existing state, repairs only what's missing, and reports here.

### Path 4 verdict

```
gbrain status: GREEN  (mode: remote-http)

  MCP ............. OK   {SERVER_NAME} v{SERVER_VERSION} at {MCP_URL}
  Auth ............ OK   bearer accepted
  Engine .......... N/A  remote mode
  Doctor .......... N/A  remote mode
  Repo policy ..... OK   {tier}
  Artifacts repo .. OK   {URL}
  Artifacts sync .. OK   {mode}
  Code search ..... {OK local-pglite | N/A declined at Step 4d}
  CLAUDE.md ....... OK
  Smoke test ...... INFO printed for post-restart manual verification

Restart Claude Code to pick up the `mcp__gbrain__*` tools.
```

### Local stdio verdict

```
gbrain status: GREEN  (mode: local-stdio)

  CLI ............. OK   {version}
  Engine .......... OK   {pglite|supabase}
  Doctor .......... OK
  MCP ............. OK   registered (user scope)
  Repo policy ..... OK   {tier}
  Code import ..... OK   {last_imported_head}
  Artifacts sync .. OK   {mode} to {remote}
  CLAUDE.md ....... OK
  Smoke test ...... OK   put → search round-trip

Re-run `/setup-gbrain` any time gbrain feels off — it's safe and idempotent.
```

If any row is YELLOW or RED, the verdict line says so and failing rows surface a one-line
"next action."

## `/setup-gbrain --cleanup-orphans`

Re-collect a PAT (with the Step 4 path-2a disclosure), list all Supabase projects whose
name starts with `gbrain`, identify orphans (their `ref` doesn't match the active
`~/.gbrain/config.json` pooler URL), and ask per-project before deleting. NEVER batch —
per-project confirm is a one-way door.

```bash
# List projects
projects=$(curl -s -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  https://api.supabase.com/v1/projects)

# Delete confirmed orphans one by one
curl -s -X DELETE -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  https://api.supabase.com/v1/projects/$REF
```

Never delete the active brain without a second explicit confirmation. At end:
`unset SUPABASE_ACCESS_TOKEN` and revocation reminder.

## Important rules

- **One rule for every secret.** PAT, DB_PASS, pooler URL: env-var only, never argv, never
  logged, never persisted to disk by this skill. The only file that holds the pooler URL
  long-term is `~/.gbrain/config.json`, written by gbrain's own `init` at mode 0600.
- **STOP points are hard.** Gbrain doctor not healthy, PATH shadow, migrate timeout, smoke
  test failure — each is a STOP. Do not paper over.
- **Concurrent-run lock.** At skill start, `mkdir ~/.setup-gbrain.lock.d` (atomic). If
  mkdir fails, abort with: "Another `/setup-gbrain` instance is running. Wait for it, or
  `rm -rf ~/.setup-gbrain.lock.d` if you're sure it's stale." Release on normal exit AND
  in the SIGINT trap.
- **CLAUDE.md is the audit trail.** Always update it in Step 8 after a successful setup.
- **pnpm preferred.** Install gbrain via pnpm (`pnpm add -g gbrain` or `pnpm link --global`
  in a local checkout), not npm or bun.
