#!/usr/bin/env bash
# bp.sh — single entry point for the business-planning skill.
#
#   bp.sh <command> [args...]
#
# Commands:
#   readiness        8-dimension readiness score + HEALTHY/FRAGILE/UNSUSTAINABLE/INSUFFICIENT_DATA verdict
#   market           Bottom-up TAM/SAM/SOM chain with per-step provenance (rejects top-down shapes)
#   scenarios        Locked conservative/base/optimistic multiplier table + fa.sh-ready driver files
#   lint <path>      Lint plan artifacts: frontmatter, Assumptions section,
#                    orphan figures, prose precision
#   retro-score <dir> Domain-agnostic e2e process scorecard over a bp_<slug>/ workspace
#   validate <file>  Strict validation of a .bp.json tagged-inputs state file
#   selftest         Golden-number tests for every module
#   doctor           Environment check (python3, fa.sh delegation probe)
#
# All analysis commands accept --json (recommended). Exit codes:
#   0 OK/PARTIAL · 1 unexpected error · 2 INSUFFICIENT_DATA · 3 validation failure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON="${BP_PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "bp.sh: python3 not found on PATH. Install Python 3.9+ to use this skill." >&2
  exit 1
fi

FA_SH="${BP_FA_SH:-$HOME/.claude/skills/financial-analysis/scripts/fa.sh}"

usage() { sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; }

runmod() {
  # Exec a Python module, but fail with exit 1 (bug/unavailable) — never 2
  # (which is contractually INSUFFICIENT_DATA) — when the module is absent.
  local mod="$1"; shift
  if [ ! -f "$SCRIPT_DIR/$mod" ]; then
    echo "bp.sh: module $mod not found — incomplete installation or build in progress" >&2
    exit 1
  fi
  exec "$PYTHON" "$SCRIPT_DIR/$mod" "$@"
}

cmd="${1:-}"
[ -n "$cmd" ] || { usage; exit 1; }
shift || true

case "$cmd" in
  readiness)      runmod readiness.py "$@" ;;
  market)         runmod market_sizing.py "$@" ;;
  scenarios)      runmod scenario_table.py "$@" ;;
  lint)           runmod artifact_lint.py "$@" ;;
  retro-score)    runmod session_score.py "$@" ;;
  validate)       runmod validate_state.py "$@" ;;
  selftest)       runmod selftest.py "$@" ;;
  doctor)
    echo "business-planning doctor"
    echo "  python3: $("$PYTHON" --version 2>&1)"
    "$PYTHON" - <<'EOF'
import sys
ok = sys.version_info >= (3, 9)
print(f"  version >= 3.9: {'ok' if ok else 'TOO OLD — upgrade Python'}")
sys.exit(0 if ok else 1)
EOF
    if [ -x "$FA_SH" ]; then
      echo "  financial delegation: available ($FA_SH)"
    else
      echo "  financial delegation: unavailable — plans will carry not_computed"
      echo "    financial sections until the financial-analysis skill is installed."
      echo "    (override probe path with BP_FA_SH)"
    fi
    ;;
  -h|--help|help) usage ;;
  *)
    echo "bp.sh: unknown command '$cmd'" >&2
    usage >&2
    exit 1
    ;;
esac
