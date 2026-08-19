"""selftest — golden-number tests for every formula module. Stdlib only.

Run via `fa.sh selftest`. Exit 0 when all pass, 1 on any failure.

These are the numbers a reviewer can check by hand. If a refactor changes any
of them, either the refactor is wrong or the golden number must be re-derived
by hand — never adjusted to match the code.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fin_common import Tagged, parse_inputs  # noqa: E402
import finmath  # noqa: E402

PASS, FAIL = 0, 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL: {name} {detail}", file=sys.stderr)


def approx(a, b, tol=1e-4) -> bool:
    if a is None or b is None:
        return False
    return abs(a - b) <= tol * max(1.0, abs(b))


def rv(result, name):
    entry = result.results.get(name)
    return None if entry is None else entry["value"]


def skipped(result, name) -> bool:
    return any(nc["metric"] == name for nc in result.not_computed)


# ---------------------------------------------------------------------------
# finmath
# ---------------------------------------------------------------------------

def test_finmath():
    check("npv zero-rate sums", approx(finmath.npv(0.0, [-100, 60, 60]), 20.0))
    # IRR of [-100, 60, 60]: 60/(1+r) + 60/(1+r)^2 = 100 → r ≈ 0.131083
    check("irr golden", approx(finmath.irr([-100, 60, 60]), 0.131083, 1e-3))
    check("irr undefined all-positive", finmath.irr([10, 20]) is None)
    # pmt: 12k over 12 periods at 0 → -1000
    check("pmt zero-rate", approx(finmath.pmt(0.0, 12, 12000), -1000.0))
    # payback: -100 then 40/mo → crosses at 2.5 periods after t0
    check("payback interpolated",
          approx(finmath.payback_period([-100, 40, 40, 40]), 2.5))
    check("payback never", finmath.payback_period([-100, 10]) is None)
    check("breakeven units", approx(finmath.breakeven_units(1000, 30, 10), 50.0))
    check("breakeven undefined", finmath.breakeven_units(1000, 10, 30) is None)
    check("cagr golden", approx(finmath.cagr(100, 200, 2), 0.414213, 1e-4))
    check("bisect linear", approx(
        finmath.bisect_solve(lambda x: 2 * x, 10.0, 0.0, 100.0), 5.0))
    sched = finmath.amortization_schedule(12000, 0.12, 12)
    check("amortization closes", sched is not None and approx(sched[-1]["balance"], 0.0, 1e-2))


# ---------------------------------------------------------------------------
# unit_economics
# ---------------------------------------------------------------------------

def test_unit_economics():
    from unit_economics import compute
    inputs = parse_inputs({
        "arpa": 100, "gross_margin_pct": 0.8, "monthly_churn_rate": 0.02,
        "sm_spend": 5000, "new_customers": 50, "fixed_monthly_costs": 4400,
    })
    r = compute(inputs); r.finalize()
    check("ue ltv = 4000", approx(rv(r, "ltv"), 4000.0))
    check("ue cac = 100", approx(rv(r, "cac"), 100.0))
    check("ue ltv:cac = 40", approx(rv(r, "ltv_cac_ratio"), 40.0))
    check("ue payback = 1.25", approx(rv(r, "cac_payback_months"), 1.25))
    check("ue breakeven customers = 55", approx(rv(r, "breakeven_customers"), 55.0))
    check("ue status OK", r.status == "OK", r.status)

    r2 = compute(parse_inputs({"arpa": 100, "gross_margin_pct": 0.8,
                               "monthly_churn_rate": 0})); r2.finalize()
    check("ue churn=0 guards ltv", skipped(r2, "ltv"))

    r3 = compute({}); r3.finalize()
    check("ue empty → INSUFFICIENT_DATA", r3.status == "INSUFFICIENT_DATA", r3.status)
    check("ue missing prioritized",
          bool(r3.missing) and r3.missing[0]["priority"] == 1)


# ---------------------------------------------------------------------------
# saas_metrics
# ---------------------------------------------------------------------------

def test_saas():
    from saas_metrics import compute_point_metrics
    inputs = parse_inputs({
        "mrr_now": 101000, "mrr_start": 100000, "new_mrr": 10000,
        "expansion_mrr": 5000, "churned_mrr": 3000, "contraction_mrr": 1000,
    })
    r = compute_point_metrics(inputs); r.finalize()
    check("saas nrr = 101%", approx(rv(r, "nrr_pct"), 101.0))
    check("saas grr = 96%", approx(rv(r, "grr_pct"), 96.0))
    check("saas quick ratio = 3.75", approx(rv(r, "quick_ratio"), 3.75))
    check("saas arr = 12×mrr", approx(rv(r, "arr"), 1212000.0))

    r2 = compute_point_metrics(parse_inputs(
        {"net_burn_monthly": -5000, "cash_balance": 100000})); r2.finalize()
    check("saas cash-positive guards runway", skipped(r2, "runway_months"))


# ---------------------------------------------------------------------------
# projection
# ---------------------------------------------------------------------------

def test_projection():
    from projection import project
    drivers = {
        "months": 3, "starting_cash": 1000,
        "activities": [{"name": "svc", "price": 100, "unit_variable_cost": 20,
                        "volume_start": 10, "volume_growth_pct_monthly": 0}],
        "opex_lines": [{"name": "tools", "monthly_amount": 500}],
    }
    r = project(drivers); r.finalize()
    # revenue 1000/mo, GM 800, EBITDA 300 → cash 1000 + 3×300 = 1900
    check("proj ending cash = 1900", approx(rv(r, "ending_cash"), 1900.0))
    check("proj breakeven month 1", rv(r, "breakeven_month") == 1)
    check("proj invariants pass", all(i["passed"] for i in r.invariants),
          str(r.invariants))
    check("proj no zero-cash month", rv(r, "zero_cash_month") is None)

    r2 = project({}); r2.finalize()
    check("proj empty → INSUFFICIENT_DATA", r2.status == "INSUFFICIENT_DATA", r2.status)


# ---------------------------------------------------------------------------
# ratios
# ---------------------------------------------------------------------------

def test_ratios():
    from ratios import compute_ratios
    inputs = parse_inputs({
        "revenue": 1000, "cogs": 400, "net_income": 100,
        "total_assets": 800, "total_equity": 500,
        "current_assets": 300, "current_liabilities": 150,
    })
    r = compute_ratios(inputs); r.finalize()
    check("ratios gross margin 60%", approx(rv(r, "gross_margin_pct"), 60.0))
    check("ratios roe 20%", approx(rv(r, "roe"), 20.0))
    check("ratios current ratio 2.0", approx(rv(r, "current_ratio"), 2.0))
    check("ratios dupont ties roe", approx(rv(r, "roe_dupont"), rv(r, "roe") or -1))

    neg = parse_inputs({"revenue": 1000, "net_income": 100, "total_equity": -50,
                        "total_assets": 800})
    r2 = compute_ratios(neg); r2.finalize()
    check("ratios negative equity guards roe", skipped(r2, "roe"))


# ---------------------------------------------------------------------------
# opsfinance
# ---------------------------------------------------------------------------

def test_opsfinance():
    from opsfinance import unit_cost, capacity_plan, initiative_roi
    r = unit_cost(parse_inputs({
        "cost_pool": {"salaries": 100, "overhead_allocation": 50},
        "driver_volume": 30, "driver_name": "ticket"}))
    r.finalize()
    check("ops unit cost = 5.0", approx(rv(r, "unit_cost"), 5.0))

    r2 = capacity_plan(parse_inputs({
        "demand_volume_monthly": 3000, "aht_minutes": 10,
        "hours_per_fte_month": 160, "shrinkage_pct": 0.25,
        "occupancy_target": 0.8}))
    r2.finalize()
    check("ops fte = 5.2083", approx(rv(r2, "required_fte_raw"), 5.208333))

    r3 = capacity_plan(parse_inputs({
        "demand_volume_monthly": 3000, "aht_minutes": 10,
        "hours_per_fte_month": 160, "shrinkage_pct": 0.25,
        "occupancy_target": 1.4}))
    r3.finalize()
    check("ops occupancy>1 guarded", skipped(r3, "effective_hours_per_fte")
          or skipped(r3, "required_fte_raw") or r3.status == "INSUFFICIENT_DATA")

    r4 = initiative_roi(parse_inputs({
        "investment": 1000, "monthly_benefit": 100,
        "discount_rate_annual": 0, "horizon_months": 12}))
    r4.finalize()
    check("ops roi npv = 200", approx(rv(r4, "npv"), 200.0))
    check("ops roi payback = 10", approx(rv(r4, "payback_months"), 10.0))


# ---------------------------------------------------------------------------
# scenarios (reversal golden) + CLI exit codes + state validation
# ---------------------------------------------------------------------------

def test_scenarios():
    from scenarios import run_reversal
    from fin_common import Result
    inputs = parse_inputs({
        "arpa": 100, "gross_margin_pct": 0.8,
        "monthly_churn_rate": 0.02, "sm_spend": 40000, "new_customers": 50,
    })
    r = Result(script="scenarios")
    # cac = 800; ratio = (80/churn)/800 = 0.1/churn → crosses 3 at 0.033333
    run_reversal("unit-economics", inputs, "monthly_churn_rate",
                 "ltv_cac_ratio", 3.0, None, None, r)
    r.finalize()
    check("scen reversal churn = 0.03333", approx(rv(r, "reversal_value"), 0.033333, 1e-3))
    check("scen base ratio = 5.0", approx(rv(r, "base_ltv_cac_ratio"), 5.0))

    # ops model: pool 120000 / volume, unit_cost crosses 38 at volume = 3157.8947
    ops_inputs = parse_inputs({
        "cost_pool": {"salaries": 100000, "overhead_allocation": 20000},
        "driver_volume": 3200, "driver_name": "ticket"})
    r2 = Result(script="scenarios")
    run_reversal("ops-unit-cost", ops_inputs, "driver_volume",
                 "unit_cost", 38.0, None, None, r2)
    r2.finalize()
    check("scen ops reversal volume = 3157.89",
          approx(rv(r2, "reversal_value"), 3157.8947, 1e-3))


def test_cli_exit_codes():
    here = os.path.dirname(os.path.abspath(__file__))
    py = sys.executable

    p = subprocess.run([py, os.path.join(here, "unit_economics.py"),
                        "--inputs", "{}", "--json"],
                       capture_output=True, text=True)
    check("cli empty inputs exit 2", p.returncode == 2, f"got {p.returncode}")
    check("cli emits valid JSON", json.loads(p.stdout or "{}").get("status")
          == "INSUFFICIENT_DATA")

    with tempfile.NamedTemporaryFile("w", suffix=".fa.json", delete=False) as f:
        json.dump({"inputs": {"x": {"value": 1, "status": "fact"}}}, f)
        bad = f.name
    p2 = subprocess.run([py, os.path.join(here, "validate_state.py"), bad],
                        capture_output=True, text=True)
    check("validate bad state exit 3", p2.returncode == 3, f"got {p2.returncode}")
    os.unlink(bad)


def main() -> None:
    for t in (test_finmath, test_unit_economics, test_saas, test_projection,
              test_ratios, test_opsfinance, test_scenarios, test_cli_exit_codes):
        t()
    total = PASS + FAIL
    print(f"selftest: {PASS}/{total} passed" + (f", {FAIL} FAILED" if FAIL else ""))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
