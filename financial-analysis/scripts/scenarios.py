"""scenarios — driver-multiplier scenarios, sensitivity, and reversal thresholds.

Three analyses over any of the skill's models (unit-economics | saas | projection):

1. Scenarios: named cases (conservative/base/optimistic) defined ONLY as
   multipliers on drivers. The base scenario is pinned to 1.0 everywhere —
   a scenario that changes outputs without changing drivers is unrepresentable,
   which is the point: it kills the hockey-stick-by-assertion failure mode.

2. Sensitivity: one driver swept ±span%, one metric observed.

3. Reversal threshold: bisection for the driver value (flat models) or driver
   multiplier (projection) at which a metric crosses a threshold — "at what churn
   does LTV:CAC fall through 3?" These solved thresholds feed the
   kill-assumptions table and the pre-committed decision triggers.

For projection, multipliers apply to well-known driver families across all lines:
  price · volume · unit_variable_cost · opex · payroll
or to any scalar top-level driver by name (e.g. tax_rate_pct, dso_days).
For flat models, multipliers apply to the named tagged input.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys

from fin_common import (EXIT_UNEXPECTED, Result, Tagged, load_inputs)
from finmath import bisect_solve

MODELS = ("unit-economics", "saas", "projection")
PROJECTION_FAMILIES = {
    "price": ("activities", "price"),
    "volume": ("activities", ("volume_start", "volumes")),
    "unit_variable_cost": ("activities", "unit_variable_cost"),
    "opex": ("opex_lines", "monthly_amount"),
    "payroll": ("payroll", "monthly_gross"),
}


# ---------------------------------------------------------------------------
# Model runners — return {metric_name: scalar_value} for one payload
# ---------------------------------------------------------------------------

def _scalars(result: Result) -> dict[str, float]:
    result.finalize()
    out = {}
    for name, entry in result.results.items():
        v = entry.get("value")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out[name] = float(v)
    return out


def _run_model(model: str, payload) -> dict[str, float]:
    if model == "projection":
        from projection import project
        return _scalars(project(copy.deepcopy(payload)))
    if model == "unit-economics":
        from unit_economics import compute
        return _scalars(compute(payload))
    if model == "saas":
        from saas_metrics import compute_point_metrics
        return _scalars(compute_point_metrics(payload))
    raise ValueError(f"unknown model {model!r}")


# ---------------------------------------------------------------------------
# Driver mutation
# ---------------------------------------------------------------------------

def _scale_value(v, mult: float):
    """Scale a scalar that may be bare or tagged {value, ...}."""
    if isinstance(v, dict) and "value" in v:
        out = dict(v)
        if isinstance(out["value"], (int, float)):
            out["value"] = out["value"] * mult
        return out
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v * mult
    return v


def mutate_flat(inputs: dict[str, Tagged], driver: str, mult: float | None = None,
                absolute: float | None = None) -> dict[str, Tagged]:
    if driver not in inputs or not inputs[driver].is_known():
        raise SystemExit(
            f"driver '{driver}' is not a known input — scenario multipliers can "
            "only scale inputs that exist and are not unknown"
        )
    out = dict(inputs)
    t = inputs[driver]
    new_value = absolute if absolute is not None else float(t.value) * mult  # type: ignore[arg-type]
    out[driver] = Tagged(value=new_value, status=t.status, basis=t.basis,
                         source_url=t.source_url, confidence=t.confidence)
    return out


def mutate_projection(drivers: dict, driver: str, mult: float) -> dict:
    out = copy.deepcopy(drivers)
    if driver in PROJECTION_FAMILIES:
        list_key, field_spec = PROJECTION_FAMILIES[driver]
        fields = field_spec if isinstance(field_spec, tuple) else (field_spec,)
        for item in out.get(list_key, []):
            for f in fields:
                if f in item:
                    if isinstance(item[f], list):
                        item[f] = [_scale_value(x, mult) for x in item[f]]
                    else:
                        item[f] = _scale_value(item[f], mult)
        return out
    if driver in out:
        out[driver] = _scale_value(out[driver], mult)
        return out
    raise SystemExit(
        f"driver '{driver}' not found — projection multipliers accept "
        f"{sorted(PROJECTION_FAMILIES)} or any scalar top-level driver name. "
        f"Available top-level keys: {sorted(drivers.keys())}"
    )


def apply_multipliers(model: str, payload, multipliers: dict[str, float]):
    mutated = payload
    for driver, mult in multipliers.items():
        if not isinstance(mult, (int, float)) or isinstance(mult, bool):
            raise SystemExit(f"multiplier for '{driver}' must be a number, got {mult!r}")
        if model == "projection":
            mutated = mutate_projection(mutated, driver, float(mult))
        else:
            mutated = mutate_flat(mutated, driver, mult=float(mult))
    return mutated


# ---------------------------------------------------------------------------
# Analyses
# ---------------------------------------------------------------------------

def run_scenarios(model: str, payload, scenarios: dict[str, dict[str, float]],
                  result: Result) -> None:
    if "base" not in scenarios:
        scenarios = {"base": {}, **scenarios}
    bad = {d: m for d, m in scenarios["base"].items() if float(m) != 1.0}
    if bad:
        raise SystemExit(
            f"the base scenario must keep every multiplier at 1.0 (got {bad}). "
            "Scenarios express deviation from base — they never restate outputs."
        )
    rows = []
    for name, mults in scenarios.items():
        metrics = _run_model(model, apply_multipliers(model, payload, mults))
        rows.append({"scenario": name, "multipliers": mults, **metrics})
    result.add_table(
        "scenario_comparison", rows,
        "each scenario = base drivers × multipliers, all outputs recomputed",
    )


def run_sensitivity(model: str, payload, driver: str, span_pct: float, steps: int,
                    metric: str, result: Result) -> None:
    if steps < 3:
        raise SystemExit("--steps must be >= 3")
    span = span_pct / 100.0
    rows = []
    for i in range(steps):
        mult = (1 - span) + (2 * span) * i / (steps - 1)
        metrics = _run_model(
            model, apply_multipliers(model, payload, {driver: mult}))
        rows.append({
            "multiplier": round(mult, 4),
            metric: metrics.get(metric),
        })
    if all(r[metric] is None for r in rows):
        result.skip(f"sensitivity:{metric}",
                    f"metric '{metric}' was never computed across the sweep — "
                    "check the metric name against the model's results")
        return
    result.add_table(
        "sensitivity", rows,
        f"{driver} swept ±{span_pct}% around base, observing {metric}",
    )


def run_reversal(model: str, payload, driver: str, metric: str, threshold: float,
                 lo: float | None, hi: float | None, result: Result) -> None:
    if model == "projection":
        current: float | None = 1.0
        lo = 0.05 if lo is None else lo
        hi = 5.0 if hi is None else hi

        def f(x: float) -> float | None:
            return _run_model(
                model, mutate_projection(payload, driver, x)).get(metric)
        unit = "multiplier"
    else:
        t = payload.get(driver)
        if t is None or not t.is_known():
            raise SystemExit(f"driver '{driver}' is unknown — cannot solve a "
                             "reversal on an input that has no current value")
        current = float(t.value)
        if lo is None or hi is None:
            if current <= 0:
                raise SystemExit("driver's current value is <= 0 — pass explicit "
                                 "--lo and --hi bounds for the search")
            lo = current * 0.02 if lo is None else lo
            hi = current * 20.0 if hi is None else hi

        def f(x: float) -> float | None:
            return _run_model(
                model, mutate_flat(payload, driver, absolute=x)).get(metric)
        unit = "absolute value"

    base_metric = f(current)
    if base_metric is None:
        result.skip(f"reversal:{driver}",
                    f"metric '{metric}' is not computable at the current inputs — "
                    "fill its required inputs first")
        return

    crossing = bisect_solve(f, threshold, lo, hi)
    result.add("base_" + metric, base_metric,
               f"{metric} at current {driver}", [driver])
    if crossing is None:
        result.skip(
            f"reversal:{driver}",
            f"{metric} does not cross {threshold} for {driver} in "
            f"[{lo:g}, {hi:g}] ({unit}) — the verdict does not flip inside the "
            "searched range, which is itself a finding (or widen --lo/--hi)",
        )
        return
    headroom = ((crossing - current) / current * 100.0) if current else None
    result.add("reversal_value", crossing,
               f"bisection: {driver} where {metric} crosses {threshold}",
               [driver], unit=unit)
    if headroom is not None:
        result.add("headroom_pct", headroom,
                   "(reversal_value - current) / current × 100", [driver])
    result.add("reversal_threshold_crossed_at", threshold,
               "threshold requested", [])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(
        prog="scenarios",
        description="Driver-multiplier scenarios, sensitivity sweeps, and "
                    "reversal-threshold solving over the skill's models.")
    p.add_argument("--model", required=True, choices=MODELS)
    p.add_argument("--inputs", help="inline tagged JSON (flat models)")
    p.add_argument("--inputs-file", help="tagged JSON file (flat models)")
    p.add_argument("--drivers-file", help="projection drivers JSON file")
    p.add_argument("--scenarios-file",
                   help='JSON file: {"conservative": {"volume": 0.7}, ...}')
    p.add_argument("--sensitivity", metavar="DRIVER")
    p.add_argument("--span", type=float, default=30.0,
                   help="sensitivity sweep half-width in pct (default 30)")
    p.add_argument("--steps", type=int, default=7)
    p.add_argument("--reversal", metavar="DRIVER")
    p.add_argument("--metric", help="metric name for sensitivity/reversal")
    p.add_argument("--threshold", type=float)
    p.add_argument("--direction", choices=("above", "below"),
                   help="side on which the verdict flips (annotation only)")
    p.add_argument("--lo", type=float)
    p.add_argument("--hi", type=float)
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args()

    modes = [bool(args.scenarios_file), bool(args.sensitivity), bool(args.reversal)]
    if sum(modes) != 1:
        raise SystemExit("pick exactly one mode: --scenarios-file, "
                         "--sensitivity, or --reversal")

    warnings: list[str] = []
    if args.model == "projection":
        if not args.drivers_file:
            raise SystemExit("--model projection requires --drivers-file")
        with open(args.drivers_file, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    else:
        src = args.inputs or args.inputs_file
        if not src:
            raise SystemExit(f"--model {args.model} requires --inputs or --inputs-file")
        payload = load_inputs(src, warnings)

    result = Result(script="scenarios")
    if args.model != "projection":
        result.echo_inputs(payload)

    try:
        if args.scenarios_file:
            with open(args.scenarios_file, "r", encoding="utf-8") as fh:
                scenarios = json.load(fh)
            run_scenarios(args.model, payload, scenarios, result)
        elif args.sensitivity:
            if not args.metric:
                raise SystemExit("--sensitivity requires --metric")
            run_sensitivity(args.model, payload, args.sensitivity, args.span,
                            args.steps, args.metric, result)
        else:
            if not args.metric or args.threshold is None:
                raise SystemExit("--reversal requires --metric and --threshold")
            run_reversal(args.model, payload, args.reversal, args.metric,
                         args.threshold, args.lo, args.hi, result)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        print(f"[scenarios] unexpected error: {e}", file=sys.stderr)
        sys.exit(EXIT_UNEXPECTED)

    for w in warnings:
        result.warn(w)
    code = result.finalize()
    result.emit(args.as_json)
    sys.exit(code)


if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
else:
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
