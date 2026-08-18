"""finmath — dependency-free financial math for the financial-analysis skill.

Pure stdlib. Every function returns None (never raises, never returns inf)
when the computation is undefined for the given inputs — callers translate
None into a `not_computed` entry with a reason.

IRR uses sign-change scanning + bisection on NPV, which handles every
realistic business cashflow more robustly than polynomial root finding.
"""

from __future__ import annotations

from typing import Callable


def npv(rate: float, cashflows: list[float]) -> float | None:
    """Net present value. cashflows[0] is t=0 (typically negative investment)."""
    if rate <= -1.0:
        return None
    return sum(cf / (1.0 + rate) ** t for t, cf in enumerate(cashflows))


def irr(cashflows: list[float], lo: float = -0.9999, hi: float = 10.0,
        tol: float = 1e-7, max_iter: int = 200) -> float | None:
    """Internal rate of return via bisection on NPV.

    Returns None when there is no sign change in [lo, hi] (e.g. all-positive
    or all-negative cashflows) — an honest "IRR undefined" beats a fabricated
    root.
    """
    if len(cashflows) < 2:
        return None
    has_pos = any(cf > 0 for cf in cashflows)
    has_neg = any(cf < 0 for cf in cashflows)
    if not (has_pos and has_neg):
        return None

    f_lo, f_hi = npv(lo, cashflows), npv(hi, cashflows)
    if f_lo is None or f_hi is None:
        return None
    if f_lo * f_hi > 0:
        # Scan for a bracketing interval before giving up.
        prev_r, prev_v = lo, f_lo
        steps = 100
        for i in range(1, steps + 1):
            r = lo + (hi - lo) * i / steps
            v = npv(r, cashflows)
            if v is None:
                continue
            if prev_v * v <= 0:
                lo, hi, f_lo, f_hi = prev_r, r, prev_v, v
                break
            prev_r, prev_v = r, v
        else:
            return None

    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        f_mid = npv(mid, cashflows)
        if f_mid is None:
            return None
        if abs(f_mid) < tol or (hi - lo) / 2.0 < tol:
            return mid
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2.0


def pmt(rate: float, nper: int, pv: float) -> float | None:
    """Constant periodic payment for a loan of pv over nper periods."""
    if nper <= 0:
        return None
    if rate == 0:
        return -pv / nper
    return -pv * rate * (1 + rate) ** nper / ((1 + rate) ** nper - 1)


def amortization_schedule(principal: float, annual_rate: float,
                          months: int) -> list[dict] | None:
    """Constant-payment schedule. Returns rows of
    {month, payment, interest, principal, balance}."""
    if principal <= 0 or months <= 0 or annual_rate < 0:
        return None
    r = annual_rate / 12.0
    payment = pmt(r, months, principal)
    if payment is None:
        return None
    payment = -payment
    rows, balance = [], principal
    for m in range(1, months + 1):
        interest = balance * r
        princ = payment - interest
        balance = max(0.0, balance - princ)
        rows.append({
            "month": m,
            "payment": round(payment, 2),
            "interest": round(interest, 2),
            "principal": round(princ, 2),
            "balance": round(balance, 2),
        })
    return rows


def cagr(begin: float, end: float, years: float) -> float | None:
    """Compound annual growth rate. Undefined for non-positive begin/years."""
    if begin <= 0 or years <= 0 or end < 0:
        return None
    return (end / begin) ** (1.0 / years) - 1.0


def payback_period(cashflows: list[float]) -> float | None:
    """Periods until cumulative cashflow crosses zero, linearly interpolated
    within the crossing period. None when it never crosses."""
    cum = 0.0
    for t, cf in enumerate(cashflows):
        prev = cum
        cum += cf
        if cum >= 0 and prev < 0:
            if cf == 0:
                return float(t)
            return t - 1 + (-prev / cf)
        if t == 0 and cum >= 0:
            return 0.0
    return None


def breakeven_units(fixed_costs: float, price: float,
                    unit_variable_cost: float) -> float | None:
    """Units to cover fixed costs. Undefined when contribution <= 0."""
    contribution = price - unit_variable_cost
    if contribution <= 0 or fixed_costs < 0:
        return None
    return fixed_costs / contribution


def bisect_solve(f: Callable[[float], float | None], target: float,
                 lo: float, hi: float, tol: float = 1e-6,
                 max_iter: int = 200) -> float | None:
    """Find x in [lo, hi] where f(x) == target, by bisection.

    Used by the reversal-threshold solver: f re-runs a model with one driver
    set to x and returns the metric. Returns None when f is undefined at the
    bounds or the target is not bracketed — meaning the verdict does NOT flip
    inside the searched range, which is itself a finding.
    """
    f_lo, f_hi = f(lo), f(hi)
    if f_lo is None or f_hi is None:
        return None
    g_lo, g_hi = f_lo - target, f_hi - target
    if g_lo == 0:
        return lo
    if g_hi == 0:
        return hi
    if g_lo * g_hi > 0:
        return None
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        f_mid = f(mid)
        if f_mid is None:
            return None
        g_mid = f_mid - target
        if abs(g_mid) < tol or (hi - lo) / 2.0 < tol:
            return mid
        if g_lo * g_mid <= 0:
            hi, g_hi = mid, g_mid
        else:
            lo, g_lo = mid, g_mid
    return (lo + hi) / 2.0
