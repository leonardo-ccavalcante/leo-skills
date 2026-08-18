#!/usr/bin/env bash
# fa.sh — single entry point for the financial-analysis skill.
#
#   fa.sh <command> [args...]
#
# Commands:
#   unit-economics   CAC, LTV, LTV:CAC, payback, contribution, break-even
#   saas             SaaS point metrics, ARR bridge (--mrr-file), cohorts (--cohort-file)
#   projection       36-month P&L + cash cascade + runway (--drivers-file)
#   ratios           Statement ratios, DuPont, common-size
#   scenarios        Driver-multiplier scenarios, sensitivity, reversal thresholds
#   ops              Operational finance: unit-cost|cost-to-serve|capacity|headcount|roi|variance
#   validate <file>  Validate a .fa.json tagged-inputs state file
#   selftest         Golden-number tests for every formula module
#   doctor           Environment check (python3, pandas/openpyxl)
#
# All analysis commands accept --json (recommended). Exit codes:
#   0 OK/PARTIAL · 1 unexpected error · 2 INSUFFICIENT_DATA · 3 validation failure

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON="${FA_PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "fa.sh: python3 not found on PATH. Install Python 3.9+ to use this skill." >&2
  exit 1
fi

usage() { sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; }

cmd="${1:-}"
[ -n "$cmd" ] || { usage; exit 1; }
shift || true

case "$cmd" in
  unit-economics) exec "$PYTHON" "$SCRIPT_DIR/unit_economics.py" "$@" ;;
  saas)           exec "$PYTHON" "$SCRIPT_DIR/saas_metrics.py" "$@" ;;
  projection)     exec "$PYTHON" "$SCRIPT_DIR/projection.py" "$@" ;;
  ratios)         exec "$PYTHON" "$SCRIPT_DIR/ratios.py" "$@" ;;
  scenarios)      exec "$PYTHON" "$SCRIPT_DIR/scenarios.py" "$@" ;;
  ops)            exec "$PYTHON" "$SCRIPT_DIR/opsfinance.py" "$@" ;;
  validate)       exec "$PYTHON" "$SCRIPT_DIR/validate_state.py" "$@" ;;
  selftest)       exec "$PYTHON" "$SCRIPT_DIR/selftest.py" "$@" ;;
  doctor)
    echo "financial-analysis doctor"
    echo "  python3: $("$PYTHON" --version 2>&1)"
    "$PYTHON" - <<'EOF'
import sys
ok = sys.version_info >= (3, 9)
print(f"  version >= 3.9: {'ok' if ok else 'TOO OLD — upgrade Python'}")
for mod, why in (("pandas", "CSV/Excel inputs"), ("openpyxl", ".xlsx inputs")):
    try:
        __import__(mod)
        print(f"  {mod}: ok")
    except ImportError:
        print(f"  {mod}: MISSING (only needed for {why}; conversation inputs work without it)")
        print(f"          install: pip install {mod}")
sys.exit(0 if ok else 1)
EOF
    ;;
  -h|--help|help) usage ;;
  *)
    echo "fa.sh: unknown command '$cmd'" >&2
    usage >&2
    exit 1
    ;;
esac
