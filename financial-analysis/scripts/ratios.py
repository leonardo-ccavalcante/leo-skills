"""ratios — financial-statement ratio analysis.

Computes profitability, liquidity, solvency, and efficiency ratios plus
DuPont decomposition, a common-size income statement, and YoY deltas from
whatever subset of statement lines is known. Every ratio is guarded: a
zero denominator, negative equity, or missing line produces an honest
`not_computed` entry, never Infinity or a default.

Three deliberate choices:

1. Derivation cascade. gross_profit, operating_income, and ebitda are
   derived from upstream lines when absent (revenue - cogs, etc.) so the
   user is not interrogated for numbers already implied by what they gave.
   Each derivation is surfaced as a warning — a derived line is a
   calculation, not a fact the user stated.

2. Averages vs period-end. Turnover and days ratios properly use average
   balance-sheet values, which need a prior period. Without one, the
   script falls back to period-end values and says so — a labeled
   approximation beats refusing to compute anything.

3. DuPont uses period-end values throughout so the identity
   net_margin x asset_turnover x equity_multiplier == ROE holds exactly;
   an invariant check enforces the tie within 0.1pp. Mixing average-based
   turnover into the product would silently break the decomposition.

The YoY variance ladder maps |delta| to reporting depth — <5% "note",
5-10% "line", >10% "paragraph", >20% "escalate" — so the interactive
layer knows how much narrative each swing deserves.

Importable entry point: compute_ratios(inputs, prior) -> Result, so
scenarios.py can re-run the analysis with modified drivers without
shelling out.
"""

from __future__ import annotations

import os
import sys

# Keep sibling imports working when this module is imported from another
# directory (scenarios.py may be run from anywhere).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fin_common import (
    Result,
    Tagged,
    cli,
    gather_inputs,
    guard,
    load_inputs,
    num,
)

INCOME_FIELDS = (
    "revenue", "cogs", "gross_profit", "operating_expenses",
    "operating_income", "depreciation_amortization", "ebitda",
    "interest_expense", "pretax_income", "tax_expense", "net_income",
)
BALANCE_FIELDS = (
    "cash", "accounts_receivable", "inventory", "current_assets",
    "total_assets", "accounts_payable", "current_liabilities",
    "total_debt", "total_liabilities", "total_equity",
)
ALL_FIELDS = INCOME_FIELDS + BALANCE_FIELDS

PERIOD_END_WARNING = "using period-end values, not averages"

# (derived line, (minuend/addend, subtrahend/addend), sign, formula text).
# Order matters: each derivation may feed the next.
_DERIVATIONS = (
    ("gross_profit", ("revenue", "cogs"), -1, "revenue - cogs"),
    ("operating_income", ("gross_profit", "operating_expenses"), -1,
     "gross_profit - operating_expenses"),
    ("ebitda", ("operating_income", "depreciation_amortization"), +1,
     "operating_income + depreciation_amortization"),
)


def _resolve(inputs: dict[str, Tagged], result: Result | None = None,
             label: str = "") -> dict[str, float | None]:
    """Extract every statement line, filling standard derivations.

    Derivations are recorded as warnings because a derived number carries
    the combined uncertainty of its parents — the user should see it was
    computed, not stated.
    """
    v: dict[str, float | None] = {name: num(inputs, name) for name in ALL_FIELDS}
    for name, (a, b), sign, formula in _DERIVATIONS:
        if v[name] is None and v[a] is not None and v[b] is not None:
            v[name] = v[a] + sign * v[b]
            if result is not None:
                result.warn(f"{label}{name} derived as {formula}")
    return v


def _record_gaps(result: Result, cur: dict[str, float | None],
                 prior: dict[str, Tagged] | None) -> None:
    """Rank absent inputs by how much analysis each unblocks.

    Priorities are fixed by field so the interactive layer's question
    order is stable across partial states.
    """
    gaps = {
        "revenue": ("denominator for every margin and the common-size table", 1),
        "net_income": ("numerator for net margin, ROA, ROE, and DuPont", 1),
        "total_assets": ("needed for ROA, asset turnover, debt-to-assets, "
                         "and the equity multiplier", 2),
        "total_equity": ("needed for ROE, debt-to-equity, ROIC, and DuPont", 2),
        "current_liabilities": ("denominator for all liquidity ratios", 2),
        "inventory": ("needed for quick ratio and days inventory outstanding", 3),
    }
    for fieldname, (why, priority) in gaps.items():
        if cur[fieldname] is None:
            result.need(fieldname, why, priority)
    if prior is None:
        result.need("prior_period", "unlocks turnover ratios and YoY", 3)


def _avg_or_current(result: Result, cur: dict[str, float | None],
                    pri: dict[str, float | None] | None, field: str,
                    warn_fallback: bool = True):
    """Average of current and prior balance, else period-end value.

    Returns (value, label) where the label feeds the formula string so
    the output is explicit about which basis was used.
    """
    c = cur[field]
    if c is None:
        return None, field
    if pri is not None and pri[field] is not None:
        return (c + pri[field]) / 2.0, f"avg_{field}"
    if warn_fallback:
        result.warn(PERIOD_END_WARNING)
    return c, field


def _margin(result: Result, cur: dict[str, float | None], key: str,
            line: str) -> None:
    rev = cur["revenue"]
    val = cur[line]
    if rev is None:
        result.skip(key, "revenue unknown", ["revenue"])
        return
    if not guard(result, key, rev > 0, "revenue must be > 0", ["revenue"]):
        return
    if val is None:
        result.skip(key, f"{line} unknown and not derivable", [line])
        return
    result.add(key, val / rev * 100.0, f"{line} / revenue * 100",
               [line, "revenue"], unit="%")


def _variance_class(abs_delta_pct: float) -> str:
    if abs_delta_pct < 5.0:
        return "note"
    if abs_delta_pct <= 10.0:
        return "line"
    if abs_delta_pct <= 20.0:
        return "paragraph"
    return "escalate"


def compute_ratios(income_balance: dict[str, Tagged],
                   prior: dict[str, Tagged] | None = None) -> Result:
    """Compute all statement ratios derivable from the given lines."""
    prior = prior or None  # an empty dict is not a prior period
    result = Result(script="ratios")
    result.echo_inputs(income_balance)
    if prior:
        for k, t in prior.items():
            result.inputs_echo[f"prior.{k}"] = t.as_dict()

    cur = _resolve(income_balance, result)
    pri = _resolve(prior, result, label="prior ") if prior else None
    _record_gaps(result, cur, prior)

    rev = cur["revenue"]
    ni = cur["net_income"]
    opinc = cur["operating_income"]
    ebitda = cur["ebitda"]
    cogs = cur["cogs"]
    pretax = cur["pretax_income"]
    tax = cur["tax_expense"]
    interest = cur["interest_expense"]
    assets = cur["total_assets"]
    equity = cur["total_equity"]
    debt = cur["total_debt"]
    cash = cur["cash"]
    ca = cur["current_assets"]
    cl = cur["current_liabilities"]
    inv = cur["inventory"]
    ar = cur["accounts_receivable"]
    ap = cur["accounts_payable"]

    # --- Profitability: margins --------------------------------------------
    for key, line in (("gross_margin_pct", "gross_profit"),
                      ("operating_margin_pct", "operating_income"),
                      ("ebitda_margin_pct", "ebitda"),
                      ("net_margin_pct", "net_income")):
        _margin(result, cur, key, line)

    # --- Profitability: returns --------------------------------------------
    if ni is None:
        result.skip("roa", "net_income unknown", ["net_income"])
    else:
        # avg-or-current is the spec here, so no fallback warning: period-end
        # ROA is standard practice when only one balance sheet exists.
        basis, basis_label = _avg_or_current(result, cur, pri, "total_assets",
                                             warn_fallback=False)
        if basis is None:
            result.skip("roa", "total_assets unknown", ["total_assets"])
        elif guard(result, "roa", basis > 0, "total_assets must be > 0",
                   ["total_assets"]):
            result.add("roa", ni / basis * 100.0,
                       f"net_income / {basis_label} * 100",
                       ["net_income", "total_assets"], unit="%")

    roe_val: float | None = None
    if ni is None or equity is None:
        needed = [n for n, v in (("net_income", ni),
                                 ("total_equity", equity)) if v is None]
        result.skip("roe", "requires net_income and total_equity", needed)
    elif equity < 0:
        result.skip("roe", "negative equity — ROE not meaningful")
    elif guard(result, "roe", equity > 0, "total_equity is zero — ROE undefined",
               ["total_equity"]):
        roe_val = ni / equity * 100.0
        result.add("roe", roe_val, "net_income / total_equity * 100",
                   ["net_income", "total_equity"], unit="%")

    etr: float | None = None
    if pretax is None or tax is None:
        needed = [n for n, v in (("pretax_income", pretax),
                                 ("tax_expense", tax)) if v is None]
        result.skip("effective_tax_rate_pct",
                    "requires pretax_income and tax_expense", needed)
    elif guard(result, "effective_tax_rate_pct", pretax > 0,
               "pretax_income must be > 0 — effective tax rate not meaningful",
               ["pretax_income"]):
        etr = tax / pretax
        result.add("effective_tax_rate_pct", etr * 100.0,
                   "tax_expense / pretax_income * 100",
                   ["tax_expense", "pretax_income"], unit="%")

    if opinc is None or debt is None or equity is None or etr is None:
        needed = [n for n, v in (("operating_income", opinc),
                                 ("total_debt", debt),
                                 ("total_equity", equity)) if v is None]
        if etr is None:
            needed += ["tax_expense", "pretax_income"]
        result.skip("roic_approx",
                    "requires operating_income, total_debt, total_equity, "
                    "and an effective tax rate", needed)
    elif guard(result, "roic_approx", debt + equity > 0,
               "total_debt + total_equity must be > 0",
               ["total_debt", "total_equity"]):
        result.add("roic_approx", opinc * (1.0 - etr) / (debt + equity) * 100.0,
                   "operating_income * (1 - effective_tax_rate) / "
                   "(total_debt + total_equity) * 100",
                   ["operating_income", "tax_expense", "pretax_income",
                    "total_debt", "total_equity"], unit="%")

    # --- Liquidity ----------------------------------------------------------
    for key, numer, numer_desc, used in (
        ("current_ratio", ca, "current_assets", ["current_assets"]),
        ("cash_ratio", cash, "cash", ["cash"]),
    ):
        if cl is None:
            result.skip(key, "current_liabilities unknown",
                        ["current_liabilities"])
        elif guard(result, key, cl > 0, "current_liabilities must be > 0",
                   ["current_liabilities"]):
            if numer is None:
                result.skip(key, f"{numer_desc} unknown", used)
            else:
                result.add(key, numer / cl,
                           f"{numer_desc} / current_liabilities",
                           used + ["current_liabilities"], unit="x")

    if cl is None:
        result.skip("quick_ratio", "current_liabilities unknown",
                    ["current_liabilities"])
    elif guard(result, "quick_ratio", cl > 0,
               "current_liabilities must be > 0", ["current_liabilities"]):
        if ca is None:
            result.skip("quick_ratio", "current_assets unknown",
                        ["current_assets"])
        elif inv is None:
            result.skip("quick_ratio",
                        "inventory unknown — cannot distinguish quick from current",
                        ["inventory"])
        else:
            result.add("quick_ratio", (ca - inv) / cl,
                       "(current_assets - inventory) / current_liabilities",
                       ["current_assets", "inventory", "current_liabilities"],
                       unit="x")

    # --- Solvency -----------------------------------------------------------
    if debt is None or equity is None:
        needed = [n for n, v in (("total_debt", debt),
                                 ("total_equity", equity)) if v is None]
        result.skip("debt_to_equity", "requires total_debt and total_equity",
                    needed)
    elif guard(result, "debt_to_equity", equity > 0,
               "total_equity <= 0 — debt-to-equity not meaningful",
               ["total_equity"]):
        result.add("debt_to_equity", debt / equity, "total_debt / total_equity",
                   ["total_debt", "total_equity"], unit="x")

    if debt is None or assets is None:
        needed = [n for n, v in (("total_debt", debt),
                                 ("total_assets", assets)) if v is None]
        result.skip("debt_to_assets", "requires total_debt and total_assets",
                    needed)
    elif guard(result, "debt_to_assets", assets > 0, "total_assets must be > 0",
               ["total_assets"]):
        result.add("debt_to_assets", debt / assets, "total_debt / total_assets",
                   ["total_debt", "total_assets"], unit="x")

    if debt is None or cash is None or ebitda is None:
        needed = [n for n, v in (("total_debt", debt), ("cash", cash),
                                 ("ebitda", ebitda)) if v is None]
        result.skip("net_debt_to_ebitda",
                    "requires total_debt, cash, and ebitda", needed)
    elif guard(result, "net_debt_to_ebitda", ebitda > 0,
               "EBITDA <= 0 — leverage multiple not meaningful", ["ebitda"]):
        result.add("net_debt_to_ebitda", (debt - cash) / ebitda,
                   "(total_debt - cash) / ebitda",
                   ["total_debt", "cash", "ebitda"], unit="x")

    if opinc is None or interest is None:
        needed = [n for n, v in (("operating_income", opinc),
                                 ("interest_expense", interest)) if v is None]
        result.skip("interest_coverage",
                    "requires operating_income and interest_expense", needed)
    elif guard(result, "interest_coverage", interest > 0,
               "interest_expense must be > 0 — no debt service to cover",
               ["interest_expense"]):
        result.add("interest_coverage", opinc / interest,
                   "operating_income / interest_expense",
                   ["operating_income", "interest_expense"], unit="x")

    # --- Efficiency ---------------------------------------------------------
    if rev is None:
        result.skip("asset_turnover", "revenue unknown", ["revenue"])
    else:
        basis, basis_label = _avg_or_current(result, cur, pri, "total_assets")
        if basis is None:
            result.skip("asset_turnover", "total_assets unknown",
                        ["total_assets"])
        elif guard(result, "asset_turnover", basis > 0,
                   "total_assets must be > 0", ["total_assets"]):
            result.add("asset_turnover", rev / basis,
                       f"revenue / {basis_label}",
                       ["revenue", "total_assets"], unit="x")

    dso = dio = dpo = None
    if ar is None:
        result.skip("dso", "accounts_receivable unknown",
                    ["accounts_receivable"])
    elif rev is None:
        result.skip("dso", "revenue unknown", ["revenue"])
    elif guard(result, "dso", rev > 0, "revenue must be > 0", ["revenue"]):
        basis, basis_label = _avg_or_current(result, cur, pri,
                                             "accounts_receivable")
        dso = basis / rev * 365.0
        result.add("dso", dso, f"{basis_label} / revenue * 365",
                   ["accounts_receivable", "revenue"], unit="days")

    if inv is None:
        result.skip("dio", "inventory unknown", ["inventory"])
    elif cogs is None:
        result.skip("dio", "cogs unknown", ["cogs"])
    elif guard(result, "dio", cogs > 0, "cogs must be > 0", ["cogs"]):
        basis, basis_label = _avg_or_current(result, cur, pri, "inventory")
        dio = basis / cogs * 365.0
        result.add("dio", dio, f"{basis_label} / cogs * 365",
                   ["inventory", "cogs"], unit="days")

    if ap is None:
        result.skip("dpo", "accounts_payable unknown", ["accounts_payable"])
    elif cogs is None:
        result.skip("dpo", "cogs unknown", ["cogs"])
    elif guard(result, "dpo", cogs > 0, "cogs must be > 0", ["cogs"]):
        basis, basis_label = _avg_or_current(result, cur, pri,
                                             "accounts_payable")
        dpo = basis / cogs * 365.0
        result.add("dpo", dpo, f"{basis_label} / cogs * 365",
                   ["accounts_payable", "cogs"], unit="days")

    if dso is not None and dio is not None and dpo is not None:
        result.add("ccc", dso + dio - dpo, "dso + dio - dpo",
                   ["accounts_receivable", "inventory", "accounts_payable",
                    "revenue", "cogs"], unit="days")
    else:
        result.skip("ccc", "requires dso, dio, and dpo to all be computed")

    # --- DuPont (period-end values so the identity ties to ROE exactly) ----
    if assets is None or equity is None:
        needed = [n for n, v in (("total_assets", assets),
                                 ("total_equity", equity)) if v is None]
        result.skip("equity_multiplier", "requires total_assets and total_equity",
                    needed)
    elif guard(result, "equity_multiplier", equity > 0,
               "total_equity <= 0 — equity multiplier not meaningful",
               ["total_equity"]):
        result.add("equity_multiplier", assets / equity,
                   "total_assets / total_equity",
                   ["total_assets", "total_equity"], unit="x")

    dupont_ready = (ni is not None and rev is not None and rev > 0
                    and assets is not None and assets > 0
                    and equity is not None and equity > 0)
    if dupont_ready:
        roe_dupont = (ni / rev) * (rev / assets) * (assets / equity) * 100.0
        result.add("roe_dupont", roe_dupont,
                   "net_margin * asset_turnover(period-end) * "
                   "equity_multiplier * 100",
                   ["net_income", "revenue", "total_assets", "total_equity"],
                   unit="%")
        if roe_val is not None:
            diff = abs(roe_dupont - roe_val)
            result.invariant("roe_dupont ties to roe within 0.1pp",
                             diff <= 0.1,
                             f"|{roe_dupont:.4f} - {roe_val:.4f}| = {diff:.6f}pp")
    else:
        needed = [n for n, v in (("net_income", ni), ("revenue", rev),
                                 ("total_assets", assets),
                                 ("total_equity", equity)) if v is None]
        result.skip("roe_dupont",
                    "requires net_income, revenue > 0, total_assets > 0, "
                    "and total_equity > 0", needed)

    # 5-way extension: only meaningful when the interest layer is observable.
    if pretax is None or opinc is None or interest is None or ni is None:
        needed = [n for n, v in (("pretax_income", pretax),
                                 ("operating_income", opinc),
                                 ("interest_expense", interest),
                                 ("net_income", ni)) if v is None]
        result.skip("dupont_5way",
                    "5-way DuPont needs pretax_income, operating_income, "
                    "interest_expense, and net_income", needed)
    else:
        if guard(result, "tax_burden", pretax > 0,
                 "pretax_income must be > 0 — tax burden not meaningful",
                 ["pretax_income"]):
            result.add("tax_burden", ni / pretax, "net_income / pretax_income",
                       ["net_income", "pretax_income"], unit="x")
        if guard(result, "interest_burden", opinc > 0,
                 "operating_income must be > 0 — interest burden not meaningful",
                 ["operating_income"]):
            result.add("interest_burden", pretax / opinc,
                       "pretax_income / operating_income",
                       ["pretax_income", "operating_income"], unit="x")

    # --- Common-size income statement ---------------------------------------
    if rev is None:
        result.skip("common_size", "revenue unknown", ["revenue"])
    elif rev <= 0:
        result.skip("common_size", "revenue must be > 0")
    else:
        rows = [{"line": f, "value": cur[f],
                 "pct_of_revenue": round(cur[f] / rev * 100.0, 2)}
                for f in INCOME_FIELDS if cur[f] is not None]
        result.add_table("common_size", rows,
                         "each income-statement line / revenue * 100")

    # --- YoY deltas ---------------------------------------------------------
    if pri is None:
        result.skip("yoy_deltas", "no prior period provided", ["prior_period"])
    else:
        rows = []
        for f in ALL_FIELDS:
            c, p = cur[f], pri[f]
            if c is None or p is None:
                continue
            if p == 0:
                # Growth from zero has no percentage — flagged, not faked.
                rows.append({"metric": f, "current": c, "prior": p,
                             "delta_pct": None,
                             "variance_class": "undefined (prior is zero)"})
                continue
            delta_pct = (c - p) / abs(p) * 100.0
            rows.append({"metric": f, "current": c, "prior": p,
                         "delta_pct": round(delta_pct, 2),
                         "variance_class": _variance_class(abs(delta_pct))})
        if rows:
            result.add_table("yoy_deltas", rows,
                             "(current - prior) / |prior| * 100, classed "
                             "<5% note, 5-10% line, >10% paragraph, >20% escalate")
        else:
            result.skip("yoy_deltas",
                        "no line has both current and prior values")

    return result


def _add_args(parser) -> None:
    parser.add_argument("--prior-inputs",
                        help="inline JSON object of prior-period tagged inputs")
    parser.add_argument("--prior-inputs-file",
                        help="path to JSON file of prior-period tagged inputs")


def _run(args, warnings: list[str]) -> Result:
    inputs = gather_inputs(args, warnings)
    if args.prior_inputs and args.prior_inputs_file:
        raise SystemExit("pass either --prior-inputs or --prior-inputs-file, "
                         "not both")
    src = args.prior_inputs or args.prior_inputs_file
    prior = load_inputs(src, warnings) if src else None
    return compute_ratios(inputs, prior)


if __name__ == "__main__":
    cli("ratios",
        "Financial-statement ratio analysis: profitability, liquidity, "
        "solvency, efficiency, DuPont, common-size, and YoY deltas from "
        "tagged statement lines (all optional — computes what it can).",
        _run, add_args=_add_args)
