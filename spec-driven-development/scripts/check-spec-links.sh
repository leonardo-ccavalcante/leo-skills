#!/usr/bin/env bash
#
# check-spec-links.sh — verify that a spec's targets and [@test] links resolve.
# Adapted from tesslio/spec-driven-development-tile for the spec-driven-development skill.
#
# For each .spec.md:
#   1. Frontmatter targets: each listed path must exist (relative to the spec's directory).
#      A glob that matches no files is flagged.
#   2. Body [@test] links: each referenced file must exist (relative to the spec's directory).
#
# Usage: check-spec-links.sh [specs-directory]   (default: ./specs)
# Exit:  0 if all links resolve, 1 if any are broken or the directory is missing.

set -euo pipefail

DIR="${1:-./specs}"

if [ ! -d "$DIR" ]; then
  echo "ERROR: directory not found: $DIR" >&2
  exit 1
fi

checked=0
failures=0

resolve_exists() {
  # $1 = base directory of the spec, $2 = relative path or glob
  local base="$1" rel="$2" matched=0 g
  # Enable globbing that yields nothing (rather than the literal) when no match.
  shopt -s nullglob
  for g in "$base"/$rel; do
    if [ -e "$g" ]; then matched=1; fi
  done
  shopt -u nullglob
  # Also handle the plain (non-glob) case explicitly.
  if [ "$matched" -eq 0 ] && [ -e "$base/$rel" ]; then matched=1; fi
  [ "$matched" -eq 1 ]
}

while IFS= read -r -d '' f; do
  checked=$((checked + 1))
  base="$(dirname "$f")"
  broken=""

  # --- 1. Frontmatter targets ---
  fm="$(awk 'NR==1 && $0=="---"{infm=1; next} infm && $0=="---"{exit} infm{print}' "$f")"
  targets="$(echo "$fm" | awk '
    /^targets:/{intg=1
      # inline list form: targets: [a, b]
      if ($0 ~ /\[/){ gsub(/^targets:[[:space:]]*\[/,""); gsub(/\].*/,""); gsub(/,/," "); print; intg=0 }
      next}
    intg && /^[A-Za-z0-9_]+:/{intg=0}
    intg && /^[[:space:]]*-[[:space:]]*/{ sub(/^[[:space:]]*-[[:space:]]*/,""); print }
  ')"
  while IFS= read -r t; do
    [ -z "$t" ] && continue
    t="$(echo "$t" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//; s/^["'\'']//; s/["'\'']$//')"
    [ -z "$t" ] && continue
    if ! resolve_exists "$base" "$t"; then
      broken="${broken}\n  - target not found: $t"
    fi
  done <<EOF
$targets
EOF

  # --- 2. Body [@test] links ---
  # Match patterns like: [@test] path/to/test.py   (optionally inside backticks)
  links="$(grep -oE '\[@test\][[:space:]]*`?[^`[:space:])]+' "$f" 2>/dev/null \
            | sed -E 's/\[@test\][[:space:]]*`?//' || true)"
  while IFS= read -r l; do
    [ -z "$l" ] && continue
    if ! resolve_exists "$base" "$l"; then
      broken="${broken}\n  - [@test] not found: $l"
    fi
  done <<EOF
$links
EOF

  if [ -n "$broken" ]; then
    failures=$((failures + 1))
    printf "BROKEN: %s%b\n" "$f" "$broken"
  else
    echo "OK:     $f"
  fi
done < <(find "$DIR" -type f -name '*.spec.md' -print0)

echo "----"
echo "checked $checked spec(s), $failures with broken links"
[ "$failures" -eq 0 ]
