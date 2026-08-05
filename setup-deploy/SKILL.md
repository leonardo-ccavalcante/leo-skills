---
name: setup-deploy
description: |
  Detect this project's deployment platform (Fly.io, Render, Vercel, Netlify, Heroku, Railway,
  GitHub Actions, or custom), figure out the production URL, health check endpoint, and deploy
  status commands, then persist the configuration so future deploys are automatic. Use this
  skill whenever the user says "setup deploy", "configure deployment", "set deploy platform",
  "add deploy config", "how do I deploy this", or asks to wire up a deploy pipeline. Triggers
  on /setup-deploy. Proactively invoke when the user mentions deploying for the first time on
  a project that has no deploy config yet.
---

# Configure deployment for this project

Detect the deploy platform, production URL, health checks, and deploy status commands. Save
everything to a local config file so subsequent deploy workflows can read it instead of
asking again. This is a one-shot configuration skill — run once per project, re-run when
deploy infrastructure changes.

## Step 1: Check existing configuration

```bash
# Prefer a dedicated config file; fall back to a section in CLAUDE.md
if [ -f .deploy-config.json ]; then
  echo "EXISTING_CONFIG:"
  cat .deploy-config.json
elif grep -q "## Deploy Configuration" CLAUDE.md 2>/dev/null; then
  echo "EXISTING_CONFIG:"
  grep -A 20 "## Deploy Configuration" CLAUDE.md
else
  echo "NO_CONFIG"
fi
```

If configuration already exists, show it and ask the user:

- A) Reconfigure from scratch (overwrite existing)
- B) Edit specific fields (show current, change one thing)
- C) Done — configuration is correct

If C, stop. If B, ask which field to change and skip to Step 4. If A, continue.

## Step 2: Detect platform

Look for platform-specific config files. Each one is a strong signal.

```bash
# Platform config files
[ -f fly.toml ] && echo "PLATFORM:fly" && cat fly.toml
[ -f render.yaml ] && echo "PLATFORM:render" && cat render.yaml
{ [ -f vercel.json ] || [ -d .vercel ]; } && echo "PLATFORM:vercel"
[ -f netlify.toml ] && echo "PLATFORM:netlify" && cat netlify.toml
[ -f Procfile ] && echo "PLATFORM:heroku"
{ [ -f railway.json ] || [ -f railway.toml ]; } && echo "PLATFORM:railway"

# GitHub Actions deploy workflows
for f in $(find .github/workflows -maxdepth 1 \( -name '*.yml' -o -name '*.yaml' \) 2>/dev/null); do
  [ -f "$f" ] && grep -qiE "deploy|release|production|staging|cd" "$f" 2>/dev/null && echo "DEPLOY_WORKFLOW:$f"
done

# Project type — affects whether deploy applies at all
[ -f package.json ] && grep -q '"bin"' package.json 2>/dev/null && echo "PROJECT_TYPE:cli"
find . -maxdepth 1 -name '*.gemspec' 2>/dev/null | grep -q . && echo "PROJECT_TYPE:library"
```

## Step 3: Platform-specific setup

Based on what was detected, walk through platform-specific configuration. The goal is to
end up with: platform name, production URL, health check (URL or command), deploy status
command, and any pre/post-deploy hooks.

### Fly.io

If `fly.toml` detected:

1. Extract app name: `grep -m1 "^app" fly.toml | sed 's/app = "\(.*\)"/\1/'`
2. Check if `fly` CLI is installed: `which fly 2>/dev/null`
3. If installed, verify: `fly status --app {app} 2>/dev/null`
4. Infer URL: `https://{app}.fly.dev`
5. Set deploy status command: `fly status --app {app}`
6. Set health check: `https://{app}.fly.dev` (or `/health` if the app has one)

Ask the user to confirm — some Fly apps use custom domains.

### Render

If `render.yaml` detected:

1. Extract service name and type from `render.yaml`
2. Check for `RENDER_API_KEY` env var: `echo "${RENDER_API_KEY:0:4}"` (don't print the full key)
3. Infer URL: `https://{service-name}.onrender.com`
4. Render auto-deploys on push to the connected branch — no deploy workflow needed
5. Health check: poll the inferred URL after merge

Confirm with the user. The deploy wait should poll the Render URL until it responds with
the new version.

### Vercel

If `vercel.json` or `.vercel` detected:

1. Check for `vercel` CLI: `which vercel 2>/dev/null`
2. If installed: `vercel ls --prod 2>/dev/null | head -3`
3. Vercel auto-deploys on push — preview on PR, production on merge to main
4. Health check: production URL from `vercel project settings`

### Netlify

If `netlify.toml` detected:

1. Extract site info from `netlify.toml`
2. Netlify auto-deploys on push
3. Health check: production URL

### Heroku

If `Procfile` detected:

1. Check for `heroku` CLI: `which heroku 2>/dev/null`
2. Get app name from `.git/config` or ask the user
3. Deploy status command: `heroku ps -a {app}`
4. URL: `https://{app}.herokuapp.com` (or custom domain)

### Railway

If `railway.json` or `railway.toml` detected:

1. Check for `railway` CLI: `which railway 2>/dev/null`
2. URL: from `railway status` or ask the user
3. Deploy status: `railway status`

### GitHub Actions only

If deploy workflows detected but no platform config:

1. Read the workflow file to understand what it does
2. Extract the deploy target (if mentioned)
3. Ask the user for the production URL
4. Deploy status: check the workflow run via `gh run list --workflow={file} --limit 1`

### Custom / Manual

If nothing detected, ask the user:

1. **How are deploys triggered?**
   - A) Automatically on push to main (Fly, Render, Vercel, Netlify, etc.)
   - B) Via GitHub Actions workflow
   - C) Via a deploy script or CLI command (which one?)
   - D) Manually (SSH, dashboard, etc.)
   - E) This project doesn't deploy (library, CLI, internal tool)

2. **What's the production URL?** (Free text)

3. **How can we check if a deploy succeeded?**
   - A) HTTP health check at a specific URL (e.g., `/health`, `/api/status`)
   - B) CLI command (e.g., `fly status`, `kubectl rollout status`)
   - C) Check the GitHub Actions workflow status
   - D) No automated way — just check the URL loads

4. **Any pre-merge or post-merge hooks?**
   - Commands to run before merging (e.g., `pnpm run build`)
   - Commands to run after merge but before deploy verification

## Step 4: Write configuration

Write the configuration to `.deploy-config.json` at the project root. This file is the
source of truth for future deploy workflows. Use JSON for easy machine parsing.

```json
{
  "platform": "fly",
  "production_url": "https://myapp.fly.dev",
  "deploy_trigger": "automatic on push to main",
  "deploy_workflow_file": ".github/workflows/deploy.yml",
  "deploy_status_command": "fly status --app myapp",
  "health_check_url": "https://myapp.fly.dev/health",
  "health_check_command": null,
  "merge_method": "squash",
  "project_type": "web app",
  "pre_merge_hook": "pnpm run build && pnpm test",
  "post_merge_hook": null
}
```

Set unused fields to `null`. If the user prefers the config inside CLAUDE.md instead of a
separate file, write the same data as a markdown section:

```markdown
## Deploy Configuration

- Platform: fly
- Production URL: https://myapp.fly.dev
- Deploy trigger: automatic on push to main
- Deploy workflow file: .github/workflows/deploy.yml
- Deploy status command: `fly status --app myapp`
- Health check URL: https://myapp.fly.dev/health
- Health check command: (none)
- Merge method: squash
- Project type: web app
- Pre-merge hook: `pnpm run build && pnpm test`
- Post-merge hook: (none)
```

## Step 5: Verify

After writing, verify the configuration actually works:

1. If a health check URL was configured, try it:
```bash
curl -sf "{health-check-url}" -o /dev/null -w "%{http_code}\n" 2>/dev/null || echo "UNREACHABLE"
```

2. If a deploy status command was configured, try it:
```bash
{deploy-status-command} 2>/dev/null | head -5 || echo "COMMAND_FAILED"
```

Report results. If anything failed, note it but don't block — the config is still useful
even if the health check is temporarily unreachable.

## Step 6: Summary

Print a clean summary:

```
DEPLOY CONFIGURATION — COMPLETE
════════════════════════════════
Platform:      {platform}
URL:           {url}
Health check:  {health check}
Status cmd:    {status command}
Merge method:  {merge method}

Saved to .deploy-config.json (or CLAUDE.md). Future deploy workflows will read these
settings automatically.

Next steps:
- Run your deploy workflow to merge and deploy the current PR
- Edit .deploy-config.json (or the "## Deploy Configuration" section in CLAUDE.md)
  to change settings
- Re-run /setup-deploy to reconfigure
```

## Important rules

- **Never expose secrets.** Don't print full API keys, tokens, or passwords. Truncate to
  the first 4 characters max if you need to confirm presence.
- **Confirm with the user.** Always show detected config and ask for confirmation before
  writing.
- **Idempotent.** Re-running overwrites the previous config cleanly.
- **Platform CLIs are optional.** If `fly`, `vercel`, `railway`, etc. aren't installed,
  fall back to URL-based health checks.
- **Use pnpm for hooks if the project uses pnpm.** Check for `pnpm-lock.yaml` to decide
  whether to suggest `pnpm` vs `npm` vs `bun`.
