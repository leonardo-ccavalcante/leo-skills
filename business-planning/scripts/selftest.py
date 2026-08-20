"""selftest — golden-number tests for the business-planning scripts.

Anti-tuning rule (from the 10x playbook): every expected value below was
derived BY HAND before the code ran. If a refactor changes a number, re-derive
it by hand — never paste the code's new output into the test.

Structure: TESTS is a registry of (name, callable). Each module built in the
parallel wave (readiness, market_sizing, scenario_table, artifact_lint,
session_score) appends its golden tests in its own clearly-marked section.
A test passes by returning None and fails by raising AssertionError.

Usage: selftest.py            (exit 0 all green · 1 any failure)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile

import bp_common
from bp_common import Result, Tagged, num, parse_inputs

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run_validator(payload: dict) -> int:
    """Write payload to a temp .bp.json and return validate_state's exit code."""
    with tempfile.NamedTemporaryFile(
        "w", suffix=".bp.json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(payload, f)
        path = f.name
    try:
        proc = subprocess.run(
            [PY, os.path.join(SCRIPT_DIR, "validate_state.py"), path, "--json"],
            capture_output=True, text=True,
        )
        return proc.returncode
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# bp_common golden tests (keystone)
# ---------------------------------------------------------------------------

def t_bare_scalar_autotags_user():
    w: list[str] = []
    out = parse_inputs({"price": 49}, w)
    assert out["price"].status == "user" and out["price"].value == 49
    assert len(w) == 1 and "untagged" in w[0]


def t_public_without_url_downgrades():
    w: list[str] = []
    out = parse_inputs(
        {"market_size": {"value": 1000, "status": "public"}}, w
    )
    assert out["market_size"].status == "assumption"
    assert "uncited public claim" in (out["market_size"].basis or "")
    assert any("downgraded to assumption" in x for x in w)


def t_public_with_url_kept():
    w: list[str] = []
    out = parse_inputs(
        {"sellers": {"value": 300000, "status": "public",
                     "source_url": "https://example.gov/stats",
                     "source_date": "2026-08-19"}}, w
    )
    assert out["sellers"].status == "public"
    assert out["sellers"].source_date == "2026-08-19"
    assert w == []


def t_unknown_with_value_raises():
    try:
        parse_inputs({"churn": {"value": 0.03, "status": "unknown"}})
    except ValueError:
        return
    raise AssertionError("unknown with a value must raise")


def t_null_value_downgrades_to_unknown():
    w: list[str] = []
    out = parse_inputs({"cac": {"value": None, "status": "user"}}, w)
    assert out["cac"].status == "unknown" and not out["cac"].is_known()
    assert any("treated as unknown" in x for x in w)


def t_bad_confidence_raises():
    try:
        parse_inputs({"x": {"value": 1, "status": "user", "confidence": "sure"}})
    except ValueError:
        return
    raise AssertionError("illegal confidence must raise")


def t_num_helper():
    inputs = parse_inputs({
        "a": {"value": 2.5, "status": "user"},
        "b": {"value": None, "status": "unknown"},
        "c": {"value": "not-a-number", "status": "user"},
    })
    assert num(inputs, "a") == 2.5
    assert num(inputs, "b") is None
    assert num(inputs, "c") is None
    assert num(inputs, "absent") is None


def t_envelope_insufficient_when_empty():
    r = Result(script="t")
    code = r.finalize()
    assert code == bp_common.EXIT_INSUFFICIENT and r.status == "INSUFFICIENT_DATA"


def t_envelope_validation_beats_results():
    r = Result(script="t")
    r.add("x", 1.0, "1", [])
    r.invariant("must-hold", False, "broken")
    code = r.finalize()
    assert code == bp_common.EXIT_VALIDATION and r.status == "VALIDATION_FAILED"


def t_envelope_partial_when_missing():
    r = Result(script="t")
    r.add("x", 1.0, "1", [])
    r.need("y", "needed for z", priority=1)
    code = r.finalize()
    assert code == bp_common.EXIT_OK and r.status == "PARTIAL"


def t_envelope_rejects_nonfinite():
    r = Result(script="t")
    r.add("bad", float("inf"), "1/0", [])
    assert "bad" not in r.results
    assert any(nc["metric"] == "bad" for nc in r.not_computed)


# ---------------------------------------------------------------------------
# validate_state golden tests (keystone)
# ---------------------------------------------------------------------------

GOOD_STATE = {
    "meta": {"slug": "demo", "route": "MODULE", "stage": "idea",
             "depth": "starter"},
    "inputs": {
        "price": {"value": 49, "status": "user"},
        "sellers": {"value": 300000, "status": "public",
                    "source_url": "https://example.gov/stats",
                    "source_date": "2026-08-19"},
        "conversion": {"value": 0.02, "status": "assumption",
                       "basis": "no data yet; standard planning placeholder "
                                "to be replaced by a real test"},
        "churn": {"value": None, "status": "unknown"},
    },
}


def t_validator_accepts_good_state():
    assert run_validator(GOOD_STATE) == 0


def t_validator_rejects_uncited_public():
    bad = json.loads(json.dumps(GOOD_STATE))
    del bad["inputs"]["sellers"]["source_url"]
    assert run_validator(bad) == 3


def t_validator_rejects_undated_public():
    bad = json.loads(json.dumps(GOOD_STATE))
    del bad["inputs"]["sellers"]["source_date"]
    assert run_validator(bad) == 3


def t_validator_rejects_bare_scalar():
    bad = json.loads(json.dumps(GOOD_STATE))
    bad["inputs"]["price"] = 49
    assert run_validator(bad) == 3


def t_validator_rejects_baseless_assumption():
    bad = json.loads(json.dumps(GOOD_STATE))
    del bad["inputs"]["conversion"]["basis"]
    assert run_validator(bad) == 3


def t_validator_rejects_unknown_with_value():
    bad = json.loads(json.dumps(GOOD_STATE))
    bad["inputs"]["churn"]["value"] = 0.05
    assert run_validator(bad) == 3


def t_validator_rejects_bad_route():
    bad = json.loads(json.dumps(GOOD_STATE))
    bad["meta"]["route"] = "MEGA-PLAN"
    assert run_validator(bad) == 3


def t_lint_prose_precision_spares_a_figure_with_nothing_to_round():
    # The carve-out and its narrowness, in one document. Hand-derived:
    #   "0,007%"    — head "0" is all zeros, so the three-digit tail is the
    #                 fraction, not a thousands group => 3 decimals, > 2; but
    #                 Decimal("0.007").normalize() has ONE significant digit,
    #                 <= MAX_PROSE_SIGDIGS, so it is exempt. Rounding it to
    #                 two decimals would turn a real difference into 0,01%.
    #   "0,698018"  — 6 decimals, > 2, and six significant digits, > 3
    #                 => 1 prose_precision violation. This is the figure a
    #                 blind reviewer quoted back from iteration 2.
    # The exemption is about over-precision, not about small numbers: both
    # figures are sub-unit and only one is reported. Expected: 1 violation
    # at the second line, exit 3.
    body = ("A diferença entre os dois censos é de 754 pessoas (0,007%).\n\n"
            "O ponto de equilíbrio fica abaixo de 0,698018 do volume base.")
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", _precision_doc(body, sources_rows=(
            "| diferença censitária | 0,007% | IBGE 2022 |\n")))
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 3, d["results"]
        v = d["results"]["violations"]["value"]
        assert [x["check"] for x in v] == ["prose_precision"], v
        assert "0,698018" in v[0]["detail"], v[0]["detail"]


TESTS: list[tuple[str, object]] = [
    ("bare scalar auto-tags user", t_bare_scalar_autotags_user),
    ("public w/o url downgrades to assumption", t_public_without_url_downgrades),
    ("public with url+date kept", t_public_with_url_kept),
    ("unknown with value raises", t_unknown_with_value_raises),
    ("null value downgrades to unknown", t_null_value_downgrades_to_unknown),
    ("bad confidence raises", t_bad_confidence_raises),
    ("num() helper", t_num_helper),
    ("envelope: empty => INSUFFICIENT_DATA", t_envelope_insufficient_when_empty),
    ("envelope: failed invariant => exit 3", t_envelope_validation_beats_results),
    ("envelope: missing => PARTIAL", t_envelope_partial_when_missing),
    ("envelope: non-finite rejected", t_envelope_rejects_nonfinite),
    ("validator accepts good state", t_validator_accepts_good_state),
    ("validator rejects uncited public", t_validator_rejects_uncited_public),
    ("validator rejects undated public", t_validator_rejects_undated_public),
    ("validator rejects bare scalar", t_validator_rejects_bare_scalar),
    ("validator rejects baseless assumption", t_validator_rejects_baseless_assumption),
    ("validator rejects unknown-with-value", t_validator_rejects_unknown_with_value),
    ("validator rejects bad meta.route", t_validator_rejects_bad_route),
]

# --- readiness golden tests (added by WP-A) --------------------------------

# Shared WP-A helpers: run a module CLI exactly as bp.sh would and return
# (exit_code, parsed_json_or_None).

def _wpa_run(mod: str, argv: "list[str]") -> "tuple[int, dict | None]":
    proc = subprocess.run(
        [PY, os.path.join(SCRIPT_DIR, mod)] + argv,
        capture_output=True, text=True,
    )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = None
    return proc.returncode, data


def _wpa_run_inputs(mod: str, inputs: dict) -> "tuple[int, dict | None]":
    with tempfile.NamedTemporaryFile(
        "w", suffix=".bp.json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"inputs": inputs}, f)
        path = f.name
    try:
        return _wpa_run(mod, ["--inputs-file", path, "--json"])
    finally:
        os.unlink(path)


READINESS_DIMS = ("problem_evidence", "icp_specificity", "reachable_market",
                  "positioning", "model_pricing", "gtm", "unit_economics",
                  "execution")


def _dim(score, evidence):
    return {"value": {"score_0_5": score, "evidence": evidence},
            "status": "user"}


def t_readiness_full_mixed():
    # Hand-derived (weights pe15 icp10 rm10 pos15 mp15 gtm15 ue10 ex10;
    # multipliers validated 1.00 / researched .75 / assumption_heavy .50 /
    # unsupported .25; points = score/5 × weight × mult):
    #   problem_evidence 4 researched        4/5×15×0.75 =  9.00
    #   icp_specificity  5 validated         5/5×10×1.00 = 10.00
    #   reachable_market 3 assumption_heavy  3/5×10×0.50 =  3.00
    #   positioning      4 researched        4/5×15×0.75 =  9.00
    #   model_pricing    2 unsupported       2/5×15×0.25 =  1.50
    #   gtm              3 researched        3/5×15×0.75 =  6.75
    #   unit_economics   1 assumption_heavy  1/5×10×0.50 =  1.00
    #   execution        4 validated         4/5×10×1.00 =  8.00
    #   total = 48.25 -> round half-up to 1dp = 48.3 -> FRAGILE (40-69)
    inputs = {
        "problem_evidence": _dim(4, "researched"),
        "icp_specificity": _dim(5, "validated"),
        "reachable_market": _dim(3, "assumption_heavy"),
        "positioning": _dim(4, "researched"),
        "model_pricing": _dim(2, "unsupported"),
        "gtm": _dim(3, "researched"),
        "unit_economics": _dim(1, "assumption_heavy"),
        "execution": _dim(4, "validated"),
    }
    code, d = _wpa_run_inputs("readiness.py", inputs)
    assert code == 0 and d is not None and d["status"] == "OK"
    assert d["results"]["readiness_score"]["value"] == 48.3
    assert d["results"]["verdict"]["value"] == "FRAGILE"
    rows = d["results"]["dimension_breakdown"]["value"]
    assert len(rows) == 8
    by_dim = {r["dimension"]: r for r in rows}
    assert by_dim["gtm"]["points"] == 6.75
    assert by_dim["model_pricing"]["points"] == 1.5


def t_readiness_boundary_exactly_70():
    # All eight dimensions 3.5 validated: 3.5/5 = 0.7; 0.7 × Σweights(100)
    # = 70.00 exactly -> HEALTHY (>= 70). Decimal arithmetic keeps the
    # boundary exact; float would give 69.999... here.
    inputs = {dm: _dim(3.5, "validated") for dm in READINESS_DIMS}
    code, d = _wpa_run_inputs("readiness.py", inputs)
    assert code == 0 and d["results"]["readiness_score"]["value"] == 70.0
    assert d["results"]["verdict"]["value"] == "HEALTHY"


def t_readiness_boundary_exactly_40():
    # All eight dimensions 2 validated: 2/5 = 0.4; 0.4 × 100 = 40.00
    # exactly -> FRAGILE (the 40 band is inclusive on the low edge).
    inputs = {dm: _dim(2, "validated") for dm in READINESS_DIMS}
    code, d = _wpa_run_inputs("readiness.py", inputs)
    assert code == 0 and d["results"]["readiness_score"]["value"] == 40.0
    assert d["results"]["verdict"]["value"] == "FRAGILE"


def t_readiness_unsustainable():
    # All eight dimensions 1 validated: 1/5 = 0.2; 0.2 × 100 = 20.00
    # -> UNSUSTAINABLE (< 40).
    inputs = {dm: _dim(1, "validated") for dm in READINESS_DIMS}
    code, d = _wpa_run_inputs("readiness.py", inputs)
    assert code == 0 and d["results"]["readiness_score"]["value"] == 20.0
    assert d["results"]["verdict"]["value"] == "UNSUSTAINABLE"


def t_readiness_insufficient_three_unknown():
    # 2 unknown + 1 absent = 3 dimensions without evidence -> the floor
    # trips: exit 2, no numeric score, the gaps ranked at priority 1.
    inputs = {dm: _dim(4, "validated") for dm in READINESS_DIMS
              if dm not in ("icp_specificity", "reachable_market", "gtm")}
    inputs["icp_specificity"] = {"value": None, "status": "unknown"}
    inputs["reachable_market"] = {"value": None, "status": "unknown"}
    code, d = _wpa_run_inputs("readiness.py", inputs)
    assert code == 2 and d["status"] == "INSUFFICIENT_DATA"
    assert "readiness_score" not in d["results"]
    p1 = {m["field"] for m in d["missing"] if m["priority"] == 1}
    assert {"icp_specificity", "reachable_market", "gtm"} <= p1


def t_readiness_all_unsupported_floor():
    # Every dimension provided, every one unsupported: the arithmetic would
    # produce a number, and the floor refuses to band it. Exit 2.
    inputs = {dm: _dim(5, "unsupported") for dm in READINESS_DIMS}
    code, d = _wpa_run_inputs("readiness.py", inputs)
    assert code == 2 and d["status"] == "INSUFFICIENT_DATA"
    assert "verdict" not in d["results"]


def t_readiness_partial_one_missing():
    # One absent dimension: score still computes as a lower bound (absent
    # contributes 0), status PARTIAL, the gap listed at priority 1.
    # Hand math: seven dims at 4 validated = 0.8 × (100 - 15) = 68.0
    # (problem_evidence absent) -> FRAGILE.
    inputs = {dm: _dim(4, "validated") for dm in READINESS_DIMS
              if dm != "problem_evidence"}
    code, d = _wpa_run_inputs("readiness.py", inputs)
    assert code == 0 and d["status"] == "PARTIAL"
    assert d["results"]["readiness_score"]["value"] == 68.0
    assert d["results"]["verdict"]["value"] == "FRAGILE"
    assert d["missing"][0]["field"] == "problem_evidence"
    assert d["missing"][0]["priority"] == 1


def t_readiness_bad_evidence_rejected():
    inputs = {dm: _dim(3, "validated") for dm in READINESS_DIMS}
    inputs["gtm"] = _dim(3, "vibes")
    code, _d = _wpa_run_inputs("readiness.py", inputs)
    assert code == 3


TESTS += [
    ("readiness: mixed case 48.25 -> 48.3 FRAGILE", t_readiness_full_mixed),
    ("readiness: boundary exactly 70 -> HEALTHY", t_readiness_boundary_exactly_70),
    ("readiness: boundary exactly 40 -> FRAGILE", t_readiness_boundary_exactly_40),
    ("readiness: 20.0 -> UNSUSTAINABLE", t_readiness_unsustainable),
    ("readiness: 3 unknown/absent => exit 2", t_readiness_insufficient_three_unknown),
    ("readiness: all unsupported => exit 2", t_readiness_all_unsupported_floor),
    ("readiness: 1 missing => PARTIAL lower bound", t_readiness_partial_one_missing),
    ("readiness: illegal evidence => exit 3", t_readiness_bad_evidence_rejected),
]


# --- market_sizing golden tests (added by WP-A) ----------------------------

def _steps_input(steps):
    return {"steps": {"value": steps, "status": "user"}}


def t_market_full_chain():
    # Hand-derived cumulative product:
    #   300000 sellers                      (marks TAM     -> 300000)
    #   × 0.6 using accounting software     -> 180000
    #   × 0.25 reachable segment            (marks SAM     -> 45000)
    #   × 0.04 winnable in 3y               (marks SOM     -> 1800)
    #   × 588 annual revenue per account    (marks SOM_REVENUE -> 1800 × 588
    #                                        = 1,058,400)
    steps = [
        {"name": "uk_ecommerce_sellers", "value": 300000, "status": "public",
         "source_url": "https://example.gov/stats",
         "source_date": "2026-08-19", "marks": "TAM"},
        {"name": "pct_using_accounting_software", "value": 0.6,
         "status": "assumption", "basis": "placeholder pending survey"},
        {"name": "pct_reachable_segment", "value": 0.25,
         "status": "assumption", "basis": "segment filter", "marks": "SAM"},
        {"name": "pct_winnable_3yr", "value": 0.04, "status": "assumption",
         "basis": "sales capacity", "marks": "SOM"},
        {"name": "annual_rev_per_account", "value": 588,
         "status": "assumption", "basis": "£49/mo standard tier",
         "marks": "SOM_REVENUE"},
    ]
    code, d = _wpa_run_inputs("market_sizing.py", _steps_input(steps))
    assert code == 0 and d["status"] == "OK"
    r = d["results"]
    assert r["tam"]["value"] == 300000.0
    assert r["sam"]["value"] == 45000.0
    assert r["som"]["value"] == 1800.0
    assert r["som_revenue"]["value"] == 1058400.0
    chain = r["chain"]["value"]
    assert [row["cumulative"] for row in chain] == \
        [300000.0, 180000.0, 45000.0, 1800.0, 1058400.0]


def t_market_truncation_at_unknown():
    # The unknown SAM step truncates: TAM (upstream) computes; SAM and
    # SOM_REVENUE (downstream) land in not_computed naming the step; the
    # step itself is the priority-1 missing input.
    steps = [
        {"name": "uk_ecommerce_sellers", "value": 300000, "status": "user",
         "marks": "TAM"},
        {"name": "pct_reachable_segment", "value": None, "status": "unknown",
         "marks": "SAM"},
        {"name": "annual_rev_per_account", "value": 588,
         "status": "assumption", "basis": "tier price",
         "marks": "SOM_REVENUE"},
    ]
    code, d = _wpa_run_inputs("market_sizing.py", _steps_input(steps))
    assert code == 0 and d["status"] == "PARTIAL"
    assert d["results"]["tam"]["value"] == 300000.0
    assert "sam" not in d["results"] and "som_revenue" not in d["results"]
    nc = {x["metric"]: x for x in d["not_computed"]}
    assert "sam" in nc and "som_revenue" in nc
    assert "pct_reachable_segment" in nc["som_revenue"]["reason"]
    assert d["missing"][0]["field"] == "pct_reachable_segment"
    assert d["missing"][0]["priority"] == 1


def t_market_topdown_rejected():
    # "1% of the $5B market": currency-denominated total + bare share step
    # => exit 3 with a corrective message pointing at the bottom-up method.
    steps = [
        {"name": "global_market_value_usd", "value": 5000000000,
         "status": "assumption", "basis": "the $5B market", "marks": "TAM"},
        {"name": "our_market_share", "value": 0.01, "status": "assumption",
         "basis": "1% capture"},
    ]
    code, d = _wpa_run_inputs("market_sizing.py", _steps_input(steps))
    assert code == 3 and d["status"] == "VALIDATION_FAILED"
    failed = [i for i in d["invariants"] if not i["passed"]]
    assert any("bottom-up" in i["detail"] for i in failed)


def t_market_zero_step_rejected():
    steps = [
        {"name": "sellers", "value": 300000, "status": "user", "marks": "TAM"},
        {"name": "pct_reachable", "value": 0, "status": "user"},
    ]
    code, _d = _wpa_run_inputs("market_sizing.py", _steps_input(steps))
    assert code == 3


TESTS += [
    ("market: full chain hand-derived", t_market_full_chain),
    ("market: unknown step truncates", t_market_truncation_at_unknown),
    ("market: top-down shape => exit 3", t_market_topdown_rejected),
    ("market: zero step => exit 3", t_market_zero_step_rejected),
]


# --- scenario_table golden tests (added by WP-A) ---------------------------

_SCENARIO_BASE = {
    "months": 12,
    "starting_cash": 10000,
    "activities": [{"name": "subscriptions", "price": 100,
                    "unit_variable_cost": 10, "volume_start": 10,
                    "volume_growth_pct_monthly": 5}],
    "opex_lines": [{"name": "hosting", "monthly_amount": 200}],
    "tax_rate_pct": 0.15,
}


def _scenario_inputs(multipliers):
    return {
        "base_drivers": {"value": _SCENARIO_BASE, "status": "user",
                         "basis": "drafted in session"},
        "multipliers": {"value": multipliers, "status": "assumption",
                        "basis": "standard band"},
    }


def t_scenario_happy_path():
    # Hand-derived mutations: conservative price 100×0.9=90, volume 10×0.7=7;
    # base untouched; optimistic volume 10×1.3=13 (price unchanged).
    mults = {
        "conservative": {"volume": 0.7, "price": 0.9},
        "base": {"volume": 1.0, "price": 1.0},
        "optimistic": {"volume": 1.3},
    }
    code, d = _wpa_run_inputs("scenario_table.py", _scenario_inputs(mults))
    assert code == 0 and d["status"] == "OK"
    df = d["results"]["driver_files"]["value"]
    assert set(df) == {"conservative", "base", "optimistic"}
    assert df["conservative"]["activities"][0]["price"] == 90.0
    assert df["conservative"]["activities"][0]["volume_start"] == 7.0
    assert df["base"]["activities"][0]["price"] == 100
    assert df["base"]["activities"][0]["volume_start"] == 10
    assert df["optimistic"]["activities"][0]["volume_start"] == 13.0
    assert df["optimistic"]["activities"][0]["price"] == 100
    # Untouched structure survives for fa.sh (starting_cash, opex, tax).
    assert df["conservative"]["starting_cash"] == 10000
    assert df["conservative"]["opex_lines"][0]["monthly_amount"] == 200
    table = {r["driver"]: r for r in
             d["results"]["assumption_table"]["value"]}
    assert table["volume"]["conservative"] == 0.7
    assert table["volume"]["base"] == 1.0
    assert table["volume"]["optimistic"] == 1.3
    assert table["price"]["optimistic"] == 1.0  # omitted resolves to 1.0


def t_scenario_base_not_one_rejected():
    mults = {"conservative": {"volume": 0.7},
             "base": {"volume": 1.1},
             "optimistic": {"volume": 1.3}}
    code, d = _wpa_run_inputs("scenario_table.py", _scenario_inputs(mults))
    assert code == 3 and d["status"] == "VALIDATION_FAILED"
    failed = [i for i in d["invariants"] if not i["passed"]]
    assert any("pinned at 1.0" in i["check"] for i in failed)


def t_scenario_missing_scenario_rejected():
    mults = {"conservative": {"volume": 0.7}, "base": {"volume": 1.0}}
    code, _d = _wpa_run_inputs("scenario_table.py", _scenario_inputs(mults))
    assert code == 3


def t_scenario_extra_scenario_rejected():
    mults = {"conservative": {"volume": 0.7}, "base": {},
             "optimistic": {"volume": 1.3}, "worst": {"volume": 0.5}}
    code, _d = _wpa_run_inputs("scenario_table.py", _scenario_inputs(mults))
    assert code == 3


TESTS += [
    ("scenarios: happy path emits fa driver files", t_scenario_happy_path),
    ("scenarios: base multiplier != 1.0 => exit 3",
     t_scenario_base_not_one_rejected),
    ("scenarios: missing scenario => exit 3",
     t_scenario_missing_scenario_rejected),
    ("scenarios: extra scenario => exit 3", t_scenario_extra_scenario_rejected),
]


# --- artifact_lint golden tests (added by WP-A) ----------------------------

_CLEAN_PLAN = """---
research_sources: 4
confidence_level: MEDIUM
stage: validating
mode: pre-revenue
---
# Demo plan

Pricing lands at £49/mo, which puts SOM revenue at $1,058,400.
<!-- bp-lint: allow -->
Setup fees add roughly $500 in month one.

## Assumptions & Limitations

Churn is unknown until the first cohort completes.

## Sources

| claim | figure | source |
|---|---|---|
| standard tier | £49 | pricing draft |
| SOM revenue | $1058400 | market.json |
"""


def _write(dirpath: str, name: str, content: str) -> str:
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def t_lint_clean_fixture_passes():
    with tempfile.TemporaryDirectory() as td:
        _write(td, "plan.md", _CLEAN_PLAN)
        # sources.md is excluded by design — an uncovered figure here must
        # not fail the lint.
        _write(td, "sources.md", "# Sources\n$999 archive-only figure.\n")
        code, d = _wpa_run("artifact_lint.py", [td, "--json"])
        assert code == 0 and d["results"]["violation_count"]["value"] == 0
        assert d["results"]["files_linted"]["value"] == 1


def t_lint_catches_each_violation_class():
    bad = """---
research_sources: -3
confidence_level: SORT_OF
stage: validating
---
# Bad artifact

We will capture $2,000,000 in revenue at a 35% margin.
"""
    with tempfile.TemporaryDirectory() as td:
        _write(td, "bad.md", bad)
        code, d = _wpa_run("artifact_lint.py", [td, "--json"])
        assert code == 3 and d["status"] == "VALIDATION_FAILED"
        v = d["results"]["violations"]["value"]
        checks = [x["check"] for x in v]
        details = " | ".join(x["detail"] for x in v)
        assert "assumptions_section" in checks
        assert checks.count("orphan_figure") == 2  # $2,000,000 and 35%
        assert "mode" in details            # missing frontmatter key
        assert "research_sources" in details  # -3 is not an int >= 0
        assert "confidence_level" in details  # SORT_OF not in the closed set
        # A file with no frontmatter at all is its own violation.
        _write(td, "nofm.md", "# X\n\n## Assumptions & Limitations\nnone\n")
        code2, d2 = _wpa_run("artifact_lint.py", [td, "--json"])
        assert code2 == 3
        v2 = d2["results"]["violations"]["value"]
        assert any(x["file"] == "nofm.md" and "no YAML frontmatter"
                   in x["detail"] for x in v2)


def t_lint_escape_hatch():
    def plan(with_hatch: bool) -> str:
        hatch = "<!-- bp-lint: allow -->\n" if with_hatch else ""
        return ("---\nresearch_sources: 0\nconfidence_level: LOW\n"
                "stage: idea\nmode: pre-revenue\n---\n# P\n\n"
                + hatch + "Ballpark spend is $1,234 monthly.\n\n"
                "## Assumptions & Limitations\nnone yet\n")
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", plan(with_hatch=False))
        code, _ = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 3
        _write(td, "plan.md", plan(with_hatch=True))
        code2, d2 = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code2 == 0 and d2["results"]["violation_count"]["value"] == 0


def t_lint_violations_capped_at_20():
    body = "\n".join(f"Metric {i} sits at {i + 30}% today." for i in range(30))
    content = ("---\nresearch_sources: 0\nconfidence_level: LOW\n"
               "stage: idea\nmode: pre-revenue\n---\n# P\n\n" + body +
               "\n\n## Assumptions & Limitations\nnone\n")
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", content)
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 3
        assert len(d["results"]["violations"]["value"]) == 20
        assert d["results"]["violation_count"]["value"] == 20


TESTS += [
    ("lint: clean fixture passes", t_lint_clean_fixture_passes),
    ("lint: every violation class caught", t_lint_catches_each_violation_class),
    ("lint: escape hatch exempts one line", t_lint_escape_hatch),
    ("lint: violations capped at 20", t_lint_violations_capped_at_20),
]


# --- session_score golden tests (added by WP-A) ----------------------------

def _build_score_fixture(td: str) -> None:
    """Workspace with hand-derived ratios:
    tagged_ratio: numeric inputs price/sellers/conversion tagged + bare
      `growth` => 3/4 = 0.75 (unknown churn is non-numeric, excluded);
    citation_coverage: public sellers cited, public conversion uncited
      => 1/2 = 0.5;
    insufficient_data_honesty: 1 unknown input + 1 INSUFFICIENT_DATA
      envelope (readiness.json) = 2;
    delegation: plan.md has a financial heading AND scenarios/ holds a
      projection envelope => true;
    corrections_count: correction heading + correction frontmatter = 2
      (the plain pricing decision does not count);
    lint_pass: plan.md is the clean fixture => true.
    """
    os.makedirs(os.path.join(td, "scenarios"))
    os.makedirs(os.path.join(td, "decisions"))
    state = {
        "meta": {"slug": "demo", "route": "MODULE", "stage": "validating"},
        "inputs": {
            "price": {"value": 49, "status": "user"},
            "sellers": {"value": 300000, "status": "public",
                        "source_url": "https://example.gov/stats",
                        "source_date": "2026-08-19"},
            "conversion": {"value": 0.02, "status": "public"},
            "growth": 0.1,
            "churn": {"value": None, "status": "unknown"},
        },
    }
    with open(os.path.join(td, "demo.bp.json"), "w", encoding="utf-8") as f:
        json.dump(state, f)
    plan = _CLEAN_PLAN.replace(
        "# Demo plan", "# Demo plan\n\n## Financial projection\n\n"
        "Outputs live in scenarios/."
    )
    _write(td, "plan.md", plan)
    _write(td, "readiness.json",
           '{"script": "readiness", "status": "INSUFFICIENT_DATA"}')
    _write(os.path.join(td, "scenarios"), "projection-base.json",
           '{"script": "projection", "status": "OK"}')
    _write(os.path.join(td, "decisions"), "001-market.md",
           "# Correction: reachable market recount\n\nRecounted.\n")
    _write(os.path.join(td, "decisions"), "002-pricing.md",
           "# Decision: pricing tier\n\nChose standard.\n")
    _write(os.path.join(td, "decisions"), "003-churn.md",
           "---\ntype: correction\n---\n# Decision: churn basis\n\nRetagged.\n")


def t_session_score_fixture():
    import re as _re
    with tempfile.TemporaryDirectory() as td:
        _build_score_fixture(td)
        code, d = _wpa_run("session_score.py", [td, "--json"])
        assert code == 0
        r = d["results"]
        assert r["tagged_ratio"]["value"] == 0.75
        assert r["citation_coverage"]["value"] == 0.5
        assert r["delegation"]["value"] is True
        assert r["insufficient_data_honesty"]["value"] == 2
        assert r["lint_pass"]["value"] is True
        assert r["corrections_count"]["value"] == 2
        entries = r["suggested_memory_entries"]["value"]
        assert entries, "structural gaps must yield memory suggestions"
        pat = _re.compile(
            r"^- \[\d{4}-\d{2}-\d{2} · MODULE\] .+\. Apply: .+\.$")
        assert all(pat.match(e) for e in entries), entries


def t_session_score_degrades_without_artifacts():
    # An empty workspace: every state-dependent metric lands in
    # not_computed with a reason; lint still runs (vacuously clean);
    # the script must not crash.
    with tempfile.TemporaryDirectory() as td:
        code, d = _wpa_run("session_score.py", [td, "--json"])
        assert code == 0 and d["status"] == "PARTIAL"
        assert d["results"]["lint_pass"]["value"] is True
        nc = {x["metric"] for x in d["not_computed"]}
        assert {"tagged_ratio", "citation_coverage", "delegation",
                "insufficient_data_honesty", "corrections_count"} <= nc


TESTS += [
    ("retro-score: fixture ratios hand-derived", t_session_score_fixture),
    ("retro-score: empty workspace degrades, never crashes",
     t_session_score_degrades_without_artifacts),
]



# --- fix-pack golden tests (dogfood 2026-08-19: nested tags, deliverable
#     detection, ES heading) ------------------------------------------------

def t_lint_accepts_spanish_heading():
    import tempfile, subprocess, os
    md = """---
research_sources: 0
confidence_level: LOW
stage: idea
mode: pre-revenue
---

# Doc

## Premisas y Limitaciones

sin cifras
"""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "doc.md")
        open(path, "w").write(md)
        proc = subprocess.run(
            [PY, os.path.join(SCRIPT_DIR, "artifact_lint.py"), path, "--json"],
            capture_output=True, text=True)
        assert proc.returncode == 0, proc.stdout[-400:]


def t_retro_counts_nested_public_tags():
    import tempfile, subprocess, os
    state = {"meta": {"slug": "t", "route": "MODULE"}, "inputs": {
        "steps": {"value": [
            {"name": "a", "value": 10, "status": "public",
             "source_url": "https://x.example/a", "source_date": "2026-08-19"},
            {"name": "b", "value": 0.5, "status": "public"},
        ], "status": "user"}}}
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "t.bp.json"), "w").write(json.dumps(state))
        proc = subprocess.run(
            [PY, os.path.join(SCRIPT_DIR, "session_score.py"), d, "--json"],
            capture_output=True, text=True)
        out = json.loads(proc.stdout)
        cc = out["results"].get("citation_coverage")
        assert cc is not None, "citation_coverage must compute on nested tags"
        # hand-derived: 2 nested public entries, 1 fully cited => 0.5
        assert abs(cc["value"] - 0.5) < 1e-9, cc


def t_retro_detects_non_plan_deliverable():
    import tempfile, subprocess, os
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, "evaluacion-x.md"), "w").write(
            "# Doc\n\n## Financial plan\n\ntexto\n")
        open(os.path.join(d, "fa-out.json"), "w").write(json.dumps(
            {"script": "projection", "status": "OK"}))
        proc = subprocess.run(
            [PY, os.path.join(SCRIPT_DIR, "session_score.py"), d, "--json"],
            capture_output=True, text=True)
        out = json.loads(proc.stdout)
        dl = out["results"].get("delegation")
        assert dl is not None and dl["value"] is True, out["not_computed"]


def t_retro_prefers_canonical_state_file():
    import tempfile, subprocess, os
    with tempfile.TemporaryDirectory() as d:
        w = os.path.join(d, "bp_demo")
        os.makedirs(w)
        # alphabetically-first auxiliary file with NO public tags
        open(os.path.join(w, "aux-baseline.bp.json"), "w").write(json.dumps(
            {"inputs": {"x": {"value": 1, "status": "user"}}}))
        # canonical slug file WITH a cited public tag
        open(os.path.join(w, "demo.bp.json"), "w").write(json.dumps(
            {"meta": {"slug": "demo", "route": "MODULE"}, "inputs": {
             "m": {"value": 5, "status": "public",
                   "source_url": "https://x.example/m",
                   "source_date": "2026-08-19"}}}))
        proc = subprocess.run(
            [PY, os.path.join(SCRIPT_DIR, "session_score.py"), w, "--json"],
            capture_output=True, text=True)
        out = json.loads(proc.stdout)
        cc = out["results"].get("citation_coverage")
        assert cc is not None and cc["value"] == 1.0, out.get("not_computed")


TESTS.extend([
    ("fix-pack: lint accepts Premisas y Limitaciones", t_lint_accepts_spanish_heading),
    ("fix-pack: retro-score counts nested public tags", t_retro_counts_nested_public_tags),
    ("fix-pack: retro-score detects non-plan.md deliverable", t_retro_detects_non_plan_deliverable),
    ("fix-pack: retro-score prefers canonical <slug>.bp.json", t_retro_prefers_canonical_state_file),
])


# --- iteration-2 golden tests (WP-1: the four verified script defects) -----
#
# Every expected value below was derived by hand from the spec, before the
# fixed code ran. Each test names the defect it would have caught.

TEMPLATE_DIR = os.path.join(SCRIPT_DIR, os.pardir, "assets", "templates")


def _record_from_template(type_value: str) -> str:
    """A decision record written exactly as the SHIPPED template instructs,
    with the Type bullet filled in. Reading the real file is the point: the
    metric and the template are one contract, and iteration 1 broke it."""
    path = os.path.join(TEMPLATE_DIR, "decision-record.md")
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    out: "list[str]" = []
    replaced = False
    for line in lines:
        if re.match(r"^\s*-\s*Type\s*:", line, re.IGNORECASE):
            out.append(f"- Type: {type_value}")
            replaced = True
        else:
            out.append(line)
    assert replaced, (
        "assets/templates/decision-record.md no longer carries a '- Type:' "
        "bullet — retro-score's corrections_count keys on it"
    )
    return "\n".join(out) + "\n"


def t_retro_counts_correction_from_shipped_template():
    # Defect 1: a record written to the skill's own template scored 0.
    # Hand-derived: two records from the REAL shipped template, one typed
    # `correction` and one typed `decision` => corrections_count = 1.
    # The template explains the word "correction" inside an HTML comment, so
    # a scorer that reads comments would answer 2 — that false positive is
    # pinned shut here too.
    with tempfile.TemporaryDirectory() as td:
        dec = os.path.join(td, "decisions")
        os.makedirs(dec)
        _write(dec, "DR-001-retag.md", _record_from_template("correction"))
        _write(dec, "DR-002-pricing.md", _record_from_template("decision"))
        code, d = _wpa_run("session_score.py", [td, "--json"])
        assert code == 0, d
        cc = d["results"].get("corrections_count")
        assert cc is not None, d["not_computed"]
        assert cc["value"] == 1, cc


def t_retro_delegation_survives_house_heading():
    # Defect 2: delegation keyed on finance vocabulary in headings, so a run
    # that delegated correctly under this skill's own "Viability gate" title
    # scored not_computed. The metric is evidence-driven now:
    #   saved unit_economics envelope + prose that quotes a financial metric
    #   and cites the artifact => True;
    #   same deliverable with NO saved envelope => False (a reported failure,
    #   never a silent not_computed).
    plan = ("---\nresearch_sources: 1\nconfidence_level: MEDIUM\n"
            "stage: revenue\nmode: standard\n---\n"
            "# Plan\n\n## Viability gate\n\n"
            "Contribution margin holds at the standard tier "
            "(unit-economics.json).\n\n"
            "## Assumptions & Limitations\n\nnone\n")
    envelope = '{"script": "unit_economics", "status": "OK"}'
    with tempfile.TemporaryDirectory() as td:
        _write(td, "plan.md", plan)
        _write(td, "unit-economics.json", envelope)
        code, d = _wpa_run("session_score.py", [td, "--json"])
        assert code == 0, d
        dl = d["results"].get("delegation")
        assert dl is not None, d["not_computed"]
        assert dl["value"] is True, dl
    with tempfile.TemporaryDirectory() as td:
        _write(td, "plan.md", plan)
        code2, d2 = _wpa_run("session_score.py", [td, "--json"])
        dl2 = d2["results"].get("delegation")
        assert dl2 is not None, d2["not_computed"]
        assert dl2["value"] is False, dl2


def t_readiness_one_warning_for_the_non_dimension_tail():
    # Defect 3: one warning per non-dimension input turned the skill's own
    # canonical state file (which holds every tagged input by convention)
    # into 132 warnings.
    # Hand-derived, 8 dimensions at score 4 / researched:
    #   points = 4/5 × weight × 0.75 = 0.6 × weight; Σweights = 100
    #   => 60.0 => FRAGILE, and NO non-dimension warning at all.
    # Drop `execution` (weight 10): 0.6 × 90 = 54.0 => FRAGILE, and exactly
    #   ONE warning, naming the 12 ignored inputs.
    dims = {dm: _dim(4, "researched") for dm in READINESS_DIMS}
    tail = {f"other_{i}": {"value": i, "status": "user"} for i in range(12)}

    def tail_warnings(envelope) -> "list[str]":
        """Warnings about the ignored tail, however they are worded — the
        count is the contract, not the phrasing."""
        return [w for w in envelope["warnings"]
                if "non-dimension" in w or any(n in w for n in tail)]

    code, d = _wpa_run_inputs("readiness.py", dict(dims, **tail))
    assert code == 0 and d["results"]["readiness_score"]["value"] == 60.0
    assert d["results"]["verdict"]["value"] == "FRAGILE"
    assert tail_warnings(d) == [], tail_warnings(d)

    partial = {k: v for k, v in dims.items() if k != "execution"}
    code2, d2 = _wpa_run_inputs("readiness.py", dict(partial, **tail))
    assert code2 == 0 and d2["results"]["readiness_score"]["value"] == 54.0
    noise2 = tail_warnings(d2)
    assert len(noise2) == 1, noise2
    assert "12" in noise2[0], noise2[0]


_ROUNDING_DOC = """---
research_sources: 1
confidence_level: MEDIUM
stage: revenue
mode: standard
---
# Take rate

## Finding

Advertising take rate sits near 1.8% of GTV, and the fee band moves 2% either
way.

## Assumptions & Limitations

none

## Sources

| claim | figure | source |
|---|---|---|
| take rate | 1.84% | filings |
| fee band | (2)% | filings |
"""


def t_lint_accepts_prose_that_rounds():
    # Defect 4a: evidence rule 6 tells the prose to round what the artifact
    # records to full precision, and the lint flagged exactly that.
    # Hand-derived: body shows one decimal, so the tolerance is
    # 0.5 × 10^-1 = 0.05; |1.84 - 1.8| = 0.04 <= 0.05 => sourced.
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", _ROUNDING_DOC)
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 0, d["results"].get("violations", {}).get("value")
        assert d["results"]["violation_count"]["value"] == 0


def t_lint_paren_cell_covers_body_percent():
    # Defect 4b: an accounting-negative cell "(2)%" yielded no token at all,
    # so the body's "2%" read as unsourced. Hand-derived: parentheses are the
    # sign convention, so "(2)%" normalizes to "2%" and covers it exactly.
    # (Same fixture as above; this asserts the second figure specifically.)
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "table-only.md", _ROUNDING_DOC.replace(
            "sits near 1.8% of GTV, and the fee band moves 2% either\nway",
            "band moves 2% either way"))
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 0, d["results"].get("violations", {}).get("value")
        assert d["results"]["violation_count"]["value"] == 0


def t_lint_still_flags_unsourced_figures():
    # Defect 4 guard-rail: the tolerance must not turn the check off.
    # Hand-derived against the same sources table (only "1.84%" and "(2)%"):
    #   "7.3%" — |1.84 - 7.3| = 5.46 > 0.05 (and |2 - 7.3| = 5.3 > 0.05)
    #            => orphan;
    #   "$4,200" — no covered currency figure exists at all => orphan.
    # Expect exactly 2 orphan_figure violations and exit 3.
    doc = _ROUNDING_DOC.replace(
        "Advertising take rate sits near 1.8% of GTV, and the fee band moves "
        "2% either\nway.",
        "Advertising take rate sits near 7.3% of GTV on $4,200 of spend.")
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", doc)
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 3, d["results"]
        v = d["results"]["violations"]["value"]
        assert [x["check"] for x in v] == ["orphan_figure", "orphan_figure"], v
        details = " | ".join(x["detail"] for x in v)
        assert "7.3%" in details and "$4,200" in details, details


TESTS.extend([
    ("iter2: retro-score counts the template's Type bullet",
     t_retro_counts_correction_from_shipped_template),
    ("iter2: delegation survives a house heading (Viability gate)",
     t_retro_delegation_survives_house_heading),
    ("iter2: readiness warns once about the non-dimension tail",
     t_readiness_one_warning_for_the_non_dimension_tail),
    ("iter2: lint accepts prose that rounds", t_lint_accepts_prose_that_rounds),
    ("iter2: lint reads (2)% as covering 2%",
     t_lint_paren_cell_covers_body_percent),
    ("iter2: lint still flags unsourced figures",
     t_lint_still_flags_unsourced_figures),
])


# --- iteration-3 golden tests: prose_precision (evidence rule 6) -----------
#
# Rule 6 says machine precision stays in the artifact and the prose rounds.
# It was written but not enforced: blind judges of iteration 2 quoted
# "281.085113 accounts" and "R$ 45.761,74875" out of the runs' own sentences,
# so documents violated the rule while passing lint. The check below fires
# only on body prose, at MORE THAN 2 decimal places.
#
# All fixtures are pt-BR on purpose: the comma is the decimal mark there, the
# separator the old parser stripped as formatting.

def _precision_doc(body: str, sources_rows: str = "") -> str:
    """A minimal, otherwise lint-clean artifact with `body` as its argument.

    "Achado" is deliberately NOT a covered heading (the covered set is
    sources/fontes/fuentes/inputs/assumptions/premissas/premisas/cifras/
    tagged), so everything in it is body prose.
    """
    rows = sources_rows or (
        "| multiplicador | R$ 0,894911 | unit-economics.json |\n"
    )
    return (
        "---\nresearch_sources: 2\nconfidence_level: MEDIUM\n"
        "stage: validating\nmode: standard\n---\n"
        "# Multiplicador de preço\n\n"
        "## Achado\n\n"
        + body +
        "\n\n## Assumptions & Limitations\n\nnenhuma\n\n"
        "## Sources\n\n| claim | figure | source |\n|---|---|---|\n"
        + rows
    )


def t_lint_prose_precision_flags_machine_output():
    # Hand-derived: "R$ 0,894911" — the last separator opens a group of SIX
    # digits, which is not a thousands group, so the comma is the decimal
    # mark and the figure shows 6 decimals. 6 > 2 => 1 prose_precision
    # violation. The same string sits in the Sources table, so the orphan
    # check is satisfied (normalized "R$0894911" on both sides) and the
    # expected total is exactly 1, exit 3.
    body = "O multiplicador de preço fica em R$ 0,894911 no cenário base."
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", _precision_doc(body))
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 3, d["results"]
        v = d["results"]["violations"]["value"]
        assert len(v) == 1, v
        # Line 11 by hand: 6 frontmatter lines, "# Multiplicador de preço",
        # a blank, "## Achado", a blank, then the sentence.
        assert v[0]["check"] == "prose_precision" and v[0]["line"] == 11, v
        detail = v[0]["detail"]
        # The message has to teach: name the figure, say where precision
        # belongs, and cite the rule.
        assert "0,894911" in detail and "6 decimal places" in detail, detail
        assert "artifact" in detail and "evidence rule 6" in detail, detail


def t_lint_prose_precision_exempts_table_rows():
    # Same figure, same document, moved into a table row inside the same
    # non-covered section. Table lines are where exact values belong — they
    # are the artifact ON the page — so the hand-expected count is 0, exit 0.
    body = ("| cenário | multiplicador |\n|---|---|\n"
            "| base | R$ 0,894911 |")
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", _precision_doc(body))
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 0, d["results"].get("violations", {}).get("value")
        assert d["results"]["violation_count"]["value"] == 0


def t_lint_precision_and_orphan_rules_coexist():
    # THE COEXISTENCE TEST. The two figure rules pull in opposite directions
    # and must both be satisfied by the house style: prose rounds (rule 6),
    # and rounded prose still counts as sourced against the table's full
    # precision (the iteration-2 tolerance).
    # Hand-derived, both checks on one document:
    #   prose_precision — "R$ 0,89" shows 2 decimals; 2 is not > 2 => clean;
    #   orphan_figure   — the body shows 2 decimals, so the tolerance is
    #                     0.5 x 10^-2 = 0.005; the Sources table carries
    #                     0.894911; |0.894911 - 0.89| = 0.004911 <= 0.005
    #                     => covered.
    # Expected total: 0 violations, exit 0.
    body = ("O multiplicador de preço arredonda para R$ 0,89 no texto; a "
            "tabela guarda a precisão cheia.")
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", _precision_doc(body))
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 0, d["results"].get("violations", {}).get("value")
        assert d["results"]["violation_count"]["value"] == 0
        # Guard: the rounding acceptance must not be doing this by turning
        # the orphan check off — an unsourced figure on the same line still
        # has to be caught.
        p2 = _write(td, "plan.md",
                    _precision_doc(body.replace("no texto", "sobre R$ 7,31")))
        code2, d2 = _wpa_run("artifact_lint.py", [p2, "--json"])
        assert code2 == 3
        v2 = d2["results"]["violations"]["value"]
        assert [x["check"] for x in v2] == ["orphan_figure"], v2
        assert "7,31" in v2[0]["detail"], v2[0]["detail"]


def t_lint_prose_precision_escape_hatch():
    # The existing escape hatch, reused: the exact comment on the PRECEDING
    # line exempts the figure. Hand-expected: 1 violation without it (the
    # same figure as the first test), 0 with it.
    body = "O multiplicador de preço fica em R$ 0,894911 no cenário base."
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", _precision_doc(body))
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 3 and d["results"]["violation_count"]["value"] == 1
        _write(td, "plan.md",
               _precision_doc("<!-- bp-lint: allow -->\n" + body))
        code2, d2 = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code2 == 0, d2["results"].get("violations", {}).get("value")
        assert d2["results"]["violation_count"]["value"] == 0


def t_lint_prose_precision_leaves_presentation_figures_alone():
    # Ordinary presentation figures must survive untouched, including the
    # pt-BR thousands form the parser could mistake for decimals.
    # Hand-derived decimals: "R$ 49,90" -> 2 (not > 2, clean);
    #   "R$ 1.058.400" -> the last separator opens a group of exactly three
    #   digits and the integer part "1.058" is not all zeros, so it is a
    #   thousands group => 0 decimals, clean;
    #   "35%" -> no separator => 0 decimals, clean.
    # Every figure is echoed in the Sources table, so the orphan check is
    # quiet too. Expected total: 0 violations, exit 0.
    body = ("A assinatura custa R$ 49,90 por mês, o SOM soma R$ 1.058.400 "
            "por ano e a margem fica em 35%.")
    rows = ("| preço | R$ 49,90 | pricing draft |\n"
            "| SOM | R$ 1.058.400 | market.json |\n"
            "| margem | 35% | unit-economics.json |\n")
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", _precision_doc(body, sources_rows=rows))
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 0, d["results"].get("violations", {}).get("value")
        assert d["results"]["violation_count"]["value"] == 0


def t_lint_thousands_dot_is_not_a_decimal_point():
    # The precision check needs to know where the decimal mark is, and the
    # orphan check now shares that parser. Before iteration 3 the parser read
    # any single dot as a decimal point, so the pt-BR "R$ 5.226" (five
    # thousand two hundred and twenty-six) was read as five-and-a-bit reais
    # and covered a bare "R$ 5" in the prose — an unsourced figure walking
    # through the gate. Hand-derived:
    #   "5.226" — the last separator opens a group of exactly three digits
    #             and the integer part "5" is not all zeros, so it is a
    #             thousands group => value 5226, 0 decimals;
    #   "R$ 5"  — 0 decimals => tolerance 0.5; |5226 - 5| = 5221 > 0.5
    #             => orphan_figure. Expected: 1 violation, exit 3.
    rows = "| custo logístico | R$ 5.226 | unit-economics.json |\n"
    body = "Um acréscimo de R$ 5 por assinante elimina o lucro do mês 36."
    with tempfile.TemporaryDirectory() as td:
        p = _write(td, "plan.md", _precision_doc(body, sources_rows=rows))
        code, d = _wpa_run("artifact_lint.py", [p, "--json"])
        assert code == 3, d["results"]
        v = d["results"]["violations"]["value"]
        assert [x["check"] for x in v] == ["orphan_figure"], v
        assert "R$ 5" in v[0]["detail"], v[0]["detail"]
        # And the figure itself is fine written out: it matches the table
        # exactly, and 0 decimals is not over-precise. Expected: 0, exit 0.
        p2 = _write(td, "plan.md", _precision_doc(
            "O custo logístico total é de R$ 5.226 por mês.",
            sources_rows=rows))
        code2, d2 = _wpa_run("artifact_lint.py", [p2, "--json"])
        assert code2 == 0, d2["results"].get("violations", {}).get("value")
        assert d2["results"]["violation_count"]["value"] == 0


TESTS.extend([
    ("iter3: lint flags machine precision in prose",
     t_lint_prose_precision_flags_machine_output),
    ("iter3: a pt-BR thousands dot is not a decimal point",
     t_lint_thousands_dot_is_not_a_decimal_point),
    ("iter3: lint exempts table rows from prose precision",
     t_lint_prose_precision_exempts_table_rows),
    ("iter3: prose-rounds and rounded-prose-is-sourced coexist",
     t_lint_precision_and_orphan_rules_coexist),
    ("iter3: prose precision honours the allow comment",
     t_lint_prose_precision_escape_hatch),
    ("iter3: prose precision leaves 2-decimal and integer figures alone",
     t_lint_prose_precision_leaves_presentation_figures_alone),
    ("iter3: a figure with nothing left to round is spared",
     t_lint_prose_precision_spares_a_figure_with_nothing_to_round),
])


def main() -> None:
    failures = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  ok   {name}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {name}: {e or 'assertion failed'}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"  FAIL {name}: unexpected {type(e).__name__}: {e}")
    total = len(TESTS)
    print(f"selftest: {total - failures}/{total} passed")
    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
