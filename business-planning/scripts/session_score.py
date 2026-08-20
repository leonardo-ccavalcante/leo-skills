"""session_score — domain-agnostic e2e process scorecard over a bp_<slug>/ dir.

Scores the PROCESS, never the business: every metric below is a structural
fact about the workspace artifacts (tags present, citations complete, files
saved, lint state). The script never interprets what a plan says — a great
process around a doomed idea still scores well here, which is exactly the
point: this scorecard feeds the retrospective, not the verdict.

Metrics (each degrades to `not_computed` with a reason; the script never
crashes on a partial workspace):

- tagged_ratio          share of numeric inputs in `<slug>.bp.json` carrying
                        explicit {"value", "status"} tags (bare scalars count
                        against it)
- citation_coverage     share of `public` inputs (at any nesting depth) with BOTH source_url and
                        source_date
- delegation            evidence-driven: true when saved fa.sh envelope JSONs
                        exist under the workspace AND a deliverable cites a
                        saved artifact or quotes a financial metric. Heading
                        vocabulary is only a fallback signal — a plan that
                        delegated correctly under the heading "Viability gate"
                        is delegating, whatever it called the section
- insufficient_data_honesty
                        count of honestly surfaced gaps: inputs tagged
                        `unknown` + saved envelope JSONs whose status is
                        INSUFFICIENT_DATA
- lint_pass             artifact_lint.py run over the dir via subprocess
                        (exit 0 => true, 3 => false)
- corrections_count     decision-record .md files under decisions/ that declare
                        type `correction` — in YAML frontmatter, in the first
                        heading, or in the `- Type:` header bullet that
                        assets/templates/decision-record.md actually ships

Output adds `suggested_memory_entries`: process lessons derived from the
structural gaps, pre-formatted for MEMORY.md as
`- [YYYY-MM-DD · route] lesson. Apply: how.` (route from meta.route in the
state file when present).

Usage: session_score.py <bp_dir> [--json]
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys

from bp_common import Result, cli

SCRIPT = "session_score"

FA_SCRIPTS = {"projection", "unit_economics", "scenarios", "ratios",
              "saas_metrics", "opsfinance"}
# Headings are a weak signal: a section can be financial without saying so
# ("Viability gate", "Economía unitaria"), so the pattern is deliberately wide
# and only ever a fallback behind the evidence test below.
_FINANCIAL_HEADING = re.compile(
    r"(financ|financeir|financier|econom|projec|projeç|proyec|p&l"
    r"|\bcash\b|caixa|\bcaja\b|runway|burn|break-?even|equil[íi]brio"
    r"|ltv|cac|payback|\bgates?\b|viabilit|viabilid"
    r"|margin|margem|margen|contribu)",
    re.IGNORECASE,
)
# A financial metric named in the prose — the thing an fa.sh envelope backs.
_FINANCIAL_TERM = re.compile(
    r"(\bltv\b|\bcac\b|payback|unit[\s-]*econom|econom[íi]a\s*unitaria"
    r"|contribution\s*margin|margem\s*de\s*contribui|margen\s*de\s*contribu"
    r"|gross\s*margin|margem\s*bruta|margen\s*bruto|break-?even|runway"
    r"|burn\s*rate|\bebitda\b|\barr\b|\bmrr\b|cash\s*flow|fluxo\s*de\s*caixa"
    r"|flujo\s*de\s*caja|p&l|profit\s*and\s*loss)",
    re.IGNORECASE,
)
# A pointer to a saved machine artifact (the delegation receipt).
_ARTIFACT_REF = re.compile(r"([\w.-]+\.json\b|\bfa\.sh\b)", re.IGNORECASE)
_CORRECTION = re.compile(r"correction|correç", re.IGNORECASE)
# The `- Type: correction` bullet that assets/templates/decision-record.md
# ships (also `Type:`, `**Type:**`, and the Portuguese/Spanish `Tipo:`).
_TYPE_BULLET = re.compile(
    r"^\s*(?:[-*+]\s+)?(?:\*\*|__)?\s*(?:type|tipo)\s*(?:\*\*|__)?\s*:\s*(.+)$",
    re.IGNORECASE,
)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
# How far into a record the metadata block may sit. The shipped template puts
# the Type bullet below a two-paragraph HTML comment, so a 10-line window is
# too tight; the scan stops at the first `##` section heading regardless.
HEADER_SCAN_LINES = 40


def _read_json(path: str) -> "dict | None":
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _read_lines(path: str) -> "list[str] | None":
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except (OSError, UnicodeDecodeError):
        return None


def _find_state_file(bp_dir: str) -> "str | None":
    """Prefer the canonical <slug>.bp.json (slug = dir name minus the bp_
    prefix); auxiliary state files (baselines, drafts) sort arbitrarily and
    must not shadow it."""
    cands = sorted(n for n in os.listdir(bp_dir) if n.endswith(".bp.json"))
    if not cands:
        return None
    base = os.path.basename(os.path.normpath(bp_dir))
    slug = base[3:] if base.startswith("bp_") else base
    preferred = f"{slug}.bp.json"
    if preferred in cands:
        return os.path.join(bp_dir, preferred)
    return os.path.join(bp_dir, cands[0])


def _workspace_envelopes(bp_dir: str) -> "list[dict]":
    """Every parseable envelope-shaped JSON under the dir (recursive), i.e. a
    dict carrying a 'script' or 'status' key. State files are excluded."""
    out = []
    for root, _dirs, files in os.walk(bp_dir):
        for n in files:
            if not n.endswith(".json") or n.endswith(".bp.json"):
                continue
            d = _read_json(os.path.join(root, n))
            if d is not None and ("script" in d or "status" in d):
                out.append(d)
    return out


def _numeric(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _blank_comments(lines: "list[str]") -> "list[str]":
    """Same lines with HTML-comment text blanked out (line count preserved).

    Load-bearing: the shipped decision-record template explains the word
    `correction` inside a comment. Scoring that comment would count every
    record ever written from the template as a correction.
    """
    text = "\n".join(lines)
    text = _HTML_COMMENT.sub(
        lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    open_at = text.find("<!--")          # comment left unclosed: blank the tail
    if open_at != -1:
        text = text[:open_at] + re.sub(r"[^\n]", " ", text[open_at:])
    return text.split("\n")


def _is_correction_record(lines: "list[str]") -> bool:
    """True when a decision record declares itself a correction.

    Three shapes count, because the skill's own docs and template use all
    three: YAML frontmatter (`type: correction`), a `# Correction: ...`
    heading, and the `- Type: correction` bullet in the metadata block of
    assets/templates/decision-record.md. The bullet is the shape the template
    actually ships, so a record written exactly as instructed must score.
    """
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() in ("---", "..."):
                body_start = i + 1
                break
            if _CORRECTION.search(lines[i]):
                return True

    scan = _blank_comments(lines)
    first_heading = next(
        (l for l in scan[body_start:] if l.lstrip().startswith("#")), "")
    if _CORRECTION.search(first_heading):
        return True

    for line in scan[body_start:body_start + HEADER_SCAN_LINES]:
        if line.lstrip().startswith("##"):
            break                        # past the metadata block, into prose
        m = _TYPE_BULLET.match(line)
        if m and _CORRECTION.search(m.group(1)):
            return True
    return False


def _run(args, warnings: "list[str]") -> Result:
    res = Result(script=SCRIPT)
    bp_dir = args.bp_dir
    if not os.path.isdir(bp_dir):
        raise SystemExit(f"{bp_dir} is not a directory — pass the bp_<slug>/ "
                         "workspace")

    route = "unscoped"
    today = datetime.date.today().isoformat()
    suggestions: "list[str]" = []

    def suggest(lesson: str, apply_how: str) -> None:
        suggestions.append(f"- [{today} · {route}] {lesson} Apply: {apply_how}")

    # -- state-file metrics ---------------------------------------------------
    state_path = _find_state_file(bp_dir)
    state = _read_json(state_path) if state_path else None
    if state is None:
        reason = ("no <slug>.bp.json state file in the workspace"
                  if state_path is None else
                  f"{os.path.basename(state_path)} is not readable JSON")
        res.skip("tagged_ratio", reason, ["<slug>.bp.json"])
        res.skip("citation_coverage", reason, ["<slug>.bp.json"])
        unknown_inputs = 0
    else:
        meta = state.get("meta")
        if isinstance(meta, dict) and isinstance(meta.get("route"), str):
            route = meta["route"]
        raw_inputs = state.get("inputs")
        entries = raw_inputs if isinstance(raw_inputs, dict) else state

        numeric_total = 0
        numeric_tagged = 0
        public_total = 0
        public_cited = 0
        unknown_inputs = 0
        def _walk_tagged(node):
            """Yield every tagged dict ({'value','status'}) at any depth:
            top-level inputs AND nested ones (e.g. sizing-chain steps).
            Provenance that lives inside a list value is still provenance."""
            if isinstance(node, dict):
                if "value" in node and "status" in node:
                    yield node
                    for x in _walk_tagged(node.get("value")):
                        yield x
                else:
                    for child in node.values():
                        for x in _walk_tagged(child):
                            yield x
            elif isinstance(node, list):
                for child in node:
                    for x in _walk_tagged(child):
                        yield x

        for _name, v in entries.items():
            if isinstance(v, dict) and "value" in v and "status" in v:
                for t in _walk_tagged(v):
                    if _numeric(t.get("value")):
                        numeric_total += 1
                        numeric_tagged += 1
                    if t.get("status") == "public":
                        public_total += 1
                        if t.get("source_url") and t.get("source_date"):
                            public_cited += 1
                    if t.get("status") == "unknown":
                        unknown_inputs += 1
            elif _numeric(v):
                numeric_total += 1  # bare scalar: numeric but untagged

        if numeric_total == 0:
            res.skip("tagged_ratio", "state file has no numeric inputs to audit")
        else:
            res.add("tagged_ratio", numeric_tagged / numeric_total,
                    "explicitly tagged numeric inputs / all numeric inputs",
                    [os.path.basename(state_path)])
            if numeric_tagged < numeric_total:
                suggest(
                    f"{numeric_total - numeric_tagged} of {numeric_total} "
                    "numeric inputs entered the state file untagged.",
                    "tag every number user/public/assumption/unknown at "
                    "intake, before any computation runs.",
                )
        if public_total == 0:
            res.skip("citation_coverage",
                     "no public-tagged inputs to audit — nothing was claimed "
                     "from external sources")
        else:
            res.add("citation_coverage", public_cited / public_total,
                    "public inputs with source_url AND source_date / all "
                    "public inputs", [os.path.basename(state_path)])
            if public_cited < public_total:
                suggest(
                    f"{public_total - public_cited} of {public_total} public "
                    "inputs lack source_url or source_date.",
                    "archive URL + access date in sources.md the moment a "
                    "public number enters the state file.",
                )

    # -- delegation -----------------------------------------------------------
    # The deliverable is plan.md OR any top-level .md the route produced
    # (EVALUATE writes evaluacion-*.md, MODULE writes module artifacts);
    # sources.md is the citation archive, never the deliverable.
    envelopes = _workspace_envelopes(bp_dir)
    fa_outputs = [d for d in envelopes if d.get("script") in FA_SCRIPTS]
    artifact_names = sorted(
        f for f in os.listdir(bp_dir)
        if f.endswith(".md") and f != "sources.md"
        and os.path.isfile(os.path.join(bp_dir, f))
    )
    deliverable_lines: "list[str]" = []
    readable_artifacts: "list[str]" = []
    for _f in artifact_names:
        lines = _read_lines(os.path.join(bp_dir, _f))
        if lines is not None:
            deliverable_lines.extend(lines)
            readable_artifacts.append(_f)
    if not readable_artifacts:
        res.skip("delegation", "no readable deliverable .md in the workspace",
                 ["plan.md or the route's artifact .md"])
    else:
        # Evidence first, vocabulary second. Section titles are a house style
        # ("Viability gate", "Economía unitaria"), so a heading match alone is
        # too brittle to decide the metric: what settles it is a saved fa.sh
        # envelope that the deliverable actually leans on.
        body = "\n".join(deliverable_lines)
        quotes_metric = bool(_FINANCIAL_TERM.search(body))
        cites_artifact = bool(_ARTIFACT_REF.search(body))
        has_financial_heading = any(
            l.lstrip().startswith("#") and _FINANCIAL_HEADING.search(l)
            for l in deliverable_lines
        )
        if fa_outputs and (quotes_metric or cites_artifact):
            res.add("delegation", True,
                    "saved fa.sh envelope JSON(s) exist AND a deliverable "
                    "cites a saved artifact or quotes a financial metric",
                    readable_artifacts)
        elif not (has_financial_heading or quotes_metric or cites_artifact):
            res.skip("delegation",
                     "no deliverable carries a financial section heading, a "
                     "quoted financial metric, or a cited saved artifact — "
                     "nothing to delegate")
        else:
            res.add("delegation", bool(fa_outputs),
                    "a deliverable signals financial content (section "
                    "heading, quoted metric, or cited artifact) => saved "
                    "fa.sh envelope JSONs must exist in the workspace",
                    readable_artifacts)
            if not fa_outputs:
                suggest(
                    "a deliverable carries financial content with no saved "
                    "fa.sh output JSON behind it.",
                    "run the fa.sh command with --json and save the output "
                    "under bp_<slug>/ BEFORE quoting any financial figure.",
                )

    # -- honesty --------------------------------------------------------------
    insufficient_envelopes = sum(
        1 for d in envelopes if d.get("status") == "INSUFFICIENT_DATA"
    )
    if state is None and not envelopes:
        res.skip("insufficient_data_honesty",
                 "no state file and no saved envelopes — nothing to count")
    else:
        res.add("insufficient_data_honesty",
                unknown_inputs + insufficient_envelopes,
                "inputs tagged unknown + saved envelopes with status "
                "INSUFFICIENT_DATA", [], unit="gaps surfaced")

    # -- lint -----------------------------------------------------------------
    lint_script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "artifact_lint.py")
    try:
        proc = subprocess.run(
            [sys.executable, lint_script, bp_dir, "--json"],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode in (0, 3):
            res.add("lint_pass", proc.returncode == 0,
                    "artifact_lint exit code (0 clean / 3 violations)",
                    [os.path.basename(bp_dir)])
            if proc.returncode == 3:
                suggest(
                    "artifacts did not pass bp.sh lint at retro time.",
                    "run bp.sh lint before delivery and fix violations "
                    "instead of allowlisting them.",
                )
        else:
            res.skip("lint_pass",
                     f"artifact_lint exited {proc.returncode} (unexpected)")
    except (OSError, subprocess.TimeoutExpired) as e:
        res.skip("lint_pass", f"could not run artifact_lint: {e}")

    # -- corrections ----------------------------------------------------------
    dec_dir = os.path.join(bp_dir, "decisions")
    if not os.path.isdir(dec_dir):
        res.skip("corrections_count", "no decisions/ directory in the workspace")
        corrections = 0
    else:
        corrections = 0
        for n in sorted(os.listdir(dec_dir)):
            if not n.endswith(".md"):
                continue
            lines = _read_lines(os.path.join(dec_dir, n))
            if lines is None:
                continue
            if _is_correction_record(lines):
                corrections += 1
        res.add("corrections_count", corrections,
                'decision records typed "correction" in frontmatter, in the '
                'first heading, or on the template\'s Type bullet',
                ["decisions/"], unit="records")
        if corrections:
            suggest(
                f"{corrections} correction decision-record(s) were needed "
                "this engagement.",
                "read decisions/ before the next session on this project; "
                "the corrections name exactly what went wrong.",
            )

    if res.results:
        res.results["suggested_memory_entries"] = {
            "value": suggestions,
            "status": "calculation",
            "formula": "process lessons derived from the structural gaps "
                       "above, in MEMORY.md entry format",
            "inputs_used": [],
        }
    return res


def _add_args(parser) -> None:
    parser.add_argument("bp_dir", help="bp_<slug>/ workspace directory")


if __name__ == "__main__":
    cli(SCRIPT, "Domain-agnostic process scorecard over a bp_<slug>/ "
                "workspace — structural facts only, never business content",
        _run, add_args=_add_args)
