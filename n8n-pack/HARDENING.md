# Hardening guide — running this pack in company environments

Operational security guidance for teams letting an AI coding agent drive an n8n instance. (Vulnerability reports → [`SECURITY.md`](./SECURITY.md).)

## 1. The API key is a root credential

On non-Enterprise n8n plans, API keys are **all-or-nothing**: a holder can create *and activate* a workflow that uses any stored credential. Scoped API keys are an Enterprise feature. Therefore:

- **Set an expiration** when creating the key — the one control available on every plan.
- Store it only in a gitignored `.env` (or a secrets manager in CI). Never in committed files, including `.mcp.json` — use the source-`.env` launcher shown in the README.
- **Never print the key.** Not `echo $N8N_API_KEY`, not `curl -v`/`--trace` (both print the auth header — and 401 debugging is exactly when you'll be tempted). Verify keys with status-code-only checks:
  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_API_URL/api/v1/workflows?limit=1"
  ```
- **Agent transcripts persist terminal output** in plaintext outside your repo (e.g. Claude Code under `~/.claude/`), beyond `.gitignore`'s reach. The rule is therefore absolute: never display credentials at all; inspect configs via commands that redact.
- Rotation runbook (401s): create a new key in n8n UI → Settings → n8n API, update `N8N_API_KEY`, restart your MCP client (it caches the key at launch). Rotate on a schedule and immediately on any suspected exposure.
- Give the MCP server a **dedicated key** so it can be revoked independently, and pin the server version (supply chain — see README).

## 2. Access control, per plan tier

- **Enterprise**: scoped API keys, custom roles, Project Viewer — use them; give agents the narrowest project scope.
- **Pro/Cloud**: project roles exist — put agent-managed workflows in a dedicated project.
- **Community**: no RBAC. The fallback is architectural: separate instances (dev/staging/prod), with the agent's key only on non-prod, and human-gated deploys to prod.
- Staging-first: let agents build and test on a non-production instance; promote exported JSON after review.

## 3. Backup-before-mutate

Ship-with-the-pack practice: before any agent mutation of a production workflow, dump live state:

```bash
mkdir -p backups
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" "$N8N_API_URL/api/v1/workflows/<id>" \
  > "backups/<id>-$(date -u +%Y%m%dT%H%M%SZ).json"
```

Enforce it mechanically with [`hooks/pre-tool-prod-guard.sh`](./hooks/pre-tool-prod-guard.sh) (`N8N_PROTECTED_WORKFLOW_IDS`). **Backups are full exports**: any secret hardcoded in a node parameter (instead of the credential store) is in the file, and execution exports contain full payload data. Keep `backups/` and `execution*.json` out of git — the shipped `.gitignore` entries do this.

## 4. Execution data is a data store

Saved executions persist **full node I/O**: chat messages, PII, tool responses, any `$env` value interpolated into a parameter. Choose `saveDataSuccessExecution` / `saveDataErrorExecution` / `saveExecutionProgress` deliberately per workflow, prune retention, and treat execution dumps shared in issues or chat as secret-bearing.

## 5. AI-agent workflows

The pack's skills carry the specific rails inline; the principles:

- **Prompt injection is a design problem, not a prompt problem.** Anyone who can message your bot controls the agent's input. Minimum tool set; no open-ended HTTP-fetch tool on the same agent as write tools; hardcode identity and destructive parameters; fail-closed output gates before sends.
- **`$fromAI` values are untrusted input** — model-generated from user-controlled context. Constrain via tool schema or a validating `toolWorkflow` wrapper.
- **Injection persists**: chat memory replays past messages; records written by tools re-enter prompts via lookups. Memory contents and lookup results are data, never instructions.
- **Formula injection**: model-filled spreadsheet values starting `=` `+` `-` `@` can execute on open — escape/strip, and check your Sheets node's cell-format option.
- **Bound the loop**: always set the agent's `maxIterations`.
- **Secrets never enter agent context**: not in `systemMessage` (extractable by chat users), not via `$env` interpolation (persists into execution data). Credential store only.

## 6. Data residency

Know where your data goes: your n8n instance region, the model provider behind every AI node (and its retention terms), and any sheet/CRM the agent writes. For fully local processing, see the pack's `n8n-self-hosted` skill (Ollama + Qdrant — no data leaves the machine).

## 7. Webhooks

Every taught intake pattern requires auth: header-auth credential or HMAC signature verification, payload validation before any DB write, and rate limiting / IP allowlisting where the platform offers it. An unauthenticated webhook URL is an unauthenticated write path to your database.
