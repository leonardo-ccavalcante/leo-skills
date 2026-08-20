"""readiness — 8-dimension business readiness score with an evidence floor.

Adapted from codex-startup-business-planner's readiness dimensions (MIT); the
evidence multipliers are OUR adaptation — engineering constants, golden-numbered
in selftest.py, never tuned to make a particular plan look better.

Each dimension is a Tagged input whose value is
{"score_0_5": <0-5>, "evidence": "validated|researched|assumption_heavy|unsupported"}.
The score says how strong the dimension is; the evidence level says how much the
score deserves to be believed. A confident 5 built on vibes is worth less than a
sober 3 built on customer interviews, and the multiplier makes that mechanical:

    dimension points = (score_0_5 / 5) × weight × evidence multiplier

Weights (total 100): problem_evidence 15 · icp_specificity 10 ·
reachable_market 10 · positioning 15 · model_pricing 15 · gtm 15 ·
unit_economics 10 · execution 10.
Multipliers: validated 1.00 · researched 0.75 · assumption_heavy 0.50 ·
unsupported 0.25.

All arithmetic runs in decimal (scores, weights, and multipliers are exact
decimals) so the rounding boundary is deterministic: the total is rounded
half-up to ONE decimal before banding, and the verdict reads the rounded
number. A raw 69.95 therefore bands as 70.0 = HEALTHY; a raw 39.95 bands as
40.0 = FRAGILE. Verdicts: HEALTHY ≥ 70 · FRAGILE 40–69 · UNSUSTAINABLE < 40.

Inputs that are not dimensions are ignored, and the script says so at most
once: the canonical state file carries every tagged input of the engagement,
so per-input warnings would drown the envelope. The single warning names the
count and appears only while a dimension is still missing — the case where a
mistyped dimension key is the likely cause.

Evidence floor (no override flag exists, on purpose): when ≥ 3 dimensions are
unknown/absent, or every provided dimension is unsupported, the arithmetic is
not trustworthy enough to band — verdict INSUFFICIENT_DATA, exit 2, no numeric
score. With 1–2 dimensions missing the score still computes, but the missing
dimensions contribute 0 points, so the result is a lower bound (warned).

Usage: readiness.py --inputs-file <f.bp.json> [--json]
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from bp_common import (
    EVIDENCE_LEVELS,
    Result,
    Tagged,
    cli,
    gather_inputs,
)

SCRIPT = "readiness"

# (dimension, weight) — order is the reporting order; weights total 100.
DIMENSIONS: "tuple[tuple[str, int], ...]" = (
    ("problem_evidence", 15),
    ("icp_specificity", 10),
    ("reachable_market", 10),
    ("positioning", 15),
    ("model_pricing", 15),
    ("gtm", 15),
    ("unit_economics", 10),
    ("execution", 10),
)

MULTIPLIERS = {
    "validated": Decimal("1.00"),
    "researched": Decimal("0.75"),
    "assumption_heavy": Decimal("0.50"),
    "unsupported": Decimal("0.25"),
}

EVIDENCE_FLOOR_MISSING = 3  # >= this many unknown/absent dims => INSUFFICIENT_DATA

WHY = {
    "problem_evidence": "is the problem real and painful? (interviews, waitlists, churn from alternatives)",
    "icp_specificity": "is the ideal customer specific enough to find and disqualify?",
    "reachable_market": "can the ICP actually be reached with the resources at hand?",
    "positioning": "why you, against the real alternatives (including doing nothing)?",
    "model_pricing": "does the revenue model and price point hold together?",
    "gtm": "is there a concrete, sequenced route to the first customers?",
    "unit_economics": "do the per-customer economics work? (delegate math to fa.sh)",
    "execution": "can this team ship this plan on this runway?",
}


def _round1_half_up(x: Decimal) -> float:
    return float(x.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _parse_dimension(name: str, tag: Tagged, res: Result) -> "tuple[Decimal, str] | None":
    """Return (score_0_5, evidence) or None; malformed input fails an invariant."""
    v = tag.value
    if not isinstance(v, dict):
        res.invariant(
            f"dimension '{name}' well-formed", False,
            'value must be {"score_0_5": 0-5, "evidence": "' +
            "|".join(EVIDENCE_LEVELS) + '"}',
        )
        return None
    score_raw = v.get("score_0_5")
    evidence = v.get("evidence")
    if isinstance(score_raw, bool) or not isinstance(score_raw, (int, float)):
        res.invariant(
            f"dimension '{name}' score numeric", False,
            f"score_0_5 is {score_raw!r} — it must be a number between 0 and 5",
        )
        return None
    score = Decimal(repr(score_raw))
    if score < 0 or score > 5:
        res.invariant(
            f"dimension '{name}' score in range", False,
            f"score_0_5 = {score_raw} is outside 0–5",
        )
        return None
    if evidence not in EVIDENCE_LEVELS:
        res.invariant(
            f"dimension '{name}' evidence legal", False,
            f"evidence {evidence!r} is not one of {EVIDENCE_LEVELS}",
        )
        return None
    return score, evidence


def _run(args, warnings: "list[str]") -> Result:
    res = Result(script=SCRIPT)
    inputs = gather_inputs(args, warnings)
    res.echo_inputs(inputs)

    known = set(d for d, _ in DIMENSIONS)
    extras = sorted(n for n in inputs if n not in known)

    scored: "dict[str, tuple[Decimal, str]]" = {}
    absent: "list[str]" = []
    for name, _weight in DIMENSIONS:
        tag = inputs.get(name)
        if tag is None or not tag.is_known():
            absent.append(name)
            continue
        parsed = _parse_dimension(name, tag, res)
        if parsed is not None:
            scored[name] = parsed

    # One warning for the whole tail, never one per input. The canonical
    # <slug>.bp.json holds EVERY tagged input of the engagement by convention
    # (SKILL.md step 2, and retro-score audits it that way), so most inputs are
    # legitimately not readiness dimensions — warning on each of them turns the
    # skill's own state format into 130 lines of noise. The count is still
    # worth naming when a dimension is missing, because a mistyped dimension
    # key hides in exactly that tail.
    if extras and absent:
        shown = ", ".join(extras[:3]) + (", …" if len(extras) > 3 else "")
        res.warn(
            f"{len(extras)} non-dimension input(s) ignored — readiness reads "
            f"only the 8 dimensions; check the {len(absent)} missing "
            f"dimension(s) for a mistyped key among them ({shown})"
        )

    # Malformed dimensions already failed invariants — let finalize() report
    # VALIDATION_FAILED rather than banding a partially-garbage score.
    if any(not i["passed"] for i in res.invariants):
        return res

    for name in absent:
        res.need(name, WHY[name], priority=1)

    all_unsupported = bool(scored) and all(
        ev == "unsupported" for _, ev in scored.values()
    )
    if len(absent) >= EVIDENCE_FLOOR_MISSING or not scored or all_unsupported:
        reason = (
            f"{len(absent)} of 8 dimensions are unknown/absent "
            f"(floor: {EVIDENCE_FLOOR_MISSING})"
            if len(absent) >= EVIDENCE_FLOOR_MISSING or not scored
            else "every provided dimension is evidence-level 'unsupported'"
        )
        res.skip("readiness_score", f"evidence floor: {reason}",
                 needed=absent or [d for d, _ in DIMENSIONS])
        res.skip("verdict", "no numeric verdict below the evidence floor — "
                            "gather evidence instead of arguing with a score",
                 needed=absent)
        # Empty results => finalize() reports INSUFFICIENT_DATA, exit 2.
        return res

    rows = []
    total = Decimal("0")
    for name, weight in DIMENSIONS:
        if name in scored:
            score, evidence = scored[name]
            mult = MULTIPLIERS[evidence]
            points = score / Decimal(5) * Decimal(weight) * mult
            total += points
            rows.append({
                "dimension": name,
                "weight": weight,
                "score_0_5": float(score),
                "evidence": evidence,
                "multiplier": float(mult),
                "points": float(points.quantize(Decimal("0.01"),
                                                rounding=ROUND_HALF_UP)),
            })
        else:
            rows.append({
                "dimension": name,
                "weight": weight,
                "score_0_5": None,
                "evidence": None,
                "multiplier": None,
                "points": None,
            })
    res.add_table(
        "dimension_breakdown", rows,
        "points = score_0_5/5 × weight × evidence multiplier "
        "(validated 1.00 · researched 0.75 · assumption_heavy 0.50 · "
        "unsupported 0.25)",
    )

    if absent:
        res.warn(
            f"{len(absent)} dimension(s) unscored ({', '.join(absent)}) — they "
            "contribute 0 points, so the score is a lower bound"
        )

    score_1dp = _round1_half_up(total)
    if score_1dp >= 70:
        verdict = "HEALTHY"
    elif score_1dp >= 40:
        verdict = "FRAGILE"
    else:
        verdict = "UNSUSTAINABLE"

    used = sorted(scored)
    res.add("readiness_score", score_1dp,
            "sum of dimension points, rounded half-up to 1 decimal before banding",
            used, unit="points (0-100)")
    res.add("verdict", verdict,
            "HEALTHY >= 70 · FRAGILE 40-69 · UNSUSTAINABLE < 40 "
            "(bands read the rounded score)", used)
    return res


if __name__ == "__main__":
    cli(SCRIPT, "8-dimension readiness score with evidence multipliers and an "
                "evidence floor (INSUFFICIENT_DATA beats a fake number)", _run)
