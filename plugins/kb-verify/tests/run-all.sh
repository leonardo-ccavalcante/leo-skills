#!/bin/bash
# tests/run-all.sh -- runs every kb-verify test suite in order with /bin/bash.
#
# Suites (in order):  tests/lib/run.sh   tests/hooks/run.sh   tests/scripts/run.sh
# Stops at the first failing (or missing) suite, prints a summary, exits 1.
# Exit 0 only when every suite passed. bash 3.2 clean: no arrays, no mapfile.
#
# Run:  /bin/bash tests/run-all.sh

set -u

HERE=$(cd "$(dirname "$0")" && pwd -P)
SUITES="lib hooks scripts"

passed=""
failed=""
status=0

run_suite() {
  # run_suite <name>  -> 0 on pass, 1 on fail/missing; records the result.
  local name="$1" script="$HERE/$1/run.sh" rc
  if [ ! -f "$script" ]; then
    printf '=== %s: MISSING (%s)\n' "$name" "$script"
    failed="$failed $name(missing)"
    return 1
  fi
  printf '=== %s: %s\n' "$name" "$script"
  /bin/bash "$script"
  rc=$?
  if [ "$rc" -eq 0 ]; then
    printf '=== %s: PASS\n\n' "$name"
    passed="$passed $name"
    return 0
  fi
  printf '=== %s: FAIL (exit %d)\n\n' "$name" "$rc"
  failed="$failed $name(exit $rc)"
  return 1
}

for s in $SUITES; do
  if ! run_suite "$s"; then
    status=1
    break
  fi
done

printf '#### kb-verify test summary (bash %s)\n' "$BASH_VERSION"
printf '#### passed:%s\n' "${passed:- none}"
printf '#### failed:%s\n' "${failed:- none}"
if [ "$status" -eq 0 ]; then
  printf '#### RESULT: all suites passed\n'
else
  printf '#### RESULT: stopped at first failure\n'
fi
exit "$status"
