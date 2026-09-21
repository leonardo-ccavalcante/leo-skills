#!/bin/bash
# tests/fixture/setup.sh -- prepare the synthetic fixture for a manual e2e run.
#
# Idempotent; touches only files under tests/fixture/. Run it before the steps
# in tests/e2e/EXPECTED.md:
#
#   eval "$(/bin/bash tests/fixture/setup.sh)"
#
# What it does
#   1. rewrites `kb_root` in tests/fixture/kb/kb-verify.config.json to the
#      absolute physical path of tests/fixture/kb (via jq; other keys untouched);
#   2. creates the symlink trap tests/fixture/kb/articles/linked-outside ->
#      ../../outside-kb, a directory OUTSIDE the KB that holds trap.md
#      (a Write to articles/linked-outside/trap.kb-verify.diff must be denied);
#   3. creates the data dir tests/fixture/.data (runs/ and repo/ land there);
#   4. validates the rewritten config with lib/common.sh and prints, on stderr,
#      the resolved paths and each article's id (first 12 hex of its sha256);
#   5. prints, on stdout, the two export lines the e2e session needs.
#
# bash 3.2 compatible. Needs jq (resolved by lib/common.sh), realpath, shasum.

set -eu

HERE=$(cd "$(dirname "$0")" && pwd -P)
PLUGIN_ROOT=$(cd "$HERE/../.." && pwd -P)
LIB="$PLUGIN_ROOT/lib/common.sh"
KB="$HERE/kb"
REPO="$HERE/fake-repo"
DATA="$HERE/.data"
OUTSIDE="$HERE/outside-kb"
CONFIG="$KB/kb-verify.config.json"
LINK="$KB/articles/linked-outside"

say() { printf 'setup: %s\n' "$*" >&2; }
die() { printf 'setup: error: %s\n' "$*" >&2; exit 1; }
# Single-quote a value for the export lines (embedded ' becomes '\'').
shq() { printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"; }

# The fixture config is what we validate; ignore overrides from the caller.
unset KB_VERIFY_CONFIG KB_VERIFY_JQ CDPATH

# shellcheck source=../../lib/common.sh
. "$LIB" || die "cannot source $LIB"
JQ=$(kbv_resolve_jq) || die "jq not found (tried: $KBV_JQ_CANDIDATES, then PATH)"
[ -d "$REPO" ] || die "fake repo missing: $REPO"
[ -f "$CONFIG" ] || die "fixture config missing: $CONFIG"
[ -d "$KB/articles" ] || die "articles dir missing: $KB/articles"

# 1. absolute kb_root -------------------------------------------------------
TMP="$HERE/.kb-verify.config.tmp.$$"
trap 'rm -f "$TMP"' EXIT
"$JQ" --arg root "$KB" '.kb_root = $root' "$CONFIG" > "$TMP" || die "jq failed rewriting $CONFIG"
mv "$TMP" "$CONFIG"
say "kb_root rewritten to $KB"

# 2. symlink trap -----------------------------------------------------------
mkdir -p "$OUTSIDE"
if [ ! -f "$OUTSIDE/trap.md" ]; then
  cat > "$OUTSIDE/trap.md" <<'EOF'
---
titulo: TRAP - this file lives outside the KB
estado: review
---

# TRAP - this file lives outside the KB

It is reachable through the symlink `articles/linked-outside`. kb-verify must
never write next to it: `articles/linked-outside/trap.kb-verify.diff`
normalizes to a path outside `articles_dir`, so the guard must deny it.
EOF
fi
if [ -L "$LINK" ]; then
  rm -f "$LINK"
elif [ -e "$LINK" ]; then
  die "$LINK exists and is not a symlink; remove it by hand"
fi
ln -s ../../outside-kb "$LINK"
say "symlink trap: $LINK -> ../../outside-kb"

# 3. data dir ---------------------------------------------------------------
mkdir -p "$DATA"
say "data dir: $DATA"

# 4. validate ---------------------------------------------------------------
kbv_load_config "$CONFIG" || die "config invalid ($KBV_CONFIG_ERROR)"
say "config OK"
say "  kb_root      = $KBV_KB_ROOT"
say "  articles_dir = $KBV_ARTICLES_DIR"
say "  triage_dir   = $KBV_TRIAGE_DIR"
say "  gh.repo      = $KBV_GH_REPO"
say "article ids (--article = first 12 hex of the file's sha256):"
for f in "$KB"/articles/0[0-9]-*.md; do
  [ -f "$f" ] || continue
  sha=$(kbv_sha256 "$f") || die "sha256 failed for $f"
  say "  ${sha:0:12}  articles/$(basename "$f")"
done

# 5. exports ----------------------------------------------------------------
say "next: eval the two lines below in the shell that will start claude, then: cd $KB && claude"
printf 'export KB_VERIFY_GH_MOCK=%s\n' "$(shq "$REPO")"
printf 'export KB_VERIFY_DATA_DIR=%s\n' "$(shq "$DATA")"
