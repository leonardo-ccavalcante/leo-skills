---
name: open-gstack-browser
description: |
  Launch an AI-controlled Chromium browser window where every action is visible in real time —
  navigation, clicks, form fills, snapshots — instead of running headless. Anti-bot stealth
  patches built in so sites like Google and NYTimes work without captchas. Use this skill
  whenever the user says "open gstack browser", "launch browser", "launch chromium", "connect
  chrome", "open chrome", "show me the browser", "real browser", "control my browser", or
  "side panel". Triggers on /open-gstack-browser. Proactively invoke when the user asks to
  watch Claude work in a real visible Chrome window or wants to demo browser automation.
---

# Launch GStack Browser

Launch an AI-controlled Chromium browser with a sidebar extension, anti-bot stealth, and a
live activity feed. Every command Claude runs shows up in the visible window in real time.

This is a workflow for projects that ship a `browse` binary (typically at
`.claude/skills/gstack/browse/dist/browse` or `~/.claude/skills/gstack/browse/dist/browse`).
Adapt the paths and commands to your own tool — the steps below describe the user-facing
workflow.

## Step 0: Pre-flight cleanup

Before connecting, kill any stale browse servers and clean up lock files that may have
persisted from a crash. This prevents "already connected" false positives and Chromium
profile lock conflicts.

```bash
# Resolve the browse binary path (project-local first, then home)
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
B=""
[ -n "$_ROOT" ] && [ -x "$_ROOT/.claude/skills/gstack/browse/dist/browse" ] && B="$_ROOT/.claude/skills/gstack/browse/dist/browse"
[ -z "$B" ] && B="$HOME/.claude/skills/gstack/browse/dist/browse"

# Kill any existing browse server
if [ -f "$_ROOT/.gstack/browse.json" ]; then
  _OLD_PID=$(cat "$_ROOT/.gstack/browse.json" 2>/dev/null | grep -o '"pid":[0-9]*' | grep -o '[0-9]*')
  [ -n "$_OLD_PID" ] && kill "$_OLD_PID" 2>/dev/null || true
  sleep 1
  [ -n "$_OLD_PID" ] && kill -9 "$_OLD_PID" 2>/dev/null || true
  rm -f "$_ROOT/.gstack/browse.json"
fi

# Clean Chromium profile locks (can persist after crashes)
_PROFILE_DIR="$HOME/.gstack/chromium-profile"
for _LF in SingletonLock SingletonSocket SingletonCookie; do
  rm -f "$_PROFILE_DIR/$_LF" 2>/dev/null || true
done
echo "Pre-flight cleanup done"
```

If the `browse` binary isn't built yet, run the setup script in the skill's source directory
(`cd <skill-dir> && ./setup`). If pnpm isn't installed, install it first — the build uses
pnpm to bundle the binary.

## Step 1: Connect

```bash
$B connect
```

This launches Chromium in headed mode with:
- A visible window you can watch (not your regular Chrome — your profile stays untouched)
- The sidebar extension auto-loaded via `launchPersistentContext`
- Anti-bot stealth patches (Google, NYTimes, captcha-protected sites work)
- A sidebar agent process for chat commands

The `connect` command always uses port **34567** so the extension can auto-connect.

After connecting, print the full output. Confirm you see `Mode: headed`. If the output shows
an error or the mode is not `headed`, run `$B status` and share the output before proceeding.

## Step 2: Verify

```bash
$B status
```

Confirm `Mode: headed`. Read the port from the state file (should be **34567**):

```bash
cat "$(git rev-parse --show-toplevel)/.gstack/browse.json" 2>/dev/null | grep -o '"port":[0-9]*' | grep -o '[0-9]*'
```

Find the extension path so the user can load it manually if needed:

```bash
_EXT_PATH=""
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
[ -n "$_ROOT" ] && [ -f "$_ROOT/.claude/skills/gstack/extension/manifest.json" ] && _EXT_PATH="$_ROOT/.claude/skills/gstack/extension"
[ -z "$_EXT_PATH" ] && [ -f "$HOME/.claude/skills/gstack/extension/manifest.json" ] && _EXT_PATH="$HOME/.claude/skills/gstack/extension"
echo "EXTENSION_PATH: ${_EXT_PATH:-NOT FOUND}"
```

## Step 3: Guide the user to the Side Panel

Tell the user:

> Chromium is launched with agent control. You should see Playwright's Chromium (not your
> regular Chrome) with a golden shimmer line at the top of the page.
>
> The Side Panel extension should be auto-loaded. To open it:
> 1. Look for the **puzzle piece icon** (Extensions) in the toolbar
> 2. Click the **puzzle piece** → find **gstack browse** → click the **pin icon**
> 3. Click the pinned icon in the toolbar
> 4. The Side Panel should open on the right showing a live activity feed
>
> **Port:** 34567 (auto-detected — the extension connects automatically).

If the extension isn't visible:

> 1. Type `chrome://extensions` in the address bar
> 2. Look for **"gstack browse"** — it should be listed and enabled
> 3. If it's there but not pinned, click the puzzle piece icon and pin it
> 4. If it's NOT listed, click **"Load unpacked"**, press **Cmd+Shift+G** in the file picker,
>    paste the EXTENSION_PATH from Step 2, click **Select**
> 5. If the badge stays gray (disconnected), click the icon and enter port **34567** manually

If something else went wrong:
1. Run `$B status` and show output
2. If unhealthy, re-run Step 0 cleanup + Step 1 connect
3. If healthy but the browser isn't visible, try `$B focus`
4. Otherwise, ask the user what they see (error message, blank screen, etc.)

## Step 4: Demo

After the user confirms the Side Panel is working, run a quick demo so they can watch
commands flow through the activity feed:

```bash
$B goto https://news.ycombinator.com
```

Wait 2 seconds, then:

```bash
$B snapshot -i
```

Tell the user: "Check the Side Panel — you should see the `goto` and `snapshot` commands
appear in the activity feed. Every command Claude runs shows up here in real time."

## Step 5: Sidebar chat

After the activity feed demo, mention the sidebar chat:

> The Side Panel has a **chat tab**. Try typing a message like "take a snapshot and describe
> this page." A sidebar agent (a child Claude instance) executes your request in the browser
> — you'll see commands appear in the activity feed as they happen.
>
> The sidebar agent can navigate pages, click buttons, fill forms, and read content. Each
> task gets up to 5 minutes. It runs in an isolated session, so it won't interfere with this
> Claude Code window.

## Step 6: What's next

Tell the user:

> You're all set. Here's what you can do:
>
> **Watch Claude work in real time:**
> - Run any browser-driving skill (`/qa`, `/design-review`, `/benchmark`) and watch every
>   action happen in the visible Chrome window + Side Panel feed
> - No cookie import needed — the Playwright browser shares its own session
>
> **Control the browser directly:**
> - **Sidebar chat** — type natural language in the Side Panel
> - **Browse commands:**
>   - `$B goto <url>`
>   - `$B click <selector>`
>   - `$B fill <selector> <value>`
>   - `$B snapshot -i`
>
> **Window management:**
> - `$B focus` — bring Chrome to the foreground
> - `$B disconnect` — close headed Chrome, return to headless mode

Then proceed with whatever the user originally asked. If they didn't specify a task, ask
what they'd like to test or browse.
