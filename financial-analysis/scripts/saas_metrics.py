"""saas_metrics — SaaS / recurring-revenue metrics for the financial-analysis skill.

Three mutually exclusive modes:

1. Point metrics (default, --inputs/--inputs-file): one measurement window's
   MRR movement and efficiency ratios — ARR, ARPA, growth, logo and revenue
   churn, NRR/GRR, quick ratio, magic number, burn multiple, runway, Rule of
   40, and inline unit economics (LTV/CAC). Every ratio is guarded because a
   plausible-but-wrong SaaS metric (an "infinite LTV" from zero churn, an NRR
   silently missing expansion) misleads far more than an honest gap.

2. ARR bridge (--mrr-file): monthly movement CSV → per-month waterfall of
   starting/new/expansion/churned/contraction/ending MRR. The first month's
   base must be pinned by `mrr_end` on the first row or --starting-mrr —
   any other derivation would be a guess, so the script refuses instead.

3. Cohort retention (--cohort-file): cohort × month customer counts →
   retention triangle as % of month-0, plus the average retention curve at
   months 1/3/6/12 where the data reaches that far.

`compute_point_metrics` is importable so scenarios.py can re-run mode 1 with
perturbed drivers without shelling out.
"""

from __future__ import annotations

from fin_common import (
    Result,
    Tagged,
    cli,
    gather_inputs,
    guard,
    load_table,
    num,
)


# ---------------------------------------------------------------------------
# Mode 1 — point metrics
# ---------------------------------------------------------------------------

def compute_point_metrics(inputs: dict[str, Tagged]) -> Result:
    """All point-in-time SaaS metrics computable from the given tagged inputs.

    Pure with respect to its argument: reads inputs, returns a fresh Result.
    Missing drivers become prioritized `missing` entries (the question agenda)
    and undefined ratios become `not_computed` entries — never defaults.
    """
    result = Result(script="saas_metrics")
    result.echo_inputs(inputs)

    mrr_now = num(inputs, "mrr_now")
    mrr_prior = num(inputs, "mrr_prior")
    months_between = num(inputs, "months_between")
    if months_between is None:
        months_between = 1.0

    # mrr_start is the base of the measured month. Over a single-month window
    # it coincides with mrr_prior, so defaulting is a restatement, not a guess.
    mrr_start = num(inputs, "mrr_start")
    if mrr_start is None and months_between == 1 and mrr_prior is not None:
        mrr_start = mrr_prior
        result.warn("mrr_start not provided; using mrr_prior as the month's "
                    "starting base (single-month window)")

    # -- ARR / ARPA -----------------------------------------------------------
    if mrr_now is not None:
        result.add("arr", mrr_now * 12, "mrr_now * 12", ["mrr_now"],
                   unit="currency")
    else:
        result.need("mrr_now", "current MRR anchors ARR, ARPA, growth and "
                    "Rule of 40 — the headline metrics", 1)
        result.skip("arr", "mrr_now unknown", ["mrr_now"])

    arpa = None
    customers_total = num(inputs, "customers_total")
    if mrr_now is not None and customers_total is not None:
        if guard(result, "arpa", customers_total > 0,
                 "customers_total must be > 0", ["customers_total"]):
            arpa = mrr_now / customers_total
            result.add("arpa", arpa, "mrr_now / customers_total",
                       ["mrr_now", "customers_total"], unit="currency/month")
    else:
        if customers_total is None:
            result.need("customers_total", "customer count turns MRR into "
                        "ARPA, the LTV numerator", 3)
        result.skip("arpa", "needs mrr_now and customers_total",
                    ["mrr_now", "customers_total"])

    # -- Growth ---------------------------------------------------------------
    growth_monthly_pct = None
    growth_metric = "mom_growth_pct" if months_between == 1 else "cmgr_pct"
    if mrr_now is not None and mrr_prior is not None:
        if months_between == 1:
            if guard(result, "mom_growth_pct", mrr_prior > 0,
                     "mrr_prior must be > 0", ["mrr_prior"]):
                growth_monthly_pct = (mrr_now - mrr_prior) / mrr_prior * 100
                result.add("mom_growth_pct", growth_monthly_pct,
                           "(mrr_now - mrr_prior) / mrr_prior * 100",
                           ["mrr_now", "mrr_prior"], unit="%")
        elif months_between > 1:
            if guard(result, "cmgr_pct", mrr_prior > 0 and mrr_now >= 0,
                     "CMGR needs mrr_prior > 0 and mrr_now >= 0",
                     ["mrr_now", "mrr_prior"]):
                growth_monthly_pct = (
                    (mrr_now / mrr_prior) ** (1.0 / months_between) - 1) * 100
                result.add("cmgr_pct", growth_monthly_pct,
                           "((mrr_now / mrr_prior)^(1/months_between) - 1) * 100",
                           ["mrr_now", "mrr_prior", "months_between"], unit="%")
        else:
            result.skip(growth_metric, "months_between must be >= 1",
                        ["months_between"])
    else:
        result.skip(growth_metric, "needs mrr_now and mrr_prior",
                    ["mrr_now", "mrr_prior"])

    # -- Revenue churn / NRR / GRR -------------------------------------------
    churned_mrr = num(inputs, "churned_mrr")
    expansion_mrr = num(inputs, "expansion_mrr")
    contraction_mrr = num(inputs, "contraction_mrr")

    revenue_churn_rate = None  # monthly decimal, feeds nrr_est and LTV
    if mrr_start is not None and churned_mrr is not None:
        if guard(result, "revenue_churn_monthly_pct", mrr_start > 0,
                 "mrr_start must be > 0", ["mrr_start"]):
            revenue_churn_rate = churned_mrr / mrr_start
            result.add("revenue_churn_monthly_pct", revenue_churn_rate * 100,
                       "churned_mrr / mrr_start * 100",
                       ["churned_mrr", "mrr_start"], unit="%")
    else:
        if mrr_start is None:
            result.need("mrr_start", "starting MRR of the measured month is "
                        "the denominator for revenue churn, NRR and GRR", 1)
        if churned_mrr is None:
            result.need("churned_mrr", "churned MRR drives revenue churn, "
                        "NRR, GRR and the quick ratio", 1)
        result.skip("revenue_churn_monthly_pct",
                    "needs mrr_start and churned_mrr",
                    ["mrr_start", "churned_mrr"])

    if expansion_mrr is None:
        result.need("expansion_mrr", "expansion MRR is required for full NRR "
                    "and the quick ratio", 2)
    if contraction_mrr is None:
        result.need("contraction_mrr", "contraction MRR is required for NRR, "
                    "GRR and the quick ratio", 2)

    if None not in (mrr_start, expansion_mrr, contraction_mrr, churned_mrr):
        if guard(result, "nrr_pct", mrr_start > 0, "mrr_start must be > 0",
                 ["mrr_start"]):
            result.add(
                "nrr_pct",
                (mrr_start + expansion_mrr - churned_mrr - contraction_mrr)
                / mrr_start * 100,
                "(mrr_start + expansion_mrr - churned_mrr - contraction_mrr)"
                " / mrr_start * 100",
                ["mrr_start", "expansion_mrr", "churned_mrr",
                 "contraction_mrr"], unit="%")
    elif revenue_churn_rate is not None:
        result.add("nrr_est_pct", (1 - revenue_churn_rate) * 100,
                   "(1 - churned_mrr / mrr_start) * 100",
                   ["churned_mrr", "mrr_start"], unit="%")
        result.warn("churn-only estimate; provide expansion MRR for full NRR")
        result.skip("nrr_pct", "expansion/contraction MRR unknown — reported "
                    "nrr_est_pct instead",
                    ["expansion_mrr", "contraction_mrr"])
    else:
        result.skip("nrr_pct", "needs mrr_start, expansion_mrr, "
                    "contraction_mrr and churned_mrr",
                    ["mrr_start", "expansion_mrr", "contraction_mrr",
                     "churned_mrr"])

    if None not in (mrr_start, churned_mrr, contraction_mrr):
        if guard(result, "grr_pct", mrr_start > 0, "mrr_start must be > 0",
                 ["mrr_start"]):
            result.add("grr_pct",
                       (mrr_start - churned_mrr - contraction_mrr)
                       / mrr_start * 100,
                       "(mrr_start - churned_mrr - contraction_mrr)"
                       " / mrr_start * 100",
                       ["mrr_start", "churned_mrr", "contraction_mrr"],
                       unit="%")
    else:
        result.skip("grr_pct",
                    "needs mrr_start, churned_mrr and contraction_mrr",
                    ["mrr_start", "churned_mrr", "contraction_mrr"])

    # -- Logo churn -----------------------------------------------------------
    customers_start = num(inputs, "customers_start")
    customers_churned = num(inputs, "customers_churned")
    logo_churn_rate = None
    if customers_start is not None and customers_churned is not None:
        if guard(result, "logo_churn_monthly_pct", customers_start > 0,
                 "customers_start must be > 0", ["customers_start"]):
            logo_churn_rate = customers_churned / customers_start
            result.add("logo_churn_monthly_pct", logo_churn_rate * 100,
                       "customers_churned / customers_start * 100",
                       ["customers_churned", "customers_start"], unit="%")
            if guard(result, "logo_churn_annualized_pct",
                     0 <= logo_churn_rate <= 1,
                     "monthly logo churn outside [0%, 100%] — compounding "
                     "annualization is undefined",
                     ["customers_churned", "customers_start"]):
                result.add("logo_churn_annualized_pct",
                           (1 - (1 - logo_churn_rate) ** 12) * 100,
                           "(1 - (1 - monthly_logo_churn_rate)^12) * 100",
                           ["customers_churned", "customers_start"], unit="%")
    else:
        if customers_start is None:
            result.need("customers_start", "starting customer count is the "
                        "logo-churn denominator", 2)
        if customers_churned is None:
            result.need("customers_churned", "churned customer count drives "
                        "logo churn", 2)
        result.skip("logo_churn_monthly_pct",
                    "needs customers_start and customers_churned",
                    ["customers_start", "customers_churned"])

    # -- Quick ratio ----------------------------------------------------------
    new_mrr = num(inputs, "new_mrr")
    if None not in (new_mrr, expansion_mrr, churned_mrr, contraction_mrr):
        lost = churned_mrr + contraction_mrr
        if guard(result, "quick_ratio", lost > 0,
                 "no churned or contracted MRR — quick ratio is undefined "
                 "(division by zero), which is itself a good sign",
                 ["churned_mrr", "contraction_mrr"]):
            result.add("quick_ratio", (new_mrr + expansion_mrr) / lost,
                       "(new_mrr + expansion_mrr) /"
                       " (churned_mrr + contraction_mrr)",
                       ["new_mrr", "expansion_mrr", "churned_mrr",
                        "contraction_mrr"], unit="x")
    else:
        if new_mrr is None:
            result.need("new_mrr", "new MRR is the growth half of the quick "
                        "ratio", 3)
        result.skip("quick_ratio", "needs new_mrr, expansion_mrr, "
                    "churned_mrr and contraction_mrr",
                    ["new_mrr", "expansion_mrr", "churned_mrr",
                     "contraction_mrr"])

    # -- Sales efficiency: magic number, burn multiple, runway ---------------
    net_new_arr_q = num(inputs, "net_new_arr_quarter")
    sm_spend = num(inputs, "sm_spend_prior_quarter")
    if net_new_arr_q is not None and sm_spend is not None:
        if guard(result, "magic_number", sm_spend > 0,
                 "sm_spend_prior_quarter must be > 0",
                 ["sm_spend_prior_quarter"]):
            result.add("magic_number", net_new_arr_q / sm_spend,
                       "net_new_arr_quarter / sm_spend_prior_quarter",
                       ["net_new_arr_quarter", "sm_spend_prior_quarter"],
                       unit="x")
    else:
        if net_new_arr_q is None:
            result.need("net_new_arr_quarter", "quarterly net-new ARR drives "
                        "the magic number and burn multiple", 3)
        if sm_spend is None:
            result.need("sm_spend_prior_quarter", "prior-quarter S&M spend "
                        "is the magic-number denominator", 3)
        result.skip("magic_number",
                    "needs net_new_arr_quarter and sm_spend_prior_quarter",
                    ["net_new_arr_quarter", "sm_spend_prior_quarter"])

    net_burn = num(inputs, "net_burn_monthly")
    if net_burn is None:
        result.need("net_burn_monthly", "monthly net burn drives the burn "
                    "multiple and runway", 2)

    if net_burn is not None and net_new_arr_q is not None:
        if net_burn <= 0:
            result.skip("burn_multiple", "company is cash-flow positive")
        elif guard(result, "burn_multiple", net_new_arr_q > 0,
                   "net_new_arr_quarter must be > 0 — burning cash while "
                   "shrinking has no meaningful burn multiple",
                   ["net_new_arr_quarter"]):
            result.add("burn_multiple", net_burn * 3 / net_new_arr_q,
                       "net_burn_monthly * 3 / net_new_arr_quarter",
                       ["net_burn_monthly", "net_new_arr_quarter"], unit="x")
    else:
        result.skip("burn_multiple",
                    "needs net_burn_monthly and net_new_arr_quarter",
                    ["net_burn_monthly", "net_new_arr_quarter"])

    cash = num(inputs, "cash_balance")
    if cash is None:
        result.need("cash_balance", "cash balance with net burn gives "
                    "runway", 2)
    if net_burn is not None and cash is not None:
        if net_burn <= 0:
            result.skip("runway_months",
                        "cash-flow positive — runway not applicable")
        else:
            result.add("runway_months", cash / net_burn,
                       "cash_balance / net_burn_monthly",
                       ["cash_balance", "net_burn_monthly"], unit="months")
    else:
        result.skip("runway_months",
                    "needs cash_balance and net_burn_monthly",
                    ["cash_balance", "net_burn_monthly"])

    # -- Rule of 40 -----------------------------------------------------------
    npm = num(inputs, "net_profit_margin_pct")
    growth_m = num(inputs, "monthly_growth_pct")
    growth_source = "monthly_growth_pct"
    if growth_m is None:
        growth_m = growth_monthly_pct
        growth_source = growth_metric
    if growth_m is not None and npm is not None:
        if guard(result, "rule_of_40", growth_m > -100,
                 "monthly growth <= -100% — annualization undefined",
                 [growth_source]):
            annual_growth = ((1 + growth_m / 100) ** 12 - 1) * 100
            result.add("rule_of_40", annual_growth + npm,
                       f"((1 + {growth_source}/100)^12 - 1) * 100"
                       " + net_profit_margin_pct",
                       [growth_source, "net_profit_margin_pct"], unit="%")
            result.warn("Rule of 40 growth was annualized from monthly "
                        "growth by compounding — aggressive; prefer actual "
                        "YoY growth when available")
    else:
        result.skip("rule_of_40",
                    "needs a growth rate (monthly_growth_pct or mrr_now + "
                    "mrr_prior) and net_profit_margin_pct",
                    ["monthly_growth_pct", "net_profit_margin_pct"])

    # -- Unit economics (inline, mirrors unit_economics.py formulas) ---------
    gm_pct = num(inputs, "gross_margin_pct")
    if gm_pct is None:
        result.need("gross_margin_pct", "gross margin turns ARPA into "
                    "contribution for LTV and CAC payback", 2)
    gm_frac = None
    if gm_pct is not None:
        if 0 < gm_pct <= 100:
            gm_frac = gm_pct / 100
        else:
            result.warn("gross_margin_pct outside (0, 100] — ignored for "
                        "LTV/CAC payback")

    churn_for_ltv = revenue_churn_rate
    churn_basis = "revenue_churn_monthly_rate"
    if churn_for_ltv is None and logo_churn_rate is not None:
        churn_for_ltv = logo_churn_rate
        churn_basis = "logo_churn_monthly_rate"
        result.warn("LTV uses logo churn as a proxy — revenue churn is the "
                    "better basis when churned MRR is known")

    ltv = None
    if arpa is not None and gm_frac is not None and churn_for_ltv is not None:
        if guard(result, "ltv", churn_for_ltv > 0,
                 "zero (or negative) churn implies infinite customer "
                 "lifetime — LTV undefined",
                 ["churned_mrr", "customers_churned"]):
            ltv = arpa * gm_frac / churn_for_ltv
            result.add("ltv", ltv,
                       f"arpa * gross_margin_fraction / {churn_basis}",
                       ["mrr_now", "customers_total", "gross_margin_pct",
                        "churned_mrr" if churn_basis.startswith("revenue")
                        else "customers_churned"], unit="currency")
    else:
        result.skip("ltv", "needs arpa (mrr_now + customers_total), "
                    "gross_margin_pct and a monthly churn rate",
                    ["mrr_now", "customers_total", "gross_margin_pct",
                     "churned_mrr"])

    cac = None
    customers_new = num(inputs, "customers_new")
    if sm_spend is not None and customers_new is not None:
        if guard(result, "cac", customers_new > 0,
                 "customers_new must be > 0", ["customers_new"]):
            cac = sm_spend / customers_new
            result.add("cac", cac, "sm_spend_prior_quarter / customers_new",
                       ["sm_spend_prior_quarter", "customers_new"],
                       unit="currency")
            result.warn("CAC divides prior-quarter S&M spend by "
                        "customers_new — confirm customers_new counts the "
                        "same quarter's acquisitions")
    else:
        result.skip("cac", "needs sm_spend_prior_quarter and customers_new",
                    ["sm_spend_prior_quarter", "customers_new"])

    if ltv is not None and cac is not None:
        if guard(result, "ltv_cac", cac > 0, "cac must be > 0",
                 ["sm_spend_prior_quarter", "customers_new"]):
            result.add("ltv_cac", ltv / cac, "ltv / cac", ["ltv", "cac"],
                       unit="x")
    else:
        result.skip("ltv_cac", "needs both ltv and cac", ["ltv", "cac"])

    if cac is not None and arpa is not None and gm_frac is not None:
        contribution = arpa * gm_frac
        if guard(result, "cac_payback_months", contribution > 0,
                 "monthly contribution (arpa * gross margin) must be > 0",
                 ["mrr_now", "customers_total", "gross_margin_pct"]):
            result.add("cac_payback_months", cac / contribution,
                       "cac / (arpa * gross_margin_fraction)",
                       ["cac", "mrr_now", "customers_total",
                        "gross_margin_pct"], unit="months")
    else:
        result.skip("cac_payback_months",
                    "needs cac, arpa and gross_margin_pct",
                    ["sm_spend_prior_quarter", "customers_new", "mrr_now",
                     "customers_total", "gross_margin_pct"])

    return result


# ---------------------------------------------------------------------------
# Mode 2 — ARR bridge from a monthly movement file
# ---------------------------------------------------------------------------

def _cell(v) -> float | None:
    """Float value of one table cell; None for blank/NaN/unparseable cells."""
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def compute_arr_bridge(path: str, starting_mrr: float | None = None) -> Result:
    """ARR bridge from a CSV/Excel of monthly MRR movements.

    Required columns: month, new_mrr, expansion_mrr, contraction_mrr,
    churned_mrr. Optional: mrr_end. The chain needs an anchor: either
    --starting-mrr or an mrr_end on the first row — refusing beats inventing
    a base every later month would inherit. When a month's reported mrr_end
    disagrees with the computed bridge, the reported figure wins (reality
    over model) and the untied residual is surfaced as a warning.
    """
    result = Result(script="saas_metrics")
    echo: dict[str, Tagged] = {"mrr_file": Tagged(value=path, status="user")}
    if starting_mrr is not None:
        echo["starting_mrr"] = Tagged(value=starting_mrr, status="user")
    result.echo_inputs(echo)

    df = load_table(path, ["month", "new_mrr", "expansion_mrr",
                           "contraction_mrr", "churned_mrr"])
    records = df.to_dict("records")
    if not records:
        raise SystemExit(f"{path} has no data rows")
    has_end = "mrr_end" in df.columns

    movement_cols = ("new_mrr", "expansion_mrr", "contraction_mrr",
                     "churned_mrr")
    blanks_filled = False

    def movements(rec: dict) -> tuple:
        nonlocal blanks_filled
        vals = []
        for col in movement_cols:
            v = _cell(rec.get(col))
            if v is None:
                v = 0.0
                blanks_filled = True
            vals.append(v)
        return tuple(vals)

    first_new, first_exp, first_ctr, first_chn = movements(records[0])
    first_end = _cell(records[0].get("mrr_end")) if has_end else None
    if starting_mrr is not None:
        base = float(starting_mrr)
    elif first_end is not None:
        base = first_end - (first_new + first_exp - first_ctr - first_chn)
    else:
        raise SystemExit(
            "Cannot derive the starting MRR base: provide --starting-mrr, or "
            "include an mrr_end value on the first row of the file. The "
            "bridge refuses to guess its anchor."
        )

    rows: list[dict] = []
    for rec in records:
        new, exp, ctr, chn = movements(rec)
        computed_end = base + new + exp - ctr - chn
        ending = computed_end
        reported = _cell(rec.get("mrr_end")) if has_end else None
        if reported is not None:
            if abs(reported - computed_end) > 0.01:
                result.warn(
                    f"month {rec.get('month')}: bridge does not tie — "
                    f"computed ending {computed_end:.2f} vs reported "
                    f"{reported:.2f}; using reported (unmodeled MRR movement)"
                )
            ending = reported
        rows.append({
            "month": str(rec.get("month")),
            "starting_mrr": round(base, 2),
            "new": round(new, 2),
            "expansion": round(exp, 2),
            "churned": round(chn, 2),
            "contraction": round(ctr, 2),
            "ending_mrr": round(ending, 2),
            "net_new_mrr": round(ending - base, 2),
        })
        base = ending

    if blanks_filled:
        result.warn("blank movement cells in the MRR file were treated as 0")

    result.add_table(
        "arr_bridge", rows,
        "ending_mrr = starting_mrr + new + expansion - churned - contraction"
        " (per month)")
    result.add("ending_arr", rows[-1]["ending_mrr"] * 12,
               "ending_mrr of last month * 12", ["mrr_file"], unit="currency")

    if len(rows) >= 13:
        window = rows[-12:]
        base12 = window[0]["starting_mrr"]
        exp12 = sum(r["expansion"] for r in window)
        chn12 = sum(r["churned"] for r in window)
        ctr12 = sum(r["contraction"] for r in window)
        if guard(result, "ltm_nrr_pct", base12 > 0,
                 "starting MRR of the trailing-12 window must be > 0"):
            result.add("ltm_nrr_pct",
                       (base12 + exp12 - chn12 - ctr12) / base12 * 100,
                       "(start_of_window + sum(expansion) - sum(churned) - "
                       "sum(contraction)) / start_of_window * 100, trailing "
                       "12 months", ["mrr_file"], unit="%")
        if guard(result, "ltm_grr_pct", base12 > 0,
                 "starting MRR of the trailing-12 window must be > 0"):
            result.add("ltm_grr_pct",
                       (base12 - chn12 - ctr12) / base12 * 100,
                       "(start_of_window - sum(churned) - sum(contraction))"
                       " / start_of_window * 100, trailing 12 months",
                       ["mrr_file"], unit="%")
    else:
        reason = f"needs >= 13 months of data for a trailing-12 window " \
                 f"(have {len(rows)})"
        result.skip("ltm_nrr_pct", reason)
        result.skip("ltm_grr_pct", reason)

    return result


# ---------------------------------------------------------------------------
# Mode 3 — cohort retention triangle
# ---------------------------------------------------------------------------

def compute_cohort_triangle(path: str) -> Result:
    """Retention triangle from a CSV/Excel of cohort × month customer counts.

    Required columns: cohort_month, months_since_start, customers (mrr is
    accepted but retention is customer-based here). Each triangle row shows
    retention as % of the cohort's month-0 count; cohorts without a positive
    month-0 count are excluded — a triangle row without its own denominator
    would be meaningless.
    """
    result = Result(script="saas_metrics")
    result.echo_inputs({"cohort_file": Tagged(value=path, status="user")})

    df = load_table(path, ["cohort_month", "months_since_start", "customers"])
    cohorts: dict[str, dict[int, float]] = {}
    order: list[str] = []
    for rec in df.to_dict("records"):
        name = str(rec.get("cohort_month"))
        month = _cell(rec.get("months_since_start"))
        count = _cell(rec.get("customers"))
        if month is None or count is None:
            result.warn(f"cohort {name}: skipped a row with blank/unparseable"
                        " months_since_start or customers")
            continue
        if name not in cohorts:
            cohorts[name] = {}
            order.append(name)
        cohorts[name][int(month)] = count

    tri_rows: list[dict] = []
    for name in order:
        series = cohorts[name]
        m0 = series.get(0)
        if m0 is None or m0 <= 0:
            result.warn(f"cohort {name}: no positive month-0 customer count "
                        "— excluded from the triangle")
            continue
        row: dict = {"cohort_month": name}
        for m in sorted(series):
            row[f"m{m}"] = round(series[m] / m0 * 100, 2)
        tri_rows.append(row)

    if not tri_rows:
        result.skip("cohort_triangle",
                    "no cohort had a positive month-0 customer count")
        result.need("cohort_month_zero_counts",
                    "each cohort's month-0 size is the retention denominator",
                    1)
        return result

    result.add_table("cohort_triangle", tri_rows,
                     "customers[month m] / customers[month 0] * 100, per "
                     "cohort")

    for k in (1, 3, 6, 12):
        vals = [r[f"m{k}"] for r in tri_rows if f"m{k}" in r]
        if vals:
            result.add(f"avg_retention_m{k}_pct", sum(vals) / len(vals),
                       f"simple average of cohort retention at month {k} "
                       f"across {len(vals)} cohort(s)", ["cohort_file"],
                       unit="%")
        else:
            result.skip(f"avg_retention_m{k}_pct",
                        f"no cohort has month-{k} data yet")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_args(parser) -> None:
    parser.add_argument("--mrr-file",
                        help="CSV/Excel of monthly MRR movements: month, "
                             "new_mrr, expansion_mrr, contraction_mrr, "
                             "churned_mrr [, mrr_end] — builds the ARR "
                             "bridge")
    parser.add_argument("--cohort-file",
                        help="CSV/Excel of cohort_month, months_since_start, "
                             "customers [, mrr] — builds the retention "
                             "triangle")
    parser.add_argument("--starting-mrr", type=float, default=None,
                        help="MRR base before the first month in --mrr-file "
                             "(alternative to mrr_end on the first row)")


def _run(args, warnings: list[str]) -> Result:
    point_inputs_given = bool(args.inputs or args.inputs_file)
    if args.mrr_file and args.cohort_file:
        raise SystemExit("--mrr-file and --cohort-file are mutually "
                         "exclusive — run the script twice")
    if (args.mrr_file or args.cohort_file) and point_inputs_given:
        raise SystemExit("file modes do not combine with --inputs/"
                         "--inputs-file — pick one mode per run")
    if args.starting_mrr is not None and not args.mrr_file:
        raise SystemExit("--starting-mrr only applies with --mrr-file")

    if args.mrr_file:
        return compute_arr_bridge(args.mrr_file, args.starting_mrr)
    if args.cohort_file:
        return compute_cohort_triangle(args.cohort_file)
    return compute_point_metrics(gather_inputs(args, warnings))


if __name__ == "__main__":
    cli("saas_metrics",
        "SaaS/recurring-revenue metrics: point metrics (default), ARR "
        "bridge (--mrr-file), cohort retention (--cohort-file)",
        _run, add_args=_add_args)
