"""unit_economics — startup/business unit economics.

Computes CAC, per-customer contribution, LTV (simplified), LTV:CAC,
CAC payback, and breakeven points from whatever subset of drivers is
known. Every metric is guarded: a zero denominator or missing driver
produces an honest `not_computed` entry, never Infinity or a default —
because a plausible-but-wrong LTV:CAC will be quoted in a board deck.

The gross-margin path (arpa * gross_margin_pct) and the per-unit path
(price - unit_variable_cost) are kept separate on purpose: blending them
silently would hide which margin assumption a headline metric rests on.

Importable entry point: compute(inputs) -> Result, so scenarios.py can
re-run the model with modified drivers without shelling out.
"""

from __future__ import annotations

import os
import sys

# Keep sibling imports working when this module is imported from another
# directory (scenarios.py may be run from anywhere).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import finmath
from fin_common import Result, Tagged, cli, gather_inputs, guard, num

LTV_CAVEAT = "LTV is simplified: excludes discounting, expansion, and cohort variation"


def _record_gaps(result: Result, known: dict[str, float | None]) -> None:
    """Rank every absent driver by how much analysis it unblocks.

    Priorities are fixed by field, not by what else is present, so the
    interactive layer's question order is stable across partial states.
    """
    gaps = {
        "arpa": ("monthly revenue per customer — drives contribution, LTV, and payback", 1),
        "monthly_churn_rate": ("LTV denominator — expected lifetime is 1/churn", 1),
        "sm_spend": ("CAC numerator — sales+marketing spend for the period", 1),
        "new_customers": ("CAC denominator — customers acquired in the same period", 1),
        "gross_margin_pct": ("converts revenue to contribution for LTV and payback", 2),
        "fixed_monthly_costs": ("needed for breakeven customer/unit counts", 3),
    }
    for fieldname, (why, priority) in gaps.items():
        if known.get(fieldname) is None:
            result.need(fieldname, why, priority)


def compute(inputs: dict[str, Tagged]) -> Result:
    """Compute all unit-economics metrics derivable from `inputs`."""
    result = Result(script="unit_economics")
    result.echo_inputs(inputs)

    arpa = num(inputs, "arpa")
    price = num(inputs, "price")
    uvc = num(inputs, "unit_variable_cost")
    gm = num(inputs, "gross_margin_pct")
    churn = num(inputs, "monthly_churn_rate")
    sm_spend = num(inputs, "sm_spend")
    new_customers = num(inputs, "new_customers")
    fixed = num(inputs, "fixed_monthly_costs")

    _record_gaps(result, {
        "arpa": arpa,
        "monthly_churn_rate": churn,
        "sm_spend": sm_spend,
        "new_customers": new_customers,
        "gross_margin_pct": gm,
        "fixed_monthly_costs": fixed,
    })

    if gm is not None and not 0.0 <= gm <= 1.0:
        result.warn("gross_margin_pct should be a 0-1 fraction "
                    f"(got {gm}) — a percent like 80 must be passed as 0.8")
    if churn is not None and not 0.0 <= churn <= 1.0:
        result.warn("monthly_churn_rate should be a 0-1 fraction "
                    f"(got {churn}) — a percent like 3 must be passed as 0.03")

    # --- CAC ---------------------------------------------------------------
    cac: float | None = None
    if sm_spend is not None and new_customers is not None:
        if guard(result, "cac", new_customers > 0,
                 "new_customers must be > 0 — CAC is undefined with no acquisitions",
                 ["new_customers"]):
            cac = sm_spend / new_customers
            result.add("cac", cac, "sm_spend / new_customers",
                       ["sm_spend", "new_customers"], unit="currency")
    else:
        needed = [n for n, v in (("sm_spend", sm_spend),
                                 ("new_customers", new_customers)) if v is None]
        result.skip("cac", "requires sm_spend and new_customers", needed)

    # --- Contribution per customer (gross-margin path) ---------------------
    contribution: float | None = None
    if arpa is not None and gm is not None:
        contribution = arpa * gm
        result.add("contribution_per_customer_monthly", contribution,
                   "arpa * gross_margin_pct", ["arpa", "gross_margin_pct"],
                   unit="currency/month")
    else:
        needed = [n for n, v in (("arpa", arpa),
                                 ("gross_margin_pct", gm)) if v is None]
        result.skip("contribution_per_customer_monthly",
                    "requires arpa and gross_margin_pct", needed)

    # --- Contribution margin ratio (per-unit path, else echo gm) -----------
    if price is not None and uvc is not None:
        if guard(result, "contribution_margin_ratio", price > 0,
                 "price must be > 0", ["price"]):
            result.add("contribution_margin_ratio", (price - uvc) / price,
                       "(price - unit_variable_cost) / price",
                       ["price", "unit_variable_cost"], unit="fraction")
    elif gm is not None:
        result.add("contribution_margin_ratio", gm,
                   "gross_margin_pct (echoed — no per-unit price/cost given)",
                   ["gross_margin_pct"], unit="fraction")
    else:
        result.skip("contribution_margin_ratio",
                    "requires price + unit_variable_cost, or gross_margin_pct",
                    ["price", "unit_variable_cost", "gross_margin_pct"])

    # --- LTV (simplified) --------------------------------------------------
    ltv: float | None = None
    if contribution is not None and churn is not None:
        if guard(result, "ltv", churn > 0,
                 "monthly_churn_rate must be > 0 — zero churn implies infinite lifetime",
                 ["monthly_churn_rate"]):
            ltv = contribution / churn
            result.add("ltv", ltv,
                       "arpa * gross_margin_pct / monthly_churn_rate",
                       ["arpa", "gross_margin_pct", "monthly_churn_rate"],
                       unit="currency")
            result.warn(LTV_CAVEAT)
    else:
        needed = [n for n, v in (("arpa", arpa), ("gross_margin_pct", gm),
                                 ("monthly_churn_rate", churn)) if v is None]
        result.skip("ltv", "requires arpa, gross_margin_pct, and monthly_churn_rate",
                    needed)

    # --- LTV : CAC ---------------------------------------------------------
    if ltv is not None and cac is not None:
        if guard(result, "ltv_cac_ratio", cac > 0,
                 "cac must be > 0 — zero-cost acquisition makes the ratio undefined",
                 ["sm_spend"]):
            result.add("ltv_cac_ratio", ltv / cac, "ltv / cac",
                       ["ltv", "cac"], unit="x")
    else:
        result.skip("ltv_cac_ratio",
                    "requires both ltv and cac to be computed")

    # --- CAC payback -------------------------------------------------------
    if cac is not None and contribution is not None:
        if guard(result, "cac_payback_months", contribution > 0,
                 "contribution per customer must be > 0 — CAC is never recovered otherwise",
                 ["arpa", "gross_margin_pct"]):
            result.add("cac_payback_months", cac / contribution,
                       "cac / (arpa * gross_margin_pct)",
                       ["cac", "arpa", "gross_margin_pct"], unit="months")
    else:
        result.skip("cac_payback_months",
                    "requires both cac and contribution_per_customer_monthly")

    # --- Breakeven customers (fixed-cost coverage, gross-margin path) ------
    if fixed is not None and contribution is not None:
        if guard(result, "breakeven_customers",
                 contribution > 0 and fixed >= 0,
                 "requires contribution per customer > 0 and fixed_monthly_costs >= 0",
                 ["arpa", "gross_margin_pct"]):
            result.add("breakeven_customers", fixed / contribution,
                       "fixed_monthly_costs / (arpa * gross_margin_pct)",
                       ["fixed_monthly_costs", "arpa", "gross_margin_pct"],
                       unit="customers")
    else:
        needed = ([n for n, v in (("fixed_monthly_costs", fixed),) if v is None]
                  + (["arpa", "gross_margin_pct"] if contribution is None else []))
        result.skip("breakeven_customers",
                    "requires fixed_monthly_costs and contribution per customer",
                    needed)

    # --- Breakeven units/revenue (per-unit path) ---------------------------
    # Only surfaced as a gap when the user is on the per-unit path at all:
    # a pure per-account SaaS case should not be nagged about unit price.
    if price is not None and uvc is not None:
        if fixed is None:
            result.skip("breakeven_units", "requires fixed_monthly_costs",
                        ["fixed_monthly_costs"])
        else:
            units = finmath.breakeven_units(fixed, price, uvc)
            if units is None:
                reason = ("price - unit_variable_cost must be > 0"
                          if price - uvc <= 0
                          else "fixed_monthly_costs must be >= 0")
                result.skip("breakeven_units", reason)
                result.skip("breakeven_revenue", reason)
            else:
                result.add("breakeven_units", units,
                           "fixed_monthly_costs / (price - unit_variable_cost)",
                           ["fixed_monthly_costs", "price", "unit_variable_cost"],
                           unit="units")
                result.add("breakeven_revenue", units * price,
                           "breakeven_units * price",
                           ["fixed_monthly_costs", "price", "unit_variable_cost"],
                           unit="currency")

    return result


def _run(args, warnings: list[str]) -> Result:
    inputs = gather_inputs(args, warnings)
    return compute(inputs)


if __name__ == "__main__":
    cli("unit_economics",
        "Startup unit economics: CAC, LTV, LTV:CAC, payback, and breakeven "
        "from tagged drivers (all optional — computes what it can).",
        _run)
