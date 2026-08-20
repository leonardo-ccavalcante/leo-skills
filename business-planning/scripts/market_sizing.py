"""market_sizing — bottom-up TAM/SAM/SOM chain with per-step provenance.

The input is one Tagged input named `steps`: an ORDERED list of tagged steps.
Each step is a dict with `name`, `value`, `status` (user|public|assumption|
unknown), optional `basis` / `source_url` / `source_date`, and optionally
`marks` — one of TAM | SAM | SOM | SOM_REVENUE, naming the level the chain has
reached at that step. The market size is the cumulative product down the chain:
a countable population, narrowed by rates (0-1), and finally priced.

    sellers 300000 (marks TAM) × 0.6 using software × 0.25 reachable (marks SAM)
    × 0.04 winnable (marks SOM) × 588 revenue/account (marks SOM_REVENUE)

Semantics:
- Cumulative product in list order. Counts (value > 1) must be positive; rates
  (0 < value <= 1) narrow the running total. A zero or negative step is a
  validation failure — it would silently zero every level downstream.
- Each `marks` boundary emits a result (`tam`, `sam`, `som`, `som_revenue`)
  equal to the cumulative product through that step. Duplicate marks fail.
- An `unknown` step (value null) TRUNCATES the chain: every step and every
  marks boundary downstream lands in `not_computed` naming the unknown step,
  and the unknown step itself lands in `missing` at priority 1. Levels reached
  before the truncation still compute — honesty about where knowledge ends,
  not all-or-nothing.
- Runtime tagging matches bp_common: a `public` step without `source_url` is
  downgraded to `assumption` with a warning.

Top-down guard (contractual — the shape "x% of the $N B market" is rejected,
exit 3). Detection heuristics, documented here because they are name/basis
based, not semantic:

1. A step is treated as a CURRENCY-DENOMINATED MARKET TOTAL when its name or
   basis contains a market word (market, tam) AND a currency signal
   ($ £ € R$ | usd eur gbp brl | value/size/worth alongside a B/M magnitude),
   e.g. "global_market_value_usd", basis "the $5B market".
2. A step is treated as a BARE SHARE step when its value is a rate
   (0 < v <= 1) AND its name or basis contains share language
   (share, market_share, penetration, capture, "% of ... market").

When the same chain contains both, the chain is top-down no matter what it is
called, and the script exits 3 with a corrective message pointing to the
bottom-up method. Ordinary bottom-up rate steps ("pct_using_accounting
_software") carry no share language and do not trip the guard.

Usage: market_sizing.py --inputs-file <f.bp.json> [--json]
"""

from __future__ import annotations

import re

from bp_common import (
    INPUT_STATUSES,
    Result,
    cli,
    gather_inputs,
)

SCRIPT = "market_sizing"

MARKS = ("TAM", "SAM", "SOM", "SOM_REVENUE")

_MARKET_WORD = re.compile(r"\b(market|tam)\b", re.IGNORECASE)
_CURRENCY_SIGNAL = re.compile(
    r"([$£€]|\bR\$|\b(usd|eur|gbp|brl)\b|\b(value|size|worth)\b)",
    re.IGNORECASE,
)
_SHARE_LANGUAGE = re.compile(
    r"(\bshare\b|market_?share|\bpenetration\b|\bcapture\b"
    r"|(%|pct|percent).{0,12}\bmarket\b)",
    re.IGNORECASE,
)


def _step_text(step: dict) -> str:
    return f"{step.get('name') or ''} {step.get('basis') or ''}"


def _is_currency_market_total(step: dict) -> bool:
    if step.get("value") is None:
        return False
    text = _step_text(step)
    return bool(_MARKET_WORD.search(text)) and bool(_CURRENCY_SIGNAL.search(text))


def _is_bare_share(step: dict) -> bool:
    v = step.get("value")
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return False
    if not (0 < v <= 1):
        return False
    return bool(_SHARE_LANGUAGE.search(_step_text(step)))


def _parse_steps(raw_steps: list, res: Result,
                 warnings: "list[str]") -> "list[dict] | None":
    """Validate and normalize the step list; None when validation failed."""
    steps: "list[dict]" = []
    seen_marks: "set[str]" = set()
    ok = True
    for i, raw in enumerate(raw_steps):
        if not isinstance(raw, dict):
            res.invariant(f"steps[{i}] is an object", False,
                          f"got {type(raw).__name__}")
            ok = False
            continue
        step = dict(raw)
        name = step.get("name")
        if not name or not isinstance(name, str):
            name = f"step_{i + 1}"
            res.warn(f"steps[{i}] has no name; called '{name}'")
            step["name"] = name
        status = step.get("status", "user")
        if status not in INPUT_STATUSES:
            res.invariant(f"step '{name}' has a legal status", False,
                          f"status '{status}' is not one of {INPUT_STATUSES}")
            ok = False
            continue
        if status == "public" and not step.get("source_url"):
            status = "assumption"
            step["basis"] = step.get("basis") or \
                "uncited public claim (no source_url provided)"
            warnings.append(
                f"step '{name}' was tagged public without source_url; "
                "downgraded to assumption — cite the source to restore it"
            )
        step["status"] = status
        value = step.get("value")
        if status == "unknown":
            if value is not None:
                res.invariant(f"step '{name}' unknown => null", False,
                              "status 'unknown' requires value null")
                ok = False
                continue
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                res.invariant(f"step '{name}' value numeric", False,
                              f"value {value!r} is not a number")
                ok = False
                continue
            if value <= 0:
                res.invariant(
                    f"step '{name}' value positive", False,
                    f"value {value} — counts must be positive and rates in "
                    "(0, 1]; a zero step zeroes every level downstream",
                )
                ok = False
                continue
        marks = step.get("marks")
        if marks is not None:
            if marks not in MARKS:
                res.invariant(f"step '{name}' marks legal", False,
                              f"marks '{marks}' is not one of {MARKS}")
                ok = False
                continue
            if marks in seen_marks:
                res.invariant(f"marks '{marks}' unique", False,
                              f"step '{name}' re-marks a level already marked")
                ok = False
                continue
            seen_marks.add(marks)
        steps.append(step)
    return steps if ok else None


def _run(args, warnings: "list[str]") -> Result:
    res = Result(script=SCRIPT)
    inputs = gather_inputs(args, warnings)
    res.echo_inputs(inputs)

    steps_tag = inputs.get("steps")
    if steps_tag is None or not steps_tag.is_known():
        res.need("steps",
                 "the ordered bottom-up chain (population, rates, price) is "
                 "the entire computation", priority=1)
        return res
    if not isinstance(steps_tag.value, list) or not steps_tag.value:
        res.invariant("steps is a non-empty list", False,
                      "steps.value must be a non-empty ordered list of step "
                      "objects")
        return res

    steps = _parse_steps(steps_tag.value, res, warnings)
    if steps is None:
        return res

    # Top-down guard: a currency-denominated market total combined with a bare
    # share step is the "x% of the $N market" shape — reject it whole.
    totals = [s["name"] for s in steps if _is_currency_market_total(s)]
    shares = [s["name"] for s in steps if _is_bare_share(s)]
    if totals and shares:
        res.invariant(
            "bottom_up_chain", False,
            f"top-down sizing detected: '{totals[0]}' looks like a "
            f"currency-denominated market total and '{shares[0]}' looks like "
            "a bare share of it. Rebuild bottom-up: start from a countable "
            "population (accounts, sellers, companies), narrow it with "
            "reachability rates in (0, 1], then price the winnable accounts "
            "(method: references/market-gtm.md).",
        )
        return res

    first_value = steps[0].get("value")
    if isinstance(first_value, (int, float)) and 0 < first_value <= 1:
        res.warn(f"chain starts with the rate step '{steps[0]['name']}' — "
                 "bottom-up chains normally start from a countable population")

    rows = []
    running = 1.0
    truncated_at: "str | None" = None
    level_values: "dict[str, float]" = {}
    level_step: "dict[str, str]" = {}
    names_used: "list[str]" = []
    for s in steps:
        row = {"name": s["name"], "value": s.get("value"),
               "status": s["status"], "marks": s.get("marks")}
        if truncated_at is None and s["status"] == "unknown":
            truncated_at = s["name"]
            res.need(s["name"],
                     "unknown step truncates the chain — every level "
                     "downstream depends on it", priority=1)
        elif s["status"] == "unknown":
            res.need(s["name"],
                     "also unknown; the chain is already truncated upstream",
                     priority=2)
        if truncated_at is None:
            running *= float(s["value"])
            names_used.append(s["name"])
            row["kind"] = "rate" if 0 < float(s["value"]) <= 1 else "count"
            row["cumulative"] = round(running, 6)
            if s.get("marks"):
                level_values[s["marks"]] = running
                level_step[s["marks"]] = s["name"]
        else:
            row["kind"] = None
            row["cumulative"] = None
            if s.get("marks"):
                res.skip(s["marks"].lower(),
                         f"chain truncated at unknown step '{truncated_at}'",
                         needed=[truncated_at])
        rows.append(row)

    res.add_table("chain", rows,
                  "cumulative product of the steps in order; truncated at the "
                  "first unknown step")

    for mark in MARKS:
        if mark in level_values:
            res.add(mark.lower(), level_values[mark],
                    f"cumulative product through step '{level_step[mark]}'",
                    names_used,
                    unit="revenue/period" if mark == "SOM_REVENUE" else "units")
    if not level_values and truncated_at is None:
        res.warn("no marks boundaries (TAM/SAM/SOM/SOM_REVENUE) in the chain — "
                 "only the raw cumulative product was computed")
    return res


if __name__ == "__main__":
    cli(SCRIPT, "Bottom-up TAM/SAM/SOM sizing chain with per-step provenance; "
                "rejects top-down '% of the $N market' shapes", _run)
