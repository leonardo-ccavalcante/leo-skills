# n8n skills pack for Claude Code

Eight battle-tested Claude Code skills for building, validating, and debugging [n8n](https://n8n.io) workflows through MCP — plus the shared docs and an optional production-guard hook.

> **Unofficial.** This pack is not affiliated with or endorsed by n8n GmbH. "n8n" is used descriptively.

Every skill encodes *verified* lessons from real production workflows: validator false positives you must NOT "fix", API operations that report success while silently doing nothing, expression traps that break only at runtime, and AI-agent security rails. The knowledge here is the kind you normally pay for with an outage.

## The skills

| Skill | Load it when |
| --- | --- |
| `n8n-mcp-tools-expert` | Discovering nodes via MCP; "Node not found" errors; the two-prefix format trap |
| `n8n-workflow-patterns` | Designing workflow architecture; conversational AI, CRM sync, webhook intake patterns |
| `n8n-node-configuration` | Configuring node parameters; typeVersion migrations; partial-update operation shapes |
| `n8n-validation-expert` | Validation errors; known validator false positives; static-vs-runtime truth |
| `n8n-expression-syntax` | `={{ ... }}` expressions; `$json`/`$fromAI`/`$env`; IF/Switch condition rules |
| `n8n-code-javascript` | JavaScript Code nodes; I/O contract; offline testing; fail-closed gates |
| `n8n-code-python` | Python Code nodes; `_input`/`_('Node')` API |
| `n8n-self-hosted` | Self-hosting with the Docker Compose AI starter kit (Ollama, Qdrant) |

## Install

The skills are plain Claude Code skill folders. Copy the eight `n8n-*` directories into your skills path:

```bash
# per-user
cp -r n8n-* ~/.claude/skills/
# or per-project
cp -r n8n-* <your-repo>/.claude/skills/
```

Descriptions in each skill's frontmatter auto-trigger on the right keywords; no further wiring needed.

## MCP setup (what the skills drive)

The skills assume the n8n REST API and, optionally, one or both MCP servers:

1. **Environment** — copy `n8n-pack/.env.example` to a gitignored `.env`:
   - `N8N_API_URL` — e.g. `https://<your-instance>.app.n8n.cloud`
   - `N8N_API_KEY` — created in n8n UI → Settings → n8n API. **Treat it as a root credential** (see `HARDENING.md`) and set an expiration when creating it.
2. **Community MCP server** ([czlonkowski/n8n-mcp](https://github.com/czlonkowski/n8n-mcp), MIT) — richest discovery + surgical partial updates. **Pin a reviewed version** (`npx n8n-mcp@x.y.z`, not `-y` latest); it holds your API key. Launch it so it sources your `.env` rather than embedding the key in committed MCP config:
   ```json
   { "mcpServers": { "n8n-mcp": { "command": "sh",
     "args": ["-c", "set -a; . ./.env; set +a; exec npx n8n-mcp@<pinned>"] } } }
   ```
3. **Official n8n MCP server** (built into your instance) — enable in n8n → Settings → MCP, then add with your client's HTTP transport and the instance token. Good as an independent verifier/executor.
4. **No MCP at all?** Everything the skills describe has a `curl` equivalent against `/api/v1` with the `X-N8N-API-KEY` header.

## Shared docs

- [`LANDMINES.md`](./LANDMINES.md) — the canonical symptom → cause → workaround registry the skills reference.
- [`HARDENING.md`](./HARDENING.md) — company-environment guidance: key handling, plan-tier RBAC reality, execution-data retention, backups, AI-agent security.
- [`SECURITY.md`](./SECURITY.md) — how to report an issue in this pack.
- [`templates/CLAUDE.md.example`](./templates/CLAUDE.md.example) — a dispatch-layer template for wiring these skills into a project `CLAUDE.md`.
- [`hooks/pre-tool-prod-guard.sh`](./hooks/pre-tool-prod-guard.sh) — optional PreToolUse hook that blocks agent mutations of protected workflow IDs unless a fresh backup exists. Configure via `N8N_PROTECTED_WORKFLOW_IDS`.

## License

The pack (these eight skills and docs) is licensed under Apache-2.0 — see [`LICENSE`](./LICENSE) and [`NOTICE`](./NOTICE). `n8n-self-hosted` is adapted from the n8n self-hosted-ai-starter-kit README (© n8n GmbH, Apache-2.0). Node-schema knowledge was learned working with the MIT-licensed czlonkowski/n8n-mcp server.
