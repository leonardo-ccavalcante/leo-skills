---
name: gstack-upgrade
description: |
  Upgrade gstack (https://github.com/garrytan/gstack) to the latest version on this machine.
  Detects whether the install is global-git, local-git, or vendored; pulls the latest changes
  or re-clones; runs setup; applies version migrations; and shows what's new from the
  CHANGELOG. This is gstack-specific — gstack users only. Use this skill whenever the user
  says "upgrade gstack", "update gstack", "get latest gstack", "gstack upgrade", "gee stack
  upgrade", "upgrade the tools", or "update the tools". Triggers on /gstack-upgrade.
  Proactively invoke when a skill preamble surfaces `UPGRADE_AVAILABLE`.
---

# Upgrade gstack to the latest version

Upgrade gstack to the latest version and show what's new. Handles three install layouts:
global-git (cloned to `~/.claude/skills/gstack/` or `~/.gstack/repos/gstack/`), local-git
(cloned into the current project), and vendored (a plain copy with no `.git`).

## Inline upgrade flow (called from skill preambles when UPGRADE_AVAILABLE)

### Step 1: Decide whether to upgrade

Check whether auto-upgrade is enabled:

```bash
_AUTO=""
[ "${GSTACK_AUTO_UPGRADE:-}" = "1" ] && _AUTO="true"
[ -z "$_AUTO" ] && _AUTO=$(cat ~/.gstack/config.yaml 2>/dev/null | grep -E '^auto_upgrade:' | awk '{print $2}')
echo "AUTO_UPGRADE=$_AUTO"
```

**If `AUTO_UPGRADE=true`:** Skip the prompt. Log "Auto-upgrading gstack v{old} → v{new}..."
and proceed to Step 2. If `./setup` fails during auto-upgrade, restore from the backup
(`.bak` directory) and warn: "Auto-upgrade failed — restored previous version. Run
`/gstack-upgrade` manually to retry."

**Otherwise**, ask:

> gstack **v{new}** is available (you're on v{old}). Upgrade now?
>
> A) Yes, upgrade now
> B) Always keep me up to date (set `auto_upgrade: true` in `~/.gstack/config.yaml`)
> C) Not now (escalating backoff: 24h → 48h → 1 week)
> D) Never ask again (disables update checks)

**If "Yes":** Proceed to Step 2.

**If "Always keep me up to date":**

```bash
mkdir -p ~/.gstack
# Set auto_upgrade: true in ~/.gstack/config.yaml
if [ -f ~/.gstack/config.yaml ]; then
  grep -v '^auto_upgrade:' ~/.gstack/config.yaml > ~/.gstack/config.yaml.tmp
  mv ~/.gstack/config.yaml.tmp ~/.gstack/config.yaml
fi
echo "auto_upgrade: true" >> ~/.gstack/config.yaml
```

Tell the user: "Auto-upgrade enabled. Future updates will install automatically." Then
proceed to Step 2.

**If "Not now":** Write snooze state with escalating backoff (first snooze = 24h, second
= 48h, third+ = 1 week), then continue with whatever skill the user originally invoked. Do
not mention the upgrade again.

```bash
_SNOOZE_FILE="$HOME/.gstack/update-snoozed"
_REMOTE_VER="{new}"  # substitute from the UPGRADE_AVAILABLE output
_CUR_LEVEL=0
if [ -f "$_SNOOZE_FILE" ]; then
  _SNOOZED_VER=$(awk '{print $1}' "$_SNOOZE_FILE")
  if [ "$_SNOOZED_VER" = "$_REMOTE_VER" ]; then
    _CUR_LEVEL=$(awk '{print $2}' "$_SNOOZE_FILE")
    case "$_CUR_LEVEL" in *[!0-9]*) _CUR_LEVEL=0 ;; esac
  fi
fi
_NEW_LEVEL=$((_CUR_LEVEL + 1))
[ "$_NEW_LEVEL" -gt 3 ] && _NEW_LEVEL=3
mkdir -p ~/.gstack
echo "$_REMOTE_VER $_NEW_LEVEL $(date +%s)" > "$_SNOOZE_FILE"
```

Tip: "Set `auto_upgrade: true` in `~/.gstack/config.yaml` for automatic upgrades."

**If "Never ask again":** Disable update checks (write `update_check: false` to
`~/.gstack/config.yaml`). Tell the user how to re-enable. Continue with the current skill.

### Step 2: Detect install type

```bash
if [ -d "$HOME/.claude/skills/gstack/.git" ]; then
  INSTALL_TYPE="global-git"
  INSTALL_DIR="$HOME/.claude/skills/gstack"
elif [ -d "$HOME/.gstack/repos/gstack/.git" ]; then
  INSTALL_TYPE="global-git"
  INSTALL_DIR="$HOME/.gstack/repos/gstack"
elif [ -d ".claude/skills/gstack/.git" ]; then
  INSTALL_TYPE="local-git"
  INSTALL_DIR=".claude/skills/gstack"
elif [ -d ".agents/skills/gstack/.git" ]; then
  INSTALL_TYPE="local-git"
  INSTALL_DIR=".agents/skills/gstack"
elif [ -d ".claude/skills/gstack" ]; then
  INSTALL_TYPE="vendored"
  INSTALL_DIR=".claude/skills/gstack"
elif [ -d "$HOME/.claude/skills/gstack" ]; then
  INSTALL_TYPE="vendored-global"
  INSTALL_DIR="$HOME/.claude/skills/gstack"
else
  echo "ERROR: gstack not found"
  exit 1
fi
echo "Install type: $INSTALL_TYPE at $INSTALL_DIR"
```

### Step 3: Save old version

```bash
OLD_VERSION=$(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo "unknown")
```

### Step 4: Upgrade

**For git installs** (global-git, local-git):

```bash
cd "$INSTALL_DIR"
STASH_OUTPUT=$(git stash 2>&1)
git fetch origin
git reset --hard origin/main
./setup
```

If `$STASH_OUTPUT` contains "Saved working directory", warn: "Note: local changes were
stashed. Run `git stash pop` in the skill directory to restore them."

**For vendored installs** (vendored, vendored-global):

```bash
PARENT=$(dirname "$INSTALL_DIR")
TMP_DIR=$(mktemp -d)
git clone --depth 1 https://github.com/garrytan/gstack.git "$TMP_DIR/gstack"
mv "$INSTALL_DIR" "$INSTALL_DIR.bak"
mv "$TMP_DIR/gstack" "$INSTALL_DIR"
cd "$INSTALL_DIR" && ./setup
rm -rf "$INSTALL_DIR.bak" "$TMP_DIR"
```

If `./setup` fails, restore from `$INSTALL_DIR.bak`.

### Step 4.5: Handle local vendored copy

Check whether there's also a local vendored copy in the current project, separate from the
primary install:

```bash
_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
LOCAL_GSTACK=""
if [ -n "$_ROOT" ] && [ -d "$_ROOT/.claude/skills/gstack" ]; then
  _RESOLVED_LOCAL=$(cd "$_ROOT/.claude/skills/gstack" && pwd -P)
  _RESOLVED_PRIMARY=$(cd "$INSTALL_DIR" && pwd -P)
  if [ "$_RESOLVED_LOCAL" != "$_RESOLVED_PRIMARY" ]; then
    LOCAL_GSTACK="$_ROOT/.claude/skills/gstack"
  fi
fi
# Detect team mode (if config exists)
_TEAM_MODE=$(grep -E '^team_mode:' ~/.gstack/config.yaml 2>/dev/null | awk '{print $2}' || echo "false")
echo "LOCAL_GSTACK=$LOCAL_GSTACK"
echo "TEAM_MODE=$_TEAM_MODE"
```

**If `LOCAL_GSTACK` is non-empty AND `TEAM_MODE` is `true`:** Remove the vendored copy.
Team mode uses the global install as the single source of truth.

```bash
cd "$_ROOT"
git rm -r --cached .claude/skills/gstack/ 2>/dev/null || true
if ! grep -qF '.claude/skills/gstack/' .gitignore 2>/dev/null; then
  echo '.claude/skills/gstack/' >> .gitignore
fi
rm -rf "$LOCAL_GSTACK"
```

Tell the user: "Removed vendored copy at `$LOCAL_GSTACK` (team mode active — global install
is the source of truth). Commit the `.gitignore` change when ready."

**If `LOCAL_GSTACK` is non-empty AND `TEAM_MODE` is NOT `true`:** Update the vendored copy
from the freshly-upgraded primary:

```bash
mv "$LOCAL_GSTACK" "$LOCAL_GSTACK.bak"
cp -Rf "$INSTALL_DIR" "$LOCAL_GSTACK"
rm -rf "$LOCAL_GSTACK/.git"
cd "$LOCAL_GSTACK" && ./setup
rm -rf "$LOCAL_GSTACK.bak"
```

Tell the user: "Also updated vendored copy at `$LOCAL_GSTACK` — commit
`.claude/skills/gstack/` when you're ready."

If `./setup` fails, restore from backup:

```bash
rm -rf "$LOCAL_GSTACK"
mv "$LOCAL_GSTACK.bak" "$LOCAL_GSTACK"
```

Tell the user: "Sync failed — restored previous version at `$LOCAL_GSTACK`. Run
`/gstack-upgrade` manually to retry."

### Step 4.75: Run version migrations

After `./setup` completes, run any migration scripts for versions between the old and new
version. Migrations handle state fixes that `./setup` alone can't cover (stale config,
orphaned files, directory structure changes).

```bash
MIGRATIONS_DIR="$INSTALL_DIR/gstack-upgrade/migrations"
if [ -d "$MIGRATIONS_DIR" ]; then
  for migration in $(find "$MIGRATIONS_DIR" -maxdepth 1 -name 'v*.sh' -type f 2>/dev/null | sort -V); do
    # Extract version from filename: v0.15.2.0.sh → 0.15.2.0
    m_ver="$(basename "$migration" .sh | sed 's/^v//')"
    # Run if this migration version is newer than old version
    if [ "$OLD_VERSION" != "unknown" ] && \
       [ "$(printf '%s\n%s' "$OLD_VERSION" "$m_ver" | sort -V | head -1)" = "$OLD_VERSION" ] && \
       [ "$OLD_VERSION" != "$m_ver" ]; then
      echo "Running migration $m_ver..."
      bash "$migration" || echo "  Warning: migration $m_ver had errors (non-fatal)"
    fi
  done
fi
```

Migrations are idempotent bash scripts in `gstack-upgrade/migrations/`. Each is named
`v{VERSION}.sh` and runs only when upgrading from an older version.

### Step 5: Write marker + clear cache

```bash
mkdir -p ~/.gstack
echo "$OLD_VERSION" > ~/.gstack/just-upgraded-from
rm -f ~/.gstack/last-update-check
rm -f ~/.gstack/update-snoozed
```

### Step 6: Show what's new

Read `$INSTALL_DIR/CHANGELOG.md`. Find all version entries between the old version and the
new version. Summarize as 5-7 bullets grouped by theme. Don't overwhelm — focus on
user-facing changes. Skip internal refactors unless they're significant.

Format:

```
gstack v{new} — upgraded from v{old}!

What's new:
- [bullet 1]
- [bullet 2]
- ...

Happy shipping!
```

### Step 7: Continue

After showing what's new, continue with whatever skill the user originally invoked. The
upgrade is done — no further action needed.

---

## Standalone usage

When invoked directly as `/gstack-upgrade` (not from a preamble):

1. Force a fresh update check. Compare the current version (from `$INSTALL_DIR/VERSION`)
   to the latest GitHub release:

```bash
LATEST=$(curl -fsSL https://api.github.com/repos/garrytan/gstack/releases/latest 2>/dev/null \
  | grep -m1 '"tag_name"' | sed 's/.*"tag_name": *"v\?\([^"]*\)".*/\1/')
echo "LATEST=$LATEST"
```

2. If an upgrade is available: follow Steps 2-6 above.

3. If no upgrade is available: check for a stale local vendored copy. Run the Step 2
   detection to find the primary install (`INSTALL_TYPE`, `INSTALL_DIR`), then the Step 4.5
   detection to find `LOCAL_GSTACK` and `TEAM_MODE`.

   **If `LOCAL_GSTACK` is empty:** Tell the user "You're already on the latest version
   (v{version})."

   **If `LOCAL_GSTACK` is non-empty AND `TEAM_MODE` is `true`:** Remove the vendored copy
   (Step 4.5 team-mode removal). Tell the user: "Global v{version} is up to date. Removed
   stale vendored copy (team mode active). Commit the `.gitignore` change when ready."

   **If `LOCAL_GSTACK` is non-empty AND `TEAM_MODE` is NOT `true`:** Compare versions:

```bash
PRIMARY_VER=$(cat "$INSTALL_DIR/VERSION" 2>/dev/null || echo "unknown")
LOCAL_VER=$(cat "$LOCAL_GSTACK/VERSION" 2>/dev/null || echo "unknown")
echo "PRIMARY=$PRIMARY_VER LOCAL=$LOCAL_VER"
```

   **If versions differ:** Follow the Step 4.5 sync to update the local copy from the
   primary. Tell the user: "Global v{PRIMARY_VER} is up to date. Updated local vendored
   copy from v{LOCAL_VER} → v{PRIMARY_VER}. Commit `.claude/skills/gstack/` when you're
   ready."

   **If versions match:** Tell the user "You're on the latest version (v{PRIMARY_VER}).
   Global and local vendored copy are both up to date."

## Notes

- This skill uses `git` and `curl` directly — no `pnpm dlx` invocation needed for the
  upgrade itself since gstack ships its own `./setup` script.
- If `./setup` invokes a package manager internally, it should prefer `pnpm` over `bun` or
  `npm` when the project's lockfile indicates pnpm.
