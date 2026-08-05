---
name: pair-agent
description: |
  Pair a remote AI agent with your browser so it can drive a real browser session
  through any browser-control tool (Playwright, Chrome DevTools Protocol, Puppeteer,
  a local HTTP browser-control server, or similar). Generates a short-lived setup
  key, prints copy-pasteable instructions the other agent can follow, and (optionally)
  opens an ngrok tunnel for remote agents. Each connected agent gets its own scoped
  tab with read+write access by default and admin only on request. Use this skill
  whenever the user says "pair agent", "connect agent", "share my browser", "remote
  browser access", "let another agent use my browser", "give browser access", "hook
  up [Codex|Cursor|another Claude] to my browser", or describes wanting a second AI
  to control or watch their browser. Also triggers on /pair-agent.
---

# Pair Agent — Share Your Browser With Another AI Agent

You're sitting in one AI coding session with a browser-control tool running locally. You also have another AI agent open (Codex, Cursor, a second Claude session, a custom agent, whatever). You want that other agent to drive YOUR browser. This skill makes that happen.

## How it works

Your local browser-control tool exposes an HTTP API (any of: Playwright server, Chrome DevTools Protocol over HTTP, a Puppeteer wrapper, or a dedicated browser-control server). This skill creates a one-time setup key, prints a block of instructions, and you paste those instructions into the other agent. The other agent exchanges the key for a session token, creates its own tab, and starts browsing. Each agent gets its own tab — they cannot mess with each other's tabs.

The setup key should expire in 5 minutes and be single-use. If it leaks, it's dead before anyone can abuse it. The session token should last 24 hours (configurable).

**Same machine:** If the other agent is on the same machine, you can skip the copy-paste ceremony and write the credentials directly to the agent's config directory.

**Remote:** If the other agent is on a different machine, you need a tunnel (ngrok is the default, but Cloudflare Tunnel or any reverse proxy works). The skill will tell you if one is needed and walk through setup.

## Prerequisites

Before running this skill the user needs:
- A local browser-control tool with an HTTP API endpoint (e.g., a Playwright server, Chrome DevTools Protocol, a custom browser-control server). Throughout this skill, references to `$B` mean the user's browser-control CLI/server entrypoint.
- The browser-control server running and reachable on a known port.
- Optionally, `ngrok` (or another tunneling tool) installed if pairing a remote agent.

## Step 1: Verify the local browser-control server is running

Replace `$B` below with the user's actual browser-control entrypoint. Check that the server is alive:

```bash
# Example: most browser-control tools expose a /status or /version endpoint
curl -sf http://localhost:<PORT>/status 2>/dev/null && echo "READY" || echo "NEEDS_START"
```

If `NEEDS_START`, tell the user how to start their browser-control server (this depends on their tool — Playwright `npx playwright run-server`, Chrome with `--remote-debugging-port=9222`, or their custom server's start command). Then re-check.

## Step 2: Ask what they want

Ask the user which agent they're pairing with. This determines the format of the instructions and (if local) where credentials get written.

Options:
- A) A second Claude Code session (local or remote)
- B) Codex / OpenAI Agents (local or remote)
- C) Cursor (local)
- D) A custom or other agent (generic HTTP instructions)

Set `TARGET_HOST` based on the answer:
- A → `claude`
- B → `codex`
- C → `cursor`
- D → `generic` (no host-specific config)

## Step 3: Local or remote?

Ask: is the other agent running on this same machine, or on a different machine/server?

- **Same machine** skips the copy-paste ceremony. Credentials are written directly to the agent's config directory. No tunnel needed.
- **Different machine** generates a setup key and instruction block. If a tunneling tool is installed, the tunnel starts automatically. If not, walk through setup.

**Recommendation:** Choose same-machine if the agent is local. It's instant, no copy-paste needed.

## Step 4: Execute pairing

### Path A — Same machine

Generate a session token and write it directly to the target agent's config directory. The exact path depends on the agent:

- Codex: `~/.codex/skills/<your-skill>/browse-remote.json`
- Cursor: `~/.cursor/skills/<your-skill>/browse-remote.json`
- Custom agent: a JSON file at the path the agent expects

The file should contain something like:

```json
{
  "endpoint": "http://localhost:<PORT>",
  "token": "<scoped-session-token>",
  "scope": ["read", "write"],
  "expires_at": "<iso-8601-timestamp>"
}
```

If the target agent doesn't have a known config path, fall back to the remote flow (Path B).

After writing, tell the user:
"Done. The target agent can now use your browser. It will read credentials from the config file just written. Try asking it to navigate to a URL."

If it fails (host not found, write permission error), show the error and suggest using the remote flow.

### Path B — Different machine

First detect tunnel tooling. ngrok is the most common; other options work too:

```bash
which ngrok 2>/dev/null && echo "NGROK_INSTALLED" || echo "NGROK_NOT_INSTALLED"
ngrok config check 2>/dev/null && echo "NGROK_AUTHED" || echo "NGROK_NOT_AUTHED"
```

**If ngrok is installed AND authed:** Start the tunnel and generate the instruction block:

```bash
ngrok http <PORT> --log=stdout > /tmp/ngrok.log &
sleep 2
TUNNEL_URL=$(curl -sf http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok[^"]*' | head -1)
echo "Tunnel: $TUNNEL_URL"
```

Then mint a scoped, time-limited setup key (5-minute TTL, single-use) in your browser-control server. The exact command depends on your tool — most have a CLI for this. The setup key is short, opaque, and can be exchanged for a 24-hour session token.

Print an instruction block the user can paste into the other agent. The block should include:
1. The tunnel URL.
2. The setup key.
3. A short curl one-liner the remote agent can run to exchange the key for a session token.
4. Examples of typical browser-control commands the agent can run (navigate, screenshot, click, fill).

**CRITICAL: Output the full instruction block to the user inside a markdown code block.** Do NOT summarize it, do NOT skip it, do NOT just say "here's the output." The user needs to SEE the block to copy-paste it into the other agent's chat. Wrap it in triple-backticks so the user can select and copy in one motion.

Then tell the user:
"Copy the block above and paste it into your other agent's chat. The setup key expires in 5 minutes."

If the user wants admin access (JS execution, cookies, storage), the setup key should be minted with admin scope. Warn the user: only do this for agents you fully trust.

**If ngrok is installed but NOT authed:** Walk the user through authentication:

1. Go to https://dashboard.ngrok.com/get-started/your-authtoken
2. Copy the auth token
3. Provide the token, then run:
   ```bash
   ngrok config add-authtoken THEIR_TOKEN
   ```

Then retry the tunnel + pairing flow.

**If ngrok is NOT installed:** Walk the user through installation:

1. Go to https://ngrok.com and sign up (free tier works)
2. Install:
   - macOS: `brew install ngrok`
   - Linux: `snap install ngrok` or download from ngrok.com/download
3. Auth: `ngrok config add-authtoken YOUR_TOKEN`
4. Re-run `/pair-agent`

(Alternative tunnels also work — Cloudflare Tunnel, Tailscale Funnel, etc. The protocol is the same: expose your local browser-control port at a public URL.)

## Step 5: Verify connection

After the user pastes the instructions into the other agent, wait a moment then check whether the remote agent has connected. The exact check depends on your browser-control tool — most expose a `/status` or `/tunnel/list` endpoint that shows active connections.

If the connected agent appears, tell the user:
"The remote agent is connected and has its own tab. You'll see its activity in your browser's tab list."

## What the remote agent can do

With default (read+write) access:
- Navigate to URLs, click elements, fill forms, take screenshots
- Read page content (text, HTML, snapshot)
- Create new tabs (each agent gets its own)
- Cannot execute arbitrary JavaScript, read cookies, or access storage

With admin access:
- Everything above, plus JS execution, cookie access, storage access
- Use sparingly. Only for agents you fully trust.

## Troubleshooting

**"Tab not owned by your agent"** — The remote agent tried to interact with a tab it didn't create. Tell it to create its own tab first.

**"Domain not allowed"** — The token has domain restrictions. Re-pair with broader domain access or no domain restrictions.

**"Rate limit exceeded"** — The agent is sending > 10 requests/second. It should wait for the Retry-After header and slow down.

**"Token expired"** — The 24-hour session expired. Run `/pair-agent` again to generate a new setup key.

**Agent can't reach the server** — If remote, check the tunnel is still running. If local, check the browser-control server is running.

## Revoking access

To disconnect a specific agent: invalidate that agent's scoped session token via your browser-control tool's revoke endpoint or CLI.

To disconnect ALL agents at once: rotate the root token in your browser-control server. This invalidates every scoped token immediately. This is the nuclear option — use it if you suspect a leaked key.
