"""opsfinance — operational finance for support/CS/ops teams and PMOs.

Six calculators behind one CLI with subcommands:

  unit-cost      fully-loaded cost per driver unit (ticket, project, order)
                 from a category cost pool, or a monthly trend from files
  cost-to-serve  which segments consume the cost base, vs their revenue
  capacity       deterministic FTE sizing from demand, AHT, shrinkage,
                 occupancy (Erlang-lite — averages, not intra-day SLAs)
  headcount      monthly FTE + cost plan from a demand file
  roi            NPV / IRR / payback for an initiative business case
  variance       budget vs actual with materiality classing

Why subcommands instead of fin_common.cli: these are six small models that
share almost no inputs, and scenarios.py needs to re-run each one with
modified drivers — so each model is exposed as a pure importable function
(`unit_cost`, `capacity_plan`, `initiative_roi`, ...) that takes Tagged
inputs (or plain row dicts for file-backed models) and returns an
un-finalized Result. The CLI is a thin dispatch layer that keeps the
fin_common discipline: finalize() -> emit() -> sys.exit(code).

Everything follows the fin_common contract: guarded formulas (never
Infinity/NaN/magic defaults), partial results with a prioritized `missing`
agenda, INSUFFICIENT_DATA when nothing meaningful is computable.
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Optional

import finmath
from fin_common import (
    EXIT_UNEXPECTED,
    Result,
    Tagged,
    gather_inputs,
    guard,
    load_table,
    num,
)

LABOR_KEYS = ("salar", "labor", "payroll")
OVERHEAD_KEYS = ("overhead", "alloc")
ERLANG_WARNING = (
    "deterministic average-based model (Erlang-lite) — for strict intra-day "
    "SLAs use an Erlang C calculation"
)


# ---------------------------------------------------------------------------
# Small conversions — file cells and pool entries arrive as anything
# ---------------------------------------------------------------------------

def _fnum(x: object) -> Optional[float]:
    """Float or None — NaN/Inf collapse to None so they can never leak into
    a formula and defeat the guards downstream."""
    if x is None:
        return None
    try:
        v = float(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return v


def _str_input(inputs: dict[str, Tagged], name: str,
               default: Optional[str] = None) -> Optional[str]:
    t = inputs.get(name)
    if t is None or not t.is_known():
        return default
    return str(t.value)


def _records(df) -> list[dict]:
    return df.to_dict("records")


# ---------------------------------------------------------------------------
# unit-cost — pool mode
# ---------------------------------------------------------------------------

def _parse_pool(raw: dict, result: Result) -> dict[str, float]:
    """Flatten a category -> amount map where each amount may be a bare
    number or a full Tagged dict — provenance of individual pool lines is
    kept in inputs_echo, only the numbers are needed here."""
    pool: dict[str, float] = {}
    for cat, v in raw.items():
        if isinstance(v, dict) and "value" in v:
            v = v.get("value")
        amt = _fnum(v)
        if amt is None:
            result.warn(f"cost_pool category '{cat}' has a non-numeric amount — ignored")
            continue
        pool[str(cat)] = amt
    return pool


def unit_cost(inputs: dict[str, Tagged]) -> Result:
    """Fully-loaded cost per driver unit. Pure: scenarios.py re-runs this
    with a modified cost_pool or driver_volume. Caller finalizes."""
    result = Result(script="opsfinance:unit-cost")
    driver_name = _str_input(inputs, "driver_name", "unit")
    if "driver_name" not in inputs:
        result.warn("driver_name not provided — reporting cost per 'unit'")

    pool_t = inputs.get("cost_pool")
    pool: dict[str, float] = {}
    if pool_t is None or not pool_t.is_known() or not isinstance(pool_t.value, dict):
        result.need("cost_pool",
                    "category -> amount map is the numerator of unit cost", 1)
    else:
        pool = _parse_pool(pool_t.value, result)
        if not pool:
            result.need("cost_pool", "cost_pool contained no numeric amounts", 1)

    volume = num(inputs, "driver_volume")
    if pool:
        total = sum(pool.values())
        result.add("pool_total", total, "sum(cost_pool amounts)",
                   ["cost_pool"], unit="currency")
        rows = []
        for cat, amt in sorted(pool.items(), key=lambda kv: kv[1], reverse=True):
            pct = round(amt / total * 100, 2) if total > 0 else None
            rows.append({"category": cat, "amount": amt, "pct_of_pool": pct})
        result.add_table("pool_breakdown", rows, "amount / pool_total * 100")
        if total <= 0:
            result.skip("pct_of_pool",
                        f"pool_total is not positive ({total}) — shares undefined")

        lowered = [c.lower() for c in pool]
        if not any(k in c for c in lowered for k in LABOR_KEYS):
            result.warn("cost pool has no labor line — fully-loaded cost is understated")
        if not any(k in c for c in lowered for k in OVERHEAD_KEYS):
            result.warn("no overhead allocation — marginal cost only")

        if volume is None:
            result.need("driver_volume",
                        f"denominator: how many {driver_name}s the pool served", 1)
        elif guard(result, "unit_cost", volume > 0,
                   f"driver_volume must be > 0 (got {volume}) — "
                   f"cost per {driver_name} undefined"):
            result.add("unit_cost", total / volume, "pool_total / driver_volume",
                       ["cost_pool", "driver_volume"], unit=f"per {driver_name}")
    elif volume is None:
        result.need("driver_volume", "denominator for unit cost", 1)

    result.echo_inputs(inputs)
    return result


# ---------------------------------------------------------------------------
# unit-cost — trend mode (monthly files)
# ---------------------------------------------------------------------------

def unit_cost_trend(cost_rows: list[dict],
                    volume_rows: Optional[list[dict]] = None) -> Result:
    """Monthly unit-cost trend from (month, cost_category, amount) and
    (month, volume) rows. Rows are plain dicts so callers never need pandas."""
    result = Result(script="opsfinance:unit-cost-trend")

    pools: dict[str, float] = {}
    for r in cost_rows:
        amt = _fnum(r.get("amount"))
        if amt is None:
            result.warn(f"costs row for month '{r.get('month')}' has a "
                        "non-numeric amount — ignored")
            continue
        month = str(r.get("month"))
        pools[month] = pools.get(month, 0.0) + amt
    if not pools:
        result.need("costs_file",
                    "no usable (month, amount) rows — nothing to trend", 1)
        return result

    vols: dict[str, float] = {}
    for r in volume_rows or []:
        v = _fnum(r.get("volume"))
        if v is not None:
            month = str(r.get("month"))
            vols[month] = vols.get(month, 0.0) + v

    rows: list[dict] = []
    prev_uc: Optional[float] = None
    zero_vol_months: list[str] = []
    no_vol_months: list[str] = []
    for month in sorted(pools):
        pool = pools[month]
        vol = vols.get(month)
        uc: Optional[float] = None
        if vol is None:
            no_vol_months.append(month)
        elif vol > 0:
            uc = round(pool / vol, 6)
        else:
            zero_vol_months.append(month)
        mom = None
        if uc is not None and prev_uc is not None and prev_uc != 0:
            mom = round((uc - prev_uc) / abs(prev_uc) * 100, 2)
        rows.append({"month": month, "pool_total": round(pool, 2),
                     "volume": vol, "unit_cost": uc, "mom_change_pct": mom})
        if uc is not None:
            prev_uc = uc
    result.add_table(
        "unit_cost_trend", rows,
        "pool_total / volume per month; MoM % vs previous computed month")

    if not vols:
        result.need("volume_file",
                    "monthly driver volumes are the denominator of the trend", 1)
        result.skip("unit_cost", "no volume data — trend shows pool totals only",
                    needed=["volume_file"])
    else:
        if no_vol_months:
            result.warn("no volume for month(s) "
                        f"{no_vol_months} — unit cost left blank there")
        extra = sorted(set(vols) - set(pools))
        if extra:
            result.warn(f"volume file has month(s) {extra} with no cost rows — ignored")
    if zero_vol_months:
        result.skip("unit_cost",
                    f"volume is 0 for month(s) {zero_vol_months} — unit cost undefined")

    ucs = [r["unit_cost"] for r in rows if r["unit_cost"] is not None]
    if ucs:
        result.add("avg_unit_cost", sum(ucs) / len(ucs),
                   "mean(unit_cost over months with volume)",
                   ["costs_file", "volume_file"], unit="per unit")
        if len(ucs) >= 2 and ucs[0] > 0:
            change = (ucs[-1] - ucs[0]) / ucs[0]
            direction = ("rising" if change > 0.01
                         else "falling" if change < -0.01 else "flat")
            result.add("trend_direction", direction,
                       "last vs first computed unit_cost, ±1% deadband",
                       ["costs_file", "volume_file"])
        else:
            result.skip("trend_direction",
                        "need at least 2 months with a positive computed unit cost")
    return result


# ---------------------------------------------------------------------------
# cost-to-serve
# ---------------------------------------------------------------------------

def cost_to_serve(rows: list[dict]) -> Result:
    """Segment-level cost concentration from (segment, cost[, revenue]) rows.
    Duplicate segment rows are summed — files often arrive un-aggregated."""
    result = Result(script="opsfinance:cost-to-serve")

    agg: dict[str, dict] = {}
    has_revenue_col = any("revenue" in r for r in rows)
    for r in rows:
        cost = _fnum(r.get("cost"))
        if cost is None:
            result.warn(f"row for segment '{r.get('segment')}' has a "
                        "non-numeric cost — ignored")
            continue
        seg = str(r.get("segment"))
        e = agg.setdefault(seg, {"cost": 0.0, "revenue": None})
        e["cost"] += cost
        rev = _fnum(r.get("revenue"))
        if rev is not None:
            e["revenue"] = (e["revenue"] or 0.0) + rev
    if not agg:
        result.need("file", "no usable (segment, cost) rows", 1)
        return result

    total = sum(e["cost"] for e in agg.values())
    out_rows: list[dict] = []
    no_revenue_segments: list[str] = []
    for seg, e in sorted(agg.items(), key=lambda kv: kv[1]["cost"], reverse=True):
        share = round(e["cost"] / total * 100, 2) if total > 0 else None
        rev = e["revenue"]
        if rev is not None and rev > 0:
            cpr = round(e["cost"] / rev * 100, 2)
        else:
            cpr = None
            no_revenue_segments.append(seg)
        out_rows.append({"segment": seg, "cost": round(e["cost"], 2),
                         "cost_share_pct": share, "revenue": rev,
                         "cost_pct_of_revenue": cpr})
    result.add_table("cost_to_serve", out_rows,
                     "cost / total_cost * 100; cost / revenue * 100; sorted by cost desc")

    result.add("total_cost", total, "sum(cost)", ["file"], unit="currency")
    top = out_rows[0]
    result.add("top_segment", top["segment"], "segment with the largest cost", ["file"])
    if top["cost_share_pct"] is not None:
        result.add("top_segment_share_pct", top["cost_share_pct"],
                   "top segment cost / total_cost * 100", ["file"], unit="%")
    else:
        result.skip("top_segment_share_pct",
                    f"total cost is not positive ({total}) — shares undefined")

    if not has_revenue_col:
        result.skip("cost_pct_of_revenue", "no revenue column in the file",
                    needed=["revenue"])
        result.need("revenue",
                    "segment revenue turns cost concentration into profitability", 3)
    elif no_revenue_segments:
        result.skip("cost_pct_of_revenue",
                    "revenue missing or non-positive for segment(s): "
                    f"{no_revenue_segments}")
    return result


# ---------------------------------------------------------------------------
# capacity / headcount
# ---------------------------------------------------------------------------

def _effective_hours(inputs: dict[str, Tagged], result: Result) -> Optional[float]:
    """Productive hours one FTE delivers per month. Injects the 160h default
    as a *tagged assumption* so the echo never hides where it came from."""
    hours = num(inputs, "hours_per_fte_month")
    if hours is None:
        hours = 160.0
        inputs["hours_per_fte_month"] = Tagged(
            160, "assumption",
            basis="default: ~160 paid hours per FTE-month (full-time)")
        result.warn("hours_per_fte_month not provided — assuming 160 "
                    "(tagged assumption)")
    shrinkage = num(inputs, "shrinkage_pct")
    occupancy = num(inputs, "occupancy_target")
    if shrinkage is None:
        result.need("shrinkage_pct",
                    "PTO/training/meetings share (0-1) — without it FTE "
                    "capacity is overstated", 1)
    if occupancy is None:
        result.need("occupancy_target",
                    "sustainable busy share (0-1) — planning at 100% "
                    "occupancy burns the team", 1)
    if shrinkage is None or occupancy is None:
        return None
    if not guard(result, "effective_hours_per_fte", hours > 0,
                 f"hours_per_fte_month must be > 0 (got {hours})"):
        return None
    if not guard(result, "effective_hours_per_fte", 0 <= shrinkage < 1,
                 f"shrinkage_pct must be in [0, 1) (got {shrinkage})"):
        return None
    if not guard(result, "effective_hours_per_fte", 0 < occupancy <= 1,
                 f"occupancy_target must be in (0, 1] (got {occupancy})"):
        return None
    return hours * (1 - shrinkage) * occupancy


def capacity_plan(inputs: dict[str, Tagged]) -> Result:
    """Average-based FTE requirement. Pure: scenarios.py re-runs this with
    modified demand/AHT/shrinkage drivers. Caller finalizes."""
    result = Result(script="opsfinance:capacity")

    demand = num(inputs, "demand_volume_monthly")
    aht = num(inputs, "aht_minutes")
    if demand is None:
        result.need("demand_volume_monthly",
                    "monthly demand is the workload numerator", 1)
    if aht is None:
        result.need("aht_minutes",
                    "average handle time converts volume into hours of work", 1)

    workload = None
    if demand is not None and aht is not None and guard(
            result, "workload_hours", demand >= 0 and aht > 0,
            f"needs demand >= 0 and aht > 0 (got demand={demand}, aht={aht})"):
        workload = demand * aht / 60.0
        result.add("workload_hours", workload,
                   "demand_volume_monthly * aht_minutes / 60",
                   ["demand_volume_monthly", "aht_minutes"], unit="hours/month")

    effective = _effective_hours(inputs, result)
    if effective is not None:
        result.add("effective_hours_per_fte", effective,
                   "hours_per_fte_month * (1 - shrinkage_pct) * occupancy_target",
                   ["hours_per_fte_month", "shrinkage_pct", "occupancy_target"],
                   unit="hours/month")

    buffer = num(inputs, "service_buffer_pct")
    if buffer is None:
        buffer = 0.0
    if workload is not None and effective is not None and effective > 0:
        raw = workload / effective
        result.add("required_fte_raw", raw,
                   "workload_hours / effective_hours_per_fte",
                   ["demand_volume_monthly", "aht_minutes",
                    "hours_per_fte_month", "shrinkage_pct", "occupancy_target"],
                   unit="FTE")
        if guard(result, "required_fte_buffered", buffer >= 0,
                 f"service_buffer_pct must be >= 0 (got {buffer})"):
            result.add("required_fte_buffered", raw * (1 + buffer),
                       "required_fte_raw * (1 + service_buffer_pct)",
                       ["service_buffer_pct"], unit="FTE")

    result.warn(ERLANG_WARNING)
    result.echo_inputs(inputs)
    return result


def headcount_plan(inputs: dict[str, Tagged],
                   demand_rows: list[dict]) -> Result:
    """Monthly FTE and cost plan from (month, volume) rows plus capacity
    drivers. FTEs are ceil'd per month — you hire whole people."""
    result = Result(script="opsfinance:headcount")

    months: dict[str, float] = {}
    for r in demand_rows:
        vol = _fnum(r.get("volume"))
        if vol is None:
            result.warn(f"demand row for month '{r.get('month')}' has a "
                        "non-numeric volume — ignored")
            continue
        month = str(r.get("month"))
        months[month] = months.get(month, 0.0) + vol
    if not months:
        result.need("demand_file", "no usable (month, volume) rows", 1)
        result.echo_inputs(inputs)
        return result

    aht = num(inputs, "aht_minutes")
    if aht is None:
        result.need("aht_minutes",
                    "average handle time converts volume into hours of work", 1)
    effective = _effective_hours(inputs, result)
    buffer = num(inputs, "service_buffer_pct")
    if buffer is None:
        buffer = 0.0
    loaded_cost = num(inputs, "loaded_monthly_cost_per_fte")
    if loaded_cost is None:
        result.need("loaded_monthly_cost_per_fte",
                    "converts the FTE plan into a budget line", 2)
        result.skip("total_cost", "loaded_monthly_cost_per_fte missing",
                    needed=["loaded_monthly_cost_per_fte"])

    if aht is None or effective is None:
        result.skip("headcount_plan",
                    "cannot size FTEs without aht_minutes and effective hours "
                    "per FTE", needed=["aht_minutes", "shrinkage_pct",
                                      "occupancy_target"])
        result.echo_inputs(inputs)
        return result
    if not guard(result, "headcount_plan", aht > 0,
                 f"aht_minutes must be > 0 (got {aht})"):
        result.echo_inputs(inputs)
        return result
    if not guard(result, "headcount_plan", buffer >= 0,
                 f"service_buffer_pct must be >= 0 (got {buffer})"):
        result.echo_inputs(inputs)
        return result
    if effective <= 0:
        result.skip("headcount_plan", "effective hours per FTE must be > 0")
        result.echo_inputs(inputs)
        return result

    rows: list[dict] = []
    for month in sorted(months):
        vol = months[month]
        fte = math.ceil((vol * aht / 60.0) / effective * (1 + buffer))
        cost = round(fte * loaded_cost, 2) if loaded_cost is not None else None
        rows.append({"month": month, "volume": vol,
                     "required_fte": fte, "cost": cost})
    result.add_table(
        "headcount_plan", rows,
        "ceil(volume * aht / 60 / effective_hours * (1 + buffer)); "
        "cost = required_fte * loaded_monthly_cost_per_fte")

    ftes = [r["required_fte"] for r in rows]
    result.add("peak_fte", max(ftes), "max(required_fte)",
               ["demand_file", "aht_minutes"], unit="FTE")
    result.add("avg_fte", sum(ftes) / len(ftes), "mean(required_fte)",
               ["demand_file", "aht_minutes"], unit="FTE")
    if loaded_cost is not None:
        result.add("total_cost", sum(r["cost"] for r in rows),
                   "sum(required_fte * loaded_monthly_cost_per_fte)",
                   ["demand_file", "loaded_monthly_cost_per_fte"],
                   unit="currency")

    result.warn(ERLANG_WARNING)
    result.echo_inputs(inputs)
    return result


# ---------------------------------------------------------------------------
# roi
# ---------------------------------------------------------------------------

def initiative_roi(inputs: dict[str, Tagged]) -> Result:
    """NPV / IRR / payback for one initiative. Pure: scenarios.py re-runs
    this with modified benefits or investment. Caller finalizes."""
    result = Result(script="opsfinance:roi")

    investment = num(inputs, "investment")
    if investment is None:
        result.need("investment",
                    "t=0 cash out anchors NPV, IRR, and payback", 1)

    benefits: Optional[list[float]] = None
    series_t = inputs.get("benefit_series")
    monthly_benefit = num(inputs, "monthly_benefit")
    if series_t is not None and series_t.is_known():
        if isinstance(series_t.value, (list, tuple)) and series_t.value:
            vals = [_fnum(x) for x in series_t.value]
            if any(v is None for v in vals):
                result.skip("cashflows",
                            "benefit_series contains non-numeric entries")
            else:
                benefits = [v for v in vals if v is not None]
                if monthly_benefit is not None:
                    result.warn("both benefit_series and monthly_benefit "
                                "provided — using benefit_series")
        else:
            result.skip("cashflows",
                        "benefit_series must be a non-empty list of monthly amounts")
    elif monthly_benefit is not None:
        horizon = num(inputs, "horizon_months")
        if horizon is None:
            horizon = 24.0
            inputs["horizon_months"] = Tagged(
                24, "assumption", basis="default: 24-month evaluation horizon")
            result.warn("horizon_months not provided — assuming 24 "
                        "(tagged assumption)")
        if guard(result, "cashflows", horizon >= 1,
                 f"horizon_months must be >= 1 (got {horizon})"):
            benefits = [monthly_benefit] * int(horizon)
    else:
        result.need("monthly_benefit",
                    "recurring monthly benefit (or benefit_series) drives "
                    "every ROI metric", 1)

    monthly_cost = num(inputs, "monthly_cost")
    if monthly_cost is None:
        monthly_cost = 0.0

    if any(inputs.get(k) is not None and inputs[k].status == "assumption"
           for k in ("monthly_benefit", "benefit_series")):
        result.warn("benefits are assumptions until measured — attach "
                    "measurement plan")

    if investment is not None and benefits is not None and guard(
            result, "cashflows", investment > 0,
            f"investment must be > 0 (got {investment}) — it is the t=0 "
            "cash outflow"):
        cashflows = [-investment] + [b - monthly_cost for b in benefits]
        n = len(benefits)
        result.add("total_net_benefit", sum(cashflows),
                   f"sum(benefit - monthly_cost over {n} months) - investment",
                   ["investment", "monthly_benefit", "monthly_cost"],
                   unit="currency")

        rate_annual = num(inputs, "discount_rate_annual")
        if rate_annual is None:
            result.skip("npv", "discount_rate_annual missing",
                        needed=["discount_rate_annual"])
            result.need("discount_rate_annual",
                        "discounting turns future benefits into a defensible "
                        "NPV", 2)
        elif guard(result, "npv", rate_annual > -1,
                   f"discount_rate_annual must be > -1 (got {rate_annual})"):
            rate_monthly = (1 + rate_annual) ** (1 / 12) - 1
            v = finmath.npv(rate_monthly, cashflows)
            if v is not None:
                result.add("npv", v,
                           "NPV(cashflows) at monthly rate "
                           "(1 + discount_rate_annual)^(1/12) - 1",
                           ["investment", "monthly_benefit", "monthly_cost",
                            "discount_rate_annual"], unit="currency")

        irr_monthly = finmath.irr(cashflows)
        if irr_monthly is None:
            result.skip("irr_annualized_pct",
                        "IRR undefined for these cashflows — no sign change "
                        "(net benefits never recover the investment, or "
                        "vice versa)")
        else:
            result.add("irr_monthly", irr_monthly,
                       "rate where NPV(cashflows) = 0 (bisection)",
                       ["investment", "monthly_benefit", "monthly_cost"])
            result.add("irr_annualized_pct",
                       ((1 + irr_monthly) ** 12 - 1) * 100,
                       "((1 + irr_monthly)^12 - 1) * 100",
                       ["investment", "monthly_benefit", "monthly_cost"],
                       unit="%")

        payback = finmath.payback_period(cashflows)
        if payback is None:
            result.skip("payback_months",
                        f"never pays back within the {n}-month horizon")
        else:
            result.add("payback_months", payback,
                       "months until cumulative cashflow crosses zero "
                       "(interpolated)",
                       ["investment", "monthly_benefit", "monthly_cost"],
                       unit="months")

    result.echo_inputs(inputs)
    return result


# ---------------------------------------------------------------------------
# variance
# ---------------------------------------------------------------------------

def _variance_class(abs_pct: float) -> str:
    """Materiality bands calibrated to reporting effort: how much narrative
    a line deserves in the monthly review."""
    if abs_pct < 5:
        return "note"
    if abs_pct < 10:
        return "line"
    if abs_pct <= 20:
        return "paragraph"
    return "escalate"


def variance_report(rows: list[dict]) -> Result:
    """Budget vs actual from (period, category, budget, actual[, type]) rows.
    Favorability depends on line type: underspend is good, under-revenue is
    not — a plain actual-budget sign would misread half the lines."""
    result = Result(script="opsfinance:variance")

    out: list[dict] = []
    zero_budget_lines: list[str] = []
    total_budget = 0.0
    total_actual = 0.0
    for r in rows:
        budget = _fnum(r.get("budget"))
        actual = _fnum(r.get("actual"))
        period = str(r.get("period"))
        category = str(r.get("category"))
        if budget is None or actual is None:
            result.warn(f"line '{category}' ({period}) has non-numeric "
                        "budget/actual — ignored")
            continue
        raw_type = r.get("type")
        line_type = str(raw_type).strip().lower() if raw_type is not None else "cost"
        if line_type in ("", "nan", "none"):
            line_type = "cost"
        elif line_type not in ("cost", "revenue"):
            result.warn(f"unknown type '{line_type}' for '{category}' "
                        f"({period}) — treated as cost")
            line_type = "cost"

        variance_abs = actual - budget
        if budget != 0:
            variance_pct: Optional[float] = round(
                variance_abs / abs(budget) * 100, 2)
            cls = _variance_class(abs(variance_pct))
        else:
            variance_pct = None
            zero_budget_lines.append(f"{category}/{period}")
            cls = "escalate" if actual != 0 else "note"
        favorable = (actual <= budget) if line_type == "cost" else (actual >= budget)
        out.append({"period": period, "category": category, "type": line_type,
                    "budget": budget, "actual": actual,
                    "variance_abs": round(variance_abs, 2),
                    "variance_pct": variance_pct, "favorable": favorable,
                    "variance_class": cls})
        total_budget += budget
        total_actual += actual

    if not out:
        result.need("file", "no usable (period, category, budget, actual) rows", 1)
        return result

    result.add_table(
        "variance_table", out,
        "variance = actual - budget; favorable by line type; class by "
        "|variance_pct| bands <5 note / 5-10 line / 10-20 paragraph / "
        ">20 escalate")
    result.add("total_budget", total_budget, "sum(budget)", ["file"],
               unit="currency")
    result.add("total_actual", total_actual, "sum(actual)", ["file"],
               unit="currency")
    if guard(result, "total_variance_pct", total_budget != 0,
             "total budget is 0 — aggregate percent undefined"):
        result.add("total_variance_pct",
                   (total_actual - total_budget) / abs(total_budget) * 100,
                   "(total_actual - total_budget) / |total_budget| * 100",
                   ["file"], unit="%")
    if zero_budget_lines:
        result.skip("variance_pct",
                    f"budget is 0 for line(s) {zero_budget_lines} — percent "
                    "undefined (classed escalate when actual != 0)")

    unfavorable = [r for r in out if not r["favorable"]]
    if not unfavorable:
        result.skip("worst_line", "no unfavorable variance lines")
    else:
        with_pct = [r for r in unfavorable if r["variance_pct"] is not None]
        if with_pct:
            worst = max(with_pct, key=lambda r: abs(r["variance_pct"]))
        else:
            worst = max(unfavorable, key=lambda r: abs(r["variance_abs"]))
        result.add("worst_line",
                   {"period": worst["period"], "category": worst["category"],
                    "variance_abs": worst["variance_abs"],
                    "variance_pct": worst["variance_pct"]},
                   "unfavorable line with the largest |variance_pct| "
                   "(fallback: largest |variance_abs|)", ["file"])
    return result


# ---------------------------------------------------------------------------
# CLI — subcommand dispatch with the fin_common exit discipline
# ---------------------------------------------------------------------------

def _add_common(p: argparse.ArgumentParser, with_inputs: bool = True) -> None:
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="emit machine-readable JSON to stdout")
    if with_inputs:
        p.add_argument("--inputs", help="inline JSON object of tagged inputs")
        p.add_argument("--inputs-file", dest="inputs_file",
                       help="path to JSON file of tagged inputs")


def _run_unit_cost(args, warnings: list[str]) -> Result:
    if args.volume_file and not args.costs_file:
        raise SystemExit("--volume-file requires --costs-file")
    if args.costs_file:
        cost_rows = _records(
            load_table(args.costs_file, ["month", "cost_category", "amount"]))
        volume_rows = None
        if args.volume_file:
            volume_rows = _records(
                load_table(args.volume_file, ["month", "volume"]))
        return unit_cost_trend(cost_rows, volume_rows)
    return unit_cost(gather_inputs(args, warnings))


def _run_cost_to_serve(args, warnings: list[str]) -> Result:
    return cost_to_serve(_records(load_table(args.file, ["segment", "cost"])))


def _run_capacity(args, warnings: list[str]) -> Result:
    return capacity_plan(gather_inputs(args, warnings))


def _run_headcount(args, warnings: list[str]) -> Result:
    demand_rows = _records(load_table(args.demand_file, ["month", "volume"]))
    return headcount_plan(gather_inputs(args, warnings), demand_rows)


def _run_roi(args, warnings: list[str]) -> Result:
    return initiative_roi(gather_inputs(args, warnings))


def _run_variance(args, warnings: list[str]) -> Result:
    return variance_report(_records(
        load_table(args.file, ["period", "category", "budget", "actual"])))


HANDLERS = {
    "unit-cost": _run_unit_cost,
    "cost-to-serve": _run_cost_to_serve,
    "capacity": _run_capacity,
    "headcount": _run_headcount,
    "roi": _run_roi,
    "variance": _run_variance,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opsfinance",
        description="Operational finance: unit costs, cost-to-serve, "
                    "capacity sizing, headcount planning, initiative ROI, "
                    "budget variance.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("unit-cost",
                       help="fully-loaded cost per driver unit from a cost "
                            "pool, or monthly trend from files")
    _add_common(p)
    p.add_argument("--costs-file", dest="costs_file",
                   help="CSV/Excel with month,cost_category,amount (trend mode)")
    p.add_argument("--volume-file", dest="volume_file",
                   help="CSV/Excel with month,volume (trend mode)")

    p = sub.add_parser("cost-to-serve",
                       help="segment cost concentration vs revenue")
    _add_common(p, with_inputs=False)
    p.add_argument("--file", required=True,
                   help="CSV/Excel with segment,cost[,revenue]")

    p = sub.add_parser("capacity",
                       help="FTE requirement from demand, AHT, shrinkage, "
                            "occupancy")
    _add_common(p)

    p = sub.add_parser("headcount",
                       help="monthly FTE + cost plan from a demand file")
    _add_common(p)
    p.add_argument("--demand-file", dest="demand_file", required=True,
                   help="CSV/Excel with month,volume")

    p = sub.add_parser("roi",
                       help="NPV / IRR / payback for an initiative")
    _add_common(p)

    p = sub.add_parser("variance",
                       help="budget vs actual with materiality classing")
    _add_common(p, with_inputs=False)
    p.add_argument("--file", required=True,
                   help="CSV/Excel with period,category,budget,actual[,type]")

    return parser


def main(argv: Optional[list[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    warnings: list[str] = []
    try:
        result = HANDLERS[args.command](args, warnings)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 — one honest crash surface
        print(f"[opsfinance {args.command}] unexpected error: {e}",
              file=sys.stderr)
        sys.exit(EXIT_UNEXPECTED)

    for w in warnings:
        result.warn(w)
    code = result.finalize()
    result.emit(args.as_json)
    sys.exit(code)


if __name__ == "__main__":
    main()
