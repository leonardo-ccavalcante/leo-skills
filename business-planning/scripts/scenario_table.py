"""scenario_table — locked 3-scenario multiplier table + fa.sh driver files.

Scenarios express deviation from base as DRIVER MULTIPLIERS — never as
restated outcomes. This module computes NO business outcome: it validates the
scenario trio, builds the assumption table, and materializes three driver
objects shaped exactly for `fa.sh projection --drivers-file`, which is where
every outcome (P&L, cash, runway, break-even) comes from. The caller (the
model) writes results.driver_files.<scenario> to
`bp_<slug>/scenarios/drivers-<scenario>.json` and runs fa.sh on each.

Inputs (tagged):
- `base_drivers` — the RAW projection driver object from
  financial-analysis/scripts/projection.py (activities / opex_lines / payroll /
  capex / loans / funding / starting_cash / tax_rate_pct / ...). Scalars inside
  it may themselves be tagged {"value":..., "status":..., "basis":...};
  projection unwraps them.
- `multipliers` — value is an object with EXACTLY the keys `conservative`,
  `base`, `optimistic`; each maps a driver name to a positive number.
  Driver names are either a projection family — price · volume ·
  unit_variable_cost · opex · payroll (mirrors PROJECTION_FAMILIES in
  financial-analysis/scripts/scenarios.py; keep in sync) — or any scalar
  top-level driver key present in base_drivers (e.g. tax_rate_pct).

Invariants (each violation => exit 3):
- the scenario set is exactly {conservative, base, optimistic};
- every `base` multiplier == 1.0 — the base scenario restates the plan, so a
  base that moves a driver is a hidden assumption change;
- every multiplier is a positive number;
- every driver name resolves (family or top-level scalar key).

A scenario omitting a driver leaves it at 1.0 (no change) — the assumption
table shows the resolved 1.0 so the omission is visible.

Usage: scenario_table.py --inputs-file <f.bp.json> [--json]
"""

from __future__ import annotations

import copy

from bp_common import Result, cli, gather_inputs

SCRIPT = "scenario_table"

SCENARIOS = ("conservative", "base", "optimistic")

# Mirrors financial-analysis/scripts/scenarios.py PROJECTION_FAMILIES.
FAMILIES = {
    "price": ("activities", ("price",)),
    "volume": ("activities", ("volume_start", "volumes")),
    "unit_variable_cost": ("activities", ("unit_variable_cost",)),
    "opex": ("opex_lines", ("monthly_amount",)),
    "payroll": ("payroll", ("monthly_gross",)),
}


def _scale_value(v, mult: float):
    """Scale a scalar that may be bare or tagged {value, ...} — same handling
    as financial-analysis scenarios.py, so what fa.sh would do to a driver and
    what we materialize into the file agree."""
    if isinstance(v, dict) and "value" in v:
        out = dict(v)
        if isinstance(out["value"], (int, float)) and \
                not isinstance(out["value"], bool):
            out["value"] = out["value"] * mult
        return out
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return v * mult
    return v


def _apply(drivers: dict, driver: str, mult: float, res: Result,
           scenario: str) -> dict:
    out = copy.deepcopy(drivers)
    if driver in FAMILIES:
        list_key, fields = FAMILIES[driver]
        items = out.get(list_key)
        touched = 0
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                for f in fields:
                    if f in item:
                        if isinstance(item[f], list):
                            item[f] = [_scale_value(x, mult) for x in item[f]]
                        else:
                            item[f] = _scale_value(item[f], mult)
                        touched += 1
        if touched == 0:
            res.warn(f"scenario '{scenario}': multiplier '{driver}' scaled "
                     f"nothing — base_drivers has no {list_key} field to apply "
                     "it to")
        return out
    out[driver] = _scale_value(out[driver], mult)
    return out


def _run(args, warnings: "list[str]") -> Result:
    res = Result(script=SCRIPT)
    inputs = gather_inputs(args, warnings)
    res.echo_inputs(inputs)

    base_tag = inputs.get("base_drivers")
    mult_tag = inputs.get("multipliers")
    have_base = base_tag is not None and base_tag.is_known() and \
        isinstance(base_tag.value, dict)
    have_mults = mult_tag is not None and mult_tag.is_known() and \
        isinstance(mult_tag.value, dict)
    if not have_base:
        if base_tag is not None and base_tag.is_known():
            res.invariant("base_drivers is an object", False,
                          "base_drivers.value must be a projection driver "
                          "object (see projection.py docstring)")
            return res
        res.need("base_drivers",
                 "the fa.sh projection driver object every scenario mutates",
                 priority=1)
    if not have_mults:
        if mult_tag is not None and mult_tag.is_known():
            res.invariant("multipliers is an object", False,
                          'multipliers.value must be {"conservative": {...}, '
                          '"base": {...}, "optimistic": {...}}')
            return res
        res.need("multipliers",
                 "per-scenario driver multipliers (base pinned at 1.0)",
                 priority=1)
    if not (have_base and have_mults):
        return res

    base_drivers: dict = base_tag.value
    mult_sets: dict = mult_tag.value

    got = set(mult_sets.keys())
    want = set(SCENARIOS)
    if got != want:
        extra = sorted(got - want)
        absent = sorted(want - got)
        detail = []
        if absent:
            detail.append(f"missing {absent}")
        if extra:
            detail.append(f"extra {extra}")
        res.invariant(
            "scenario trio locked", False,
            f"the scenario set must be exactly {sorted(want)} — "
            + "; ".join(detail),
        )
        return res

    valid_names = set(FAMILIES) | {
        k for k, v in base_drivers.items()
        if not isinstance(v, list)
    }
    ok = True
    for scenario in SCENARIOS:
        mults = mult_sets[scenario]
        if not isinstance(mults, dict):
            res.invariant(f"scenario '{scenario}' is an object", False,
                          f"got {type(mults).__name__}")
            ok = False
            continue
        for driver, m in mults.items():
            if isinstance(m, bool) or not isinstance(m, (int, float)):
                res.invariant(
                    f"multiplier {scenario}.{driver} numeric", False,
                    f"got {m!r} — multipliers are positive numbers",
                )
                ok = False
                continue
            if m <= 0:
                res.invariant(
                    f"multiplier {scenario}.{driver} positive", False,
                    f"got {m} — to remove a driver, change base_drivers, "
                    "don't zero it through a scenario",
                )
                ok = False
            if driver not in valid_names:
                res.invariant(
                    f"driver '{driver}' resolvable", False,
                    f"'{driver}' is neither a projection family "
                    f"{sorted(FAMILIES)} nor a scalar top-level key of "
                    f"base_drivers {sorted(k for k in base_drivers)}",
                )
                ok = False
            if scenario == "base" and isinstance(m, (int, float)) \
                    and float(m) != 1.0:
                res.invariant(
                    "base multipliers pinned at 1.0", False,
                    f"base.{driver} = {m} — the base scenario restates the "
                    "plan; deviations belong in conservative/optimistic",
                )
                ok = False
    if not ok:
        return res

    all_drivers = sorted({d for s in SCENARIOS for d in mult_sets[s]})
    if not all_drivers:
        res.invariant("at least one driver varied", False,
                      "no scenario names any driver — a scenario table with "
                      "no varied driver says nothing")
        return res

    table = []
    for driver in all_drivers:
        applies_to = (
            f"{FAMILIES[driver][0]}[*].{'/'.join(FAMILIES[driver][1])}"
            if driver in FAMILIES else f"top-level driver '{driver}'"
        )
        table.append({
            "driver": driver,
            "applies_to": applies_to,
            "conservative": float(mult_sets["conservative"].get(driver, 1.0)),
            "base": float(mult_sets["base"].get(driver, 1.0)),
            "optimistic": float(mult_sets["optimistic"].get(driver, 1.0)),
        })
    res.add_table(
        "assumption_table", table,
        "driver × scenario multipliers; omitted entries resolve to 1.0; "
        "outcomes come from fa.sh projection, never from this table",
    )

    driver_files: dict = {}
    for scenario in SCENARIOS:
        mutated = copy.deepcopy(base_drivers)
        for driver, m in mult_sets[scenario].items():
            if float(m) == 1.0:
                continue
            mutated = _apply(mutated, driver, float(m), res, scenario)
        driver_files[scenario] = mutated
    res.results["driver_files"] = {
        "value": driver_files,
        "status": "calculation",
        "formula": "base_drivers with each scenario's multipliers applied "
                   "(fa.sh projection --drivers-file shape)",
        "inputs_used": ["base_drivers", "multipliers"],
    }
    res.warn("write each driver_files.<scenario> to "
             "bp_<slug>/scenarios/drivers-<scenario>.json and run "
             "fa.sh projection --drivers-file on it — outcomes live there")
    return res


if __name__ == "__main__":
    cli(SCRIPT, "Locked conservative/base/optimistic multiplier table; emits "
                "fa.sh projection driver files, computes no outcomes", _run)
