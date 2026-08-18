"""projection — monthly P&L + cash projection (the Fisy cascade).

Turns a compact driver file into a 36-month (default) accrual P&L plus a
separate cash track, because the two diverge exactly where small companies
die: profitable on paper, out of cash in practice. The accrual cascade and
the cash roll-forward are computed independently and then tied together by
invariants, so a bookkeeping bug in one surfaces as VALIDATION_FAILED
instead of a quietly wrong runway.

Driver schema — every scalar below may be a bare number OR a tagged
{"value": ..., "status": ..., "basis": ...} object (tags are echoed for
provenance; math uses the value):

    {
      "months": 36,                 // optional, default 36, capped at 120
      "starting_cash": 30000,       // opening cash; without it the cash
                                    // track is skipped (P&L still runs)
      "currency": "USD",            // echoed only, never converted
      "activities": [               // >=1 usable activity is the critical gate
        {"name": "subscriptions",
         "price": 99,                       // per unit, accrual
         "unit_variable_cost": 8,           // per unit; missing => 0 (warned)
         "volume_start": 5,                 // units in month 1
         "volume_growth_pct_monthly": 10}   // percent (10 = 10%), compounding
        // OR "volumes": [5, 6, 7, ...]     // explicit per-month units;
        //                                  // overrides growth; a short list
        //                                  // holds its last value (warned)
      ],
      "opex_lines": [
        {"name": "hosting", "monthly_amount": 400,
         "start_month": 1,                  // default 1
         "annual_growth_pct": 0}            // percent; steps at months 13, 25...
      ],
      "payroll": [
        {"role": "founder", "monthly_gross": 4000, "count": 1,
         "start_month": 1,
         "employer_burden_pct": 0}          // fraction 0-1; a value > 1.5 is
                                            // read as percent/100 (warned)
      ],
      "capex": [
        {"name": "laptop", "amount": 3000, "month": 1,
         "amortization_months": 36}         // straight-line from its month;
                                            // missing => 36 (warned)
      ],
      "loans": [
        {"principal": 20000, "annual_rate": 0.12, "months": 36,
         "start_month": 1}                  // drawdown in at start_month, then
                                            // constant payment (finmath)
      ],
      "funding": [{"amount": 50000, "month": 1}],
      "tax_rate_pct": 0.15,         // fraction of positive pre-tax income,
                                    // monthly approximation; > 1 read as
                                    // percent/100 (warned); missing => taxes
                                    // assumed 0 with a p3 gap recorded
      "dso_days": 0,                // customer payment delay; cash shifts by
                                    // round(days/30) months
      "dpo_days": 0                 // supplier payment delay, same shift
    }

Accrual cascade per month: revenue -> variable costs -> gross margin ->
opex -> payroll -> EBITDA -> depreciation -> EBIT -> interest -> pre-tax ->
tax (on positive pre-tax only) -> net income.

Cash track per month: collections (revenue shifted by DSO — revenue earned
near the horizon edge but collected beyond it is simply not collected
within the horizon; DPO mirrors this for supplier payments), payroll and
tax paid same month, capex at its month, loan drawdown in and debt service
out, funding in.

CLI note: --drivers-file (or --inputs / --inputs-file) takes the RAW driver
JSON above, not a flat tagged-inputs dict — the schema is nested, so
per-field tags are handled by unwrap() rather than fin_common.parse_inputs.

Importable entry point (scenarios.py re-runs this with mutated drivers):

    project(drivers: dict, months: int | None = None) -> Result

The returned Result is NOT finalized — the caller decides when to freeze
status and exit code (the CLI scaffold does it for command-line runs).
"""

from __future__ import annotations

import json

from fin_common import Result, cli, guard
from finmath import amortization_schedule

SCRIPT = "projection"
DEFAULT_MONTHS = 36
MAX_MONTHS = 120
CASH_TOL = 0.01
EPS = 1e-9

_LIST_DRIVERS = ("activities", "opex_lines", "payroll", "capex", "loans", "funding")
_SCHEMA_KEYS = ("starting_cash", "activities", "opex_lines", "payroll", "capex",
                "loans", "funding", "tax_rate_pct", "dso_days", "dpo_days")


# ---------------------------------------------------------------------------
# Driver plumbing
# ---------------------------------------------------------------------------

def unwrap(v: object, name: str | None = None, echo: dict | None = None) -> object:
    """Extract the bare value from a possibly-tagged scalar.

    Drivers may tag any scalar as {"value":..,"status":..,"basis":..} to keep
    provenance visible; the math only needs the value. When `name` and `echo`
    are given, the tag (or a synthesized user tag for bare scalars) is
    recorded so the envelope echoes provenance without the cascade caring.
    """
    if isinstance(v, dict) and "value" in v:
        if echo is not None and name is not None:
            tag = {"value": v.get("value"), "status": v.get("status", "user")}
            if v.get("basis"):
                tag["basis"] = v.get("basis")
            echo[name] = tag
        return v.get("value")
    if echo is not None and name is not None and not isinstance(v, (list, dict)):
        echo[name] = {"value": v, "status": "user"}
    return v


def _num(v: object) -> float | None:
    """Coerce to float, else None. Bools are excluded — JSON true/false are
    flags, not quantities, and float(True) == 1.0 would silently invent one."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


def _items(result: Result, drivers: dict, key: str) -> list:
    v = drivers.get(key)
    if v is None:
        return []
    if not isinstance(v, list):
        result.warn(f"driver '{key}' must be a list of objects; ignored")
        return []
    return v


def _unwrap_item(item: dict) -> dict:
    return {k: unwrap(v) for k, v in item.items()}


def _resolve_months(drivers: dict, override: object, result: Result,
                    echo: dict) -> int:
    if override is not None:
        raw: object = override
        echo["months"] = {"value": override, "status": "user",
                          "basis": "explicit months override"}
    elif "months" in drivers:
        raw = unwrap(drivers.get("months"), "months", echo)
    else:
        raw = None
    if raw is None:
        echo["months"] = {"value": DEFAULT_MONTHS, "status": "assumption",
                          "basis": "default projection horizon"}
        return DEFAULT_MONTHS
    v = _num(raw)
    if v is None or v < 1:
        result.warn(f"months={raw!r} is not a usable horizon; "
                    f"defaulting to {DEFAULT_MONTHS}")
        h = DEFAULT_MONTHS
    else:
        h = int(round(v))
        if h > MAX_MONTHS:
            result.warn(f"months={h} exceeds the {MAX_MONTHS}-month cap; clamped")
            h = MAX_MONTHS
    if isinstance(echo.get("months"), dict):
        echo["months"]["value"] = h
    return h


def _month_shift(drivers: dict, key: str, result: Result, echo: dict) -> int:
    """Days -> whole-month shift, because the model is monthly: a 30-day
    delay moves cash one month; sub-15-day delays round away to zero."""
    if key not in drivers:
        return 0
    d = _num(unwrap(drivers.get(key), key, echo))
    if d is None or d < 0:
        result.warn(f"{key} is not a usable day count; assumed 0")
        return 0
    return int(round(d / 30.0))


# ---------------------------------------------------------------------------
# Driver -> month-indexed arrays (index 0 unused so month m reads arr[m])
# ---------------------------------------------------------------------------

def _activity_volumes(result: Result, a: dict, name: str,
                      horizon: int) -> list | None:
    vols_raw = a.get("volumes")
    if isinstance(vols_raw, list) and vols_raw:
        vols, bad = [], False
        for x in vols_raw:
            n = _num(unwrap(x))
            if n is None:
                bad = True
                n = 0.0
            vols.append(n)
        if bad:
            result.warn(f"activity '{name}': non-numeric volumes entries treated as 0")
        if len(vols) < horizon:
            result.warn(f"activity '{name}': volumes has {len(vols)} entries for a "
                        f"{horizon}-month horizon; holding the last value")
            vols += [vols[-1]] * (horizon - len(vols))
        return vols[:horizon]
    start = _num(a.get("volume_start"))
    if start is None:
        return None
    g = (_num(a.get("volume_growth_pct_monthly")) or 0.0) / 100.0
    if g <= -1.0:
        result.warn(f"activity '{name}': monthly growth <= -100%; "
                    "volume drops to 0 after month 1")
        return [start] + [0.0] * (horizon - 1)
    return [start * (1.0 + g) ** m for m in range(horizon)]


def _revenue_streams(result: Result, drivers: dict,
                     horizon: int) -> "tuple[list, list, int]":
    rev = [0.0] * (horizon + 1)
    var = [0.0] * (horizon + 1)
    usable = 0
    for i, item in enumerate(_items(result, drivers, "activities")):
        if not isinstance(item, dict):
            result.warn(f"activities[{i}] is not an object; ignored")
            continue
        a = _unwrap_item(item)
        name = str(a.get("name") or f"activity_{i + 1}")
        price = _num(a.get("price"))
        if price is None:
            result.need(f"activities[{i}].price",
                        f"'{name}' contributes no revenue without a unit price", 2)
            result.warn(f"activity '{name}': no usable price; excluded")
            continue
        vols = _activity_volumes(result, a, name, horizon)
        if vols is None:
            result.need(f"activities[{i}].volume_start",
                        f"'{name}' needs volume_start (or an explicit volumes list)", 2)
            result.warn(f"activity '{name}': no volume information; excluded")
            continue
        uvc = _num(a.get("unit_variable_cost"))
        if uvc is None:
            uvc = 0.0
            result.warn(f"activity '{name}': unit_variable_cost missing; assumed 0")
        usable += 1
        for m in range(1, horizon + 1):
            rev[m] += vols[m - 1] * price
            var[m] += vols[m - 1] * uvc
    return rev, var, usable


def _opex(result: Result, drivers: dict, horizon: int) -> list:
    opex = [0.0] * (horizon + 1)
    for i, item in enumerate(_items(result, drivers, "opex_lines")):
        if not isinstance(item, dict):
            result.warn(f"opex_lines[{i}] is not an object; ignored")
            continue
        o = _unwrap_item(item)
        name = str(o.get("name") or f"opex_{i + 1}")
        amt = _num(o.get("monthly_amount"))
        if amt is None:
            result.need(f"opex_lines[{i}].monthly_amount",
                        f"opex line '{name}' has no amount", 2)
            result.warn(f"opex line '{name}': no monthly_amount; excluded")
            continue
        start = int(_num(o.get("start_month")) or 1)
        g = (_num(o.get("annual_growth_pct")) or 0.0) / 100.0
        for m in range(max(1, start), horizon + 1):
            # Growth steps at horizon-year boundaries (months 13, 25, ...),
            # not at the line's own anniversary — matches annual budgeting.
            opex[m] += amt * (1.0 + g) ** ((m - 1) // 12)
    return opex


def _payroll(result: Result, drivers: dict, horizon: int) -> list:
    pay = [0.0] * (horizon + 1)
    for i, item in enumerate(_items(result, drivers, "payroll")):
        if not isinstance(item, dict):
            result.warn(f"payroll[{i}] is not an object; ignored")
            continue
        p = _unwrap_item(item)
        role = str(p.get("role") or f"role_{i + 1}")
        gross = _num(p.get("monthly_gross"))
        if gross is None:
            result.need(f"payroll[{i}].monthly_gross",
                        f"role '{role}' has no gross salary", 2)
            result.warn(f"payroll '{role}': no monthly_gross; excluded")
            continue
        count = _num(p.get("count"))
        count = 1.0 if count is None else count
        burden = _num(p.get("employer_burden_pct")) or 0.0
        if burden > 1.5:
            # A burden above 150% of gross is implausible as a fraction;
            # the author almost certainly meant percent.
            result.warn(f"payroll '{role}': employer_burden_pct={burden:g} read "
                        f"as percent; normalized to {burden / 100.0:g}")
            burden /= 100.0
        start = int(_num(p.get("start_month")) or 1)
        for m in range(max(1, start), horizon + 1):
            pay[m] += count * gross * (1.0 + burden)
    return pay


def _capex(result: Result, drivers: dict, horizon: int) -> "tuple[list, list]":
    dep = [0.0] * (horizon + 1)
    cash_out = [0.0] * (horizon + 1)
    for i, item in enumerate(_items(result, drivers, "capex")):
        if not isinstance(item, dict):
            result.warn(f"capex[{i}] is not an object; ignored")
            continue
        c = _unwrap_item(item)
        name = str(c.get("name") or f"capex_{i + 1}")
        amount = _num(c.get("amount"))
        if amount is None:
            result.warn(f"capex '{name}': no amount; excluded")
            continue
        month = int(_num(c.get("month")) or 1)
        if month < 1:
            result.warn(f"capex '{name}': month {month} < 1; treated as month 1")
            month = 1
        if month > horizon:
            result.warn(f"capex '{name}': month {month} is beyond the horizon; ignored")
            continue
        am = _num(c.get("amortization_months"))
        if am is None:
            am = 36.0
            result.warn(f"capex '{name}': amortization_months missing; assumed 36")
        am_i = int(am)
        cash_out[month] += amount
        if am_i < 1:
            result.warn(f"capex '{name}': amortization_months < 1; "
                        "no depreciation recorded")
            continue
        per = amount / am_i
        for m in range(month, min(horizon, month + am_i - 1) + 1):
            dep[m] += per
    return dep, cash_out


def _loans(result: Result, drivers: dict,
           horizon: int) -> "tuple[list, list, list]":
    interest = [0.0] * (horizon + 1)
    service = [0.0] * (horizon + 1)
    draw = [0.0] * (horizon + 1)
    for i, item in enumerate(_items(result, drivers, "loans")):
        if not isinstance(item, dict):
            result.warn(f"loans[{i}] is not an object; ignored")
            continue
        l = _unwrap_item(item)
        principal = _num(l.get("principal"))
        rate = _num(l.get("annual_rate"))
        nper = _num(l.get("months"))
        missing = [k for k, v in (("principal", principal), ("annual_rate", rate),
                                  ("months", nper)) if v is None]
        if missing:
            for k in missing:
                result.need(f"loans[{i}].{k}",
                            "principal, annual_rate and months define the schedule", 2)
            result.warn(f"loans[{i}]: missing {', '.join(missing)}; excluded")
            continue
        sched = amortization_schedule(principal, rate, int(nper))
        if sched is None:
            result.warn(f"loans[{i}]: amortization schedule undefined for "
                        f"principal={principal:g}, rate={rate:g}, "
                        f"months={int(nper)}; excluded")
            continue
        start = int(_num(l.get("start_month")) or 1)
        if start < 1:
            result.warn(f"loans[{i}]: start_month {start} < 1; treated as month 1")
            start = 1
        if start > horizon:
            result.warn(f"loans[{i}]: start_month {start} is beyond the horizon; ignored")
            continue
        draw[start] += principal
        for m in range(start, horizon + 1):
            k = m - start
            if k < len(sched):
                interest[m] += sched[k]["interest"]
                service[m] += sched[k]["payment"]
    return interest, service, draw


def _funding(result: Result, drivers: dict, horizon: int) -> list:
    fund = [0.0] * (horizon + 1)
    for i, item in enumerate(_items(result, drivers, "funding")):
        if not isinstance(item, dict):
            result.warn(f"funding[{i}] is not an object; ignored")
            continue
        f = _unwrap_item(item)
        amount = _num(f.get("amount"))
        if amount is None:
            result.warn(f"funding[{i}]: no amount; excluded")
            continue
        month = int(_num(f.get("month")) or 1)
        if 1 <= month <= horizon:
            fund[month] += amount
        else:
            result.warn(f"funding[{i}]: month {month} is outside the horizon; ignored")
    return fund


# ---------------------------------------------------------------------------
# The projection itself
# ---------------------------------------------------------------------------

def project(drivers: dict, months: "int | None" = None) -> Result:
    """Run the full cascade and return an un-finalized Result.

    `months` overrides drivers["months"] so scenario runners can shorten or
    stretch the horizon without mutating the driver dict they are varying.
    """
    if not isinstance(drivers, dict):
        raise SystemExit("drivers must be a JSON object (see projection.py docstring)")
    result = Result(script=SCRIPT)
    echo: dict = {}
    horizon = _resolve_months(drivers, months, result, echo)

    starting_cash = None
    if "starting_cash" in drivers:
        starting_cash = _num(unwrap(drivers.get("starting_cash"),
                                    "starting_cash", echo))
        if starting_cash is None:
            result.warn("starting_cash is present but not numeric; treated as unknown")
    currency = None
    if "currency" in drivers:
        raw_ccy = unwrap(drivers.get("currency"), "currency", echo)
        currency = str(raw_ccy) if raw_ccy is not None else None

    tax_rate = None
    if "tax_rate_pct" in drivers:
        tax_rate = _num(unwrap(drivers.get("tax_rate_pct"), "tax_rate_pct", echo))
    if tax_rate is None:
        tax_rate = 0.0
        result.need("tax_rate_pct",
                    "without it taxes are assumed 0 — net income and cash are "
                    "overstated", 3)
    elif tax_rate > 1.0:
        result.warn(f"tax_rate_pct={tax_rate:g} read as percent; "
                    f"normalized to {tax_rate / 100.0:g}")
        tax_rate /= 100.0
    elif tax_rate < 0:
        result.warn("negative tax_rate_pct clamped to 0")
        tax_rate = 0.0

    dso_shift = _month_shift(drivers, "dso_days", result, echo)
    dpo_shift = _month_shift(drivers, "dpo_days", result, echo)

    for key in _LIST_DRIVERS:
        if key in drivers and isinstance(drivers.get(key), list):
            echo[key] = {"value": f"{len(drivers[key])} defined", "status": "user"}
    result.inputs_echo = echo

    rev, var, usable = _revenue_streams(result, drivers, horizon)
    if usable == 0:
        # Nothing meaningful is computable without at least one revenue
        # stream — finalize() will read the empty results as INSUFFICIENT_DATA.
        result.need("activities",
                    "at least one activity with price and volume drives every "
                    "P&L and cash line", 1)
        if starting_cash is None:
            result.need("starting_cash",
                        "opening cash anchors the cash track and runway", 1)
        return result

    opex = _opex(result, drivers, horizon)
    pay = _payroll(result, drivers, horizon)
    if not drivers.get("opex_lines") and not drivers.get("payroll"):
        result.warn("no opex_lines or payroll defined — the fixed cost base is "
                    "zero, which flatters EBITDA")
    dep, capex_cash = _capex(result, drivers, horizon)
    interest, service, draw = _loans(result, drivers, horizon)
    fund = _funding(result, drivers, horizon)

    gm = [0.0] * (horizon + 1)
    ebitda = [0.0] * (horizon + 1)
    ni = [0.0] * (horizon + 1)
    tax = [0.0] * (horizon + 1)
    for m in range(1, horizon + 1):
        gm[m] = rev[m] - var[m]
        ebitda[m] = gm[m] - opex[m] - pay[m]
        ebit = ebitda[m] - dep[m]
        pretax = ebit - interest[m]
        tax[m] = max(0.0, pretax) * tax_rate
        ni[m] = pretax - tax[m]

    inflows = [0.0] * (horizon + 1)
    outflows = [0.0] * (horizon + 1)
    for m in range(1, horizon + 1):
        coll = rev[m - dso_shift] if m - dso_shift >= 1 else 0.0
        supp = (var[m - dpo_shift] + opex[m - dpo_shift]) if m - dpo_shift >= 1 else 0.0
        inflows[m] = coll + draw[m] + fund[m]
        outflows[m] = supp + pay[m] + tax[m] + capex_cash[m] + service[m]

    have_cash = starting_cash is not None
    cash: list = [None] * (horizon + 1)
    if have_cash:
        cash[0] = starting_cash
        for m in range(1, horizon + 1):
            cash[m] = cash[m - 1] + inflows[m] - outflows[m]

    present = [k for k in _SCHEMA_KEYS if k in drivers]

    monthly_rows = [{
        "m": m,
        "revenue": round(rev[m], 2),
        "gross_margin": round(gm[m], 2),
        "ebitda": round(ebitda[m], 2),
        "net_income": round(ni[m], 2),
        "cash": round(cash[m], 2) if have_cash else None,
    } for m in range(1, horizon + 1)]
    result.add_table("monthly", monthly_rows,
                     "accrual cascade + cash roll-forward per month")

    annual_rows = []
    annual_rev_total = 0.0
    for y in range(1, (horizon + 11) // 12 + 1):
        lo, hi = 12 * (y - 1) + 1, min(12 * y, horizon)
        yr_rev = sum(rev[lo:hi + 1])
        annual_rev_total += yr_rev
        annual_rows.append({
            "year": y,
            "revenue": round(yr_rev, 2),
            "gross_margin": round(sum(gm[lo:hi + 1]), 2),
            "ebitda": round(sum(ebitda[lo:hi + 1]), 2),
            "net_income": round(sum(ni[lo:hi + 1]), 2),
            "ending_cash": round(cash[hi], 2) if have_cash else None,
        })
    result.add_table("annual_summary", annual_rows,
                     "monthly cascade aggregated by year (partial final year kept)")

    last_negative = max((m for m in range(1, horizon + 1)
                         if ebitda[m] < -EPS), default=0)
    if guard(result, "breakeven_month", last_negative < horizon,
             "not reached within horizon"):
        result.add("breakeven_month", last_negative + 1,
                   "first month where EBITDA >= 0 and stays >= 0 through the horizon",
                   present, unit="month")

    if not have_cash:
        result.need("starting_cash",
                    "opening cash anchors the cash track — runway, minimum cash "
                    "and the zero-cash month all hang off it", 1)
        for metric in ("ending_cash", "min_cash", "min_cash_month",
                       "zero_cash_month", "runway_months"):
            result.skip(metric, "cash track not computed without starting_cash",
                        ["starting_cash"])
    else:
        result.add("ending_cash", cash[horizon],
                   "starting_cash + cumulative net cash flow", present,
                   unit=currency)
        min_cash = min(cash[1:horizon + 1])
        min_month = cash.index(min_cash, 1)
        result.add("min_cash", min_cash, "minimum monthly cash balance",
                   present, unit=currency)
        result.add("min_cash_month", min_month, "month of the cash low point",
                   present, unit="month")
        zero_month = next((m for m in range(1, horizon + 1)
                           if cash[m] < -EPS), None)
        result.add("zero_cash_month", zero_month,
                   "first month with negative cash; null = never within horizon",
                   present, unit="month")

        window = min(6, horizon)
        changes = [cash[m] - cash[m - 1]
                   for m in range(horizon - window + 1, horizon + 1)]
        avg_burn = sum(max(0.0, -c) for c in changes) / window
        if guard(result, "runway_months", avg_burn > EPS,
                 "cash-flow positive over trailing 6 months"):
            if guard(result, "runway_months", cash[horizon] > 0,
                     "cash already depleted at end of horizon"):
                result.add("runway_months", cash[horizon] / avg_burn,
                           "ending_cash / trailing-6-month average net burn "
                           "(avg of max(0, -net_cash_change))",
                           present, unit="months")

    # Invariants: the same economics summed two different ways must agree —
    # this is the tripwire for silent indexing or sign errors above.
    if have_cash:
        resum = starting_cash + sum(inflows[1:]) - sum(outflows[1:])
        result.invariant(
            "cash_roll_forward_ties",
            abs(resum - cash[horizon]) <= CASH_TOL,
            f"independent re-sum {round(resum, 4)} vs roll-forward "
            f"{round(cash[horizon], 4)}")
    gm_gap = max(abs(gm[m] - (rev[m] - var[m])) for m in range(1, horizon + 1))
    result.invariant("gross_margin_identity", gm_gap <= 1e-6,
                     f"max |gm - (revenue - variable)| = {gm_gap:.2e}")
    rev_total = sum(rev[1:])
    result.invariant("annual_equals_monthly_revenue",
                     abs(annual_rev_total - rev_total) <= CASH_TOL,
                     f"annual {round(annual_rev_total, 4)} vs monthly "
                     f"{round(rev_total, 4)}")
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_drivers(args) -> dict:
    sources = [s for s in (args.drivers_file, args.inputs, args.inputs_file) if s]
    if len(sources) > 1:
        raise SystemExit("pass exactly one of --drivers-file, --inputs, --inputs-file")
    if not sources:
        return {}
    src = sources[0]
    if src.strip().startswith("{"):
        raw = json.loads(src)
    else:
        with open(src, "r", encoding="utf-8") as f:
            raw = json.load(f)
    if not isinstance(raw, dict):
        raise SystemExit("drivers must be a JSON object (see projection.py docstring)")
    return raw


def _run(args, warnings: list) -> Result:
    return project(_load_drivers(args), months=args.months)


def _add_args(parser) -> None:
    parser.add_argument("--drivers-file",
                        help="path to a driver-schema JSON file (see module docstring)")
    parser.add_argument("--months", type=int,
                        help=f"horizon override, 1-{MAX_MONTHS} "
                             f"(default {DEFAULT_MONTHS})")


if __name__ == "__main__":
    cli(SCRIPT, "Monthly P&L + cash projection from a compact driver file "
                "(the Fisy cascade)", _run, add_args=_add_args)
