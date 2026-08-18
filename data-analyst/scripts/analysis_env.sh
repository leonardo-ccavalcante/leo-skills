#!/usr/bin/env bash
# Environment check/setup for the data-analyst skill.
# Detects the local Python/Jupyter stack, installs only what's missing, and
# verifies that notebook execution works. Safe to re-run; it never reinstalls
# what already works.
set -u

PY="${DATA_ANALYST_PYTHON:-}"
if [ -z "$PY" ]; then
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then PY="$candidate"; break; fi
  done
fi
if [ -z "$PY" ]; then
  echo "FAIL: no python3 found on PATH. Install Python (anaconda or python.org) first." >&2
  exit 1
fi

echo "python: $("$PY" -c 'import sys; print(sys.executable, sys.version.split()[0])')"

REQUIRED="pandas scipy statsmodels duckdb pyarrow"
MISSING=""
for pkg in $REQUIRED; do
  if "$PY" -c "import $pkg" >/dev/null 2>&1; then
    echo "ok: $pkg $("$PY" -c "import $pkg; print(getattr($pkg, '__version__', ''))" 2>/dev/null)"
  else
    MISSING="$MISSING $pkg"
  fi
done

if [ -n "$MISSING" ]; then
  echo "installing missing packages:$MISSING"
  "$PY" -m pip install --quiet $MISSING || {
    echo "WARN: pip install failed for:$MISSING — analysis can proceed without duckdb (pandas-only), but large/multi-file inputs will be slower." >&2
  }
fi

# Notebook execution path: nbconvert + a kernel.
if "$PY" -m jupyter nbconvert --version >/dev/null 2>&1; then
  echo "ok: nbconvert $("$PY" -m jupyter nbconvert --version 2>/dev/null)"
else
  echo "installing notebook execution deps (nbconvert, nbclient, ipykernel)"
  "$PY" -m pip install --quiet nbconvert nbclient ipykernel jupyter_core || {
    echo "WARN: could not install nbconvert — fall back to numbered .py scripts for analysis." >&2
  }
fi

if "$PY" -m jupyter kernelspec list >/dev/null 2>&1; then
  echo "kernels:"
  "$PY" -m jupyter kernelspec list 2>/dev/null | sed 's/^/  /'
else
  echo "registering python3 kernel"
  "$PY" -m ipykernel install --user --name python3 >/dev/null 2>&1 || \
    echo "WARN: could not register a kernel — notebook execution may fail; use .py scripts fallback." >&2
fi

# Smoke test: execute a one-cell notebook end to end.
TMPNB="$(mktemp -d)/smoke.ipynb"
"$PY" - "$TMPNB" <<'EOF'
import json, sys
nb = {"cells": [{"cell_type": "code", "metadata": {}, "source": "import pandas as pd\nprint('notebook-exec-ok', pd.__version__)", "outputs": [], "execution_count": None}],
      "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
open(sys.argv[1], "w").write(json.dumps(nb))
EOF
if "$PY" -m jupyter nbconvert --to notebook --execute --inplace "$TMPNB" >/dev/null 2>&1 \
   && grep -q "notebook-exec-ok" "$TMPNB"; then
  echo "ok: notebook execution verified (nbconvert --execute)"
else
  echo "WARN: notebook execution smoke test failed — use numbered .py scripts as the fallback." >&2
fi

echo "environment ready. Use this interpreter for all analysis: $PY"
