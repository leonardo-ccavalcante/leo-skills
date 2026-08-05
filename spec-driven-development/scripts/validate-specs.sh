#!/usr/bin/env bash
#
# validate-specs.sh — validate .spec.md structure (tesslio-style).
# Adapted from tesslio/spec-driven-development-tile for the spec-driven-development skill.
#
# Checks, per .spec.md file:
#   - filename ends in .spec.md
#   - YAML frontmatter present (delimited by --- at the very top)
#   - frontmatter contains: name, description, targets
#   - targets has at least one entry
# Also warns about .md files that look like specs but lack the .spec.md extension.
#
# Usage: validate-specs.sh [specs-directory]   (default: ./specs)
# Exit:  0 if all pass, 1 if any fail or the directory is missing.

set -euo pipefail

DIR="${1:-./specs}"

if [ ! -d "$DIR" ]; then
  echo "ERROR: directory not found: $DIR" >&2
  exit 1
fi

checked=0
failures=0

# Warn about likely specs with the wrong extension (.md but not .spec.md, body mentions targets:)
while IFS= read -r -d '' f; do
  case "$f" in
    *.spec.md) : ;;
    *.md)
      if grep -q '^targets:' "$f" 2>/dev/null; then
        echo "WARN: $f looks like a spec but does not use the .spec.md extension"
      fi
      ;;
  esac
done < <(find "$DIR" -type f -name '*.md' -print0)

# Validate each .spec.md
while IFS= read -r -d '' f; do
  checked=$((checked + 1))
  errors=""

  # Frontmatter must start on line 1 with --- and have a closing ---
  first_line="$(head -n 1 "$f")"
  if [ "$first_line" != "---" ]; then
    errors="${errors}\n  - missing YAML frontmatter (file must begin with ---)"
  else
    # Extract frontmatter: lines between the first and second --- delimiters.
    fm="$(awk 'NR==1 && $0=="---"{infm=1; next} infm && $0=="---"{exit} infm{print}' "$f")"
    if [ -z "$fm" ]; then
      errors="${errors}\n  - empty or unterminated frontmatter"
    else
      echo "$fm" | grep -q '^name:[[:space:]]*[^[:space:]]' || errors="${errors}\n  - missing 'name'"
      echo "$fm" | grep -q '^description:[[:space:]]*[^[:space:]]' || errors="${errors}\n  - missing 'description'"
      if ! echo "$fm" | grep -q '^targets:'; then
        errors="${errors}\n  - missing 'targets'"
      else
        # Count list entries under targets: (lines like "  - path") OR an inline list "targets: [a, b]".
        inline="$(echo "$fm" | sed -n 's/^targets:[[:space:]]*\[\(.*\)\].*/\1/p')"
        if [ -n "$inline" ]; then
          count=1
        else
          count="$(echo "$fm" | awk '
            /^targets:/{intg=1; next}
            intg && /^[A-Za-z0-9_]+:/{intg=0}
            intg && /^[[:space:]]*-[[:space:]]*[^[:space:]]/{c++}
            END{print c+0}')"
        fi
        if [ "${count:-0}" -lt 1 ]; then
          errors="${errors}\n  - 'targets' must list at least one entry"
        fi
      fi
    fi
  fi

  if [ -n "$errors" ]; then
    failures=$((failures + 1))
    printf "FAIL: %s%b\n" "$f" "$errors"
  else
    echo "OK:   $f"
  fi
done < <(find "$DIR" -type f -name '*.spec.md' -print0)

echo "----"
echo "checked $checked spec(s), $failures failure(s)"
[ "$failures" -eq 0 ]
