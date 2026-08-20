"""artifact_lint — plan-artifact lint: frontmatter, assumptions, figures.

Argument: a `bp_<slug>/` directory or a single `.md` file. For a directory,
every top-level `.md` is linted EXCEPT `sources.md` — the citation archive is
itself a sources section, so its checks would be circular. Subdirectories
(decisions/, scenarios/) hold records and machine outputs, not plan artifacts.

Four checks per file (violations across all files capped at 20):

1. Frontmatter — a YAML block delimited by `---` lines at the top, scanned as
   simple `key: value` pairs (stdlib only; nested YAML is out of scope for
   these four keys). Required: `research_sources` (int >= 0),
   `confidence_level` (HIGH|MEDIUM|LOW), `stage`, `mode`.
2. Assumptions section — some heading contains "Assumptions & Limitations",
   "Premissas e Limitações" or "Premisas y Limitaciones".
3. Orphan figures — currency ($ £ € R$) and percent tokens in the body that
   appear in NO covered region. Covered regions are: sections whose heading
   contains sources/fontes/inputs/assumptions/premissas/tagged, markdown
   table lines (tagged tables carry their own provenance columns), and the
   frontmatter block. Tokens are normalized (commas, spaces and accounting
   parentheses stripped) before matching, so "$1,058,400" in the body is
   covered by "$1058400" in a sources table and "2%" is covered by a "(2)%"
   cell. A body figure that is a CORRECT ROUNDING of a covered figure is also
   covered: prose is supposed to round (evidence rule 6), so "1.8%" against a
   table's "1.84%" is sourced, not orphaned. The tolerance is half a unit of
   the last digit the prose shows — tight, and it never covers a figure that
   is simply absent from every source. Comparison is language-aware: which
   separator is the decimal mark is decided by position, not by character
   (see _decimal_parts), because deliverables are written in the request's
   language and "R$ 5.226" is five thousand reais, not five. Escape hatch:
   the exact comment `<!-- bp-lint: allow -->` on the line ABOVE a figure
   exempts that line.
4. Prose precision — figures in body prose showing MORE THAN TWO decimal
   places. This instruments evidence rule 6 ("machine precision stays in the
   artifact; prose rounds"). Scope is wider than check 3 by one class: a bare
   "281.085113" with no currency symbol is machine output too, and that is
   the shape reviewers actually quoted. Exemptions are the same regions as
   check 3 in reverse: table lines, the frontmatter and
   sources/inputs/assumptions sections are exactly where exact values belong,
   so they are never flagged; only the argument itself is. Same
   `<!-- bp-lint: allow -->` escape hatch, though it should almost never be
   needed: a figure carrying MAX_PROSE_SIGDIGS or fewer significant digits is
   exempt outright, because rounding a number whose information all sits past
   the second decimal ("0,007%") destroys it instead of tidying it. Measured
   before it was written: across the 91-file workspace corpus this carve-out
   silences 1 hit out of 67, and that one is the false positive.

   MAX_PROSE_DECIMALS = 2 is a deliberate engineering constant, not a
   tunable. Two decimals is the most any presentation figure needs — cents on
   a price, a tenth of a percentage point on a rate — so anything longer in a
   sentence is machine output pasted from a JSON envelope. Blind reviewers of
   iteration 2 quoted "281.085113 accounts" and "R$ 45.761,74875" back as
   evidence that the document could not be trusted at its stated precision;
   the artifact was right to keep those digits, the sentence was wrong to
   print them. Raising the constant would only re-admit that failure, and
   lowering it to 1 would flag ordinary prices.

Checks 3 and 4 are deliberately opposed and must coexist: prose MUST round
(check 4), and rounded prose MUST still count as sourced against the full
precision in the table (check 3's rounding tolerance). A sentence that says
"R$ 0,89" over a table carrying "R$ 0,894911" is clean under both.

Exit 0 clean · 3 violations (list in results.violations with --json) ·
1 unexpected error.

Usage: artifact_lint.py <bp_dir-or-file.md> [--json]
"""

from __future__ import annotations

import os
import re
from decimal import Decimal, InvalidOperation

from bp_common import Result, cli

SCRIPT = "artifact_lint"

MAX_VIOLATIONS = 20
# Engineering constant, not a knob — see the module docstring, check 4.
MAX_PROSE_DECIMALS = 2
# A figure this short is already rounded as far as it can go: "0,007%" carries
# two significant digits, and rounding it to two decimals would erase it. The
# rule being enforced is over-precision, not decimal count, so a figure has to
# fail BOTH tests to be reported.
MAX_PROSE_SIGDIGS = 3
ALLOW_COMMENT = "<!-- bp-lint: allow -->"
CONFIDENCE_LEVELS = ("HIGH", "MEDIUM", "LOW")
REQUIRED_KEYS = ("research_sources", "confidence_level", "stage", "mode")

_ASSUMPTIONS_PAT = re.compile(
    r"(assumptions\s*&\s*limitations|premissas\s*e\s*limitações"
    r"|premisas\s*y\s*limitaciones)",
    re.IGNORECASE,
)
_COVERED_HEADING_PAT = re.compile(
    r"(sources|fontes|fuentes|inputs|assumptions|premissas|premisas|cifras"
    r"|tagged)", re.IGNORECASE
)
_FIGURE_PAT = re.compile(
    r"(\((?:[$£€]|R\$)\s?\d[\d,.]*\)"   # accounting negative: ($1,234)
    r"|(?:[$£€]|R\$)\s?\d[\d,.]*"       # currency: $1,234.50
    r"|\(\d[\d,.]*\)\s?%"               # accounting negative percent: (2)%
    r"|\d[\d,.]*\s?%)"                  # percent: 2.5%
)
# The precision check reads a wider class than the orphan check: a bare
# "281.085113" in a sentence is machine output whether or not it carries a
# currency symbol, and the judges quoted exactly that shape. Currency symbol
# and percent sign are optional here, and kept in the match so the violation
# message can name the figure the way the reader sees it.
_PROSE_FIGURE_PAT = re.compile(
    r"(?:(?:R\$|[$£€])\s?)?\d[\d,.]*\d(?:\s?%)?"
)
# A token split into sign-free parts: kind ("%" or the currency symbol),
# digits, optional decimals.
_TOKEN_NUM = re.compile(r"^(?P<sym>R\$|[$£€])?(?P<num>\d[\d.,]*)(?P<pct>%)?$")


def _normalize(token: str) -> str:
    # Commas and spaces are formatting; parentheses are the accounting sign
    # convention, which changes the sign but not the figure being sourced; a
    # trailing dot is sentence punctuation the figure regex over-captures
    # ("costs $49." vs "$49" in the table).
    return (token.replace(",", "").replace(" ", "")
                 .replace("(", "").replace(")", "").rstrip("."))


def _numeric_text(token: str) -> str:
    """Like _normalize, but KEEPS commas — they may be decimal marks.

    Deliverables are written in the request's language, so both conventions
    reach this file: "1,058,400.50" in English and "1.058.400,50" in
    Portuguese. Stripping commas before parsing turned "R$ 0,89" into 89.
    """
    return (token.replace(" ", "").replace("(", "").replace(")", "")
                 .rstrip(".,"))


def _decimal_parts(digits: str) -> "tuple[str, str]":
    """Split a written number into (integer digits, fraction digits).

    Position decides which separator is the decimal mark, never the
    character, because both conventions appear: the LAST separator opens the
    fraction, unless the group it opens is exactly three digits long — that
    reads as a thousands group, so "$1,234" is 1234 and not 1.234. The one
    exception is an integer part made only of zeros, which cannot carry a
    thousands group: "0,894" keeps its three decimals.

    Deliberately conservative: on the genuinely ambiguous three-digit group it
    under-counts decimals rather than inventing them, so the precision check
    can miss a three-decimal figure but never fires on "$1,234".
    """
    seps = [i for i, ch in enumerate(digits) if ch in ".,"]
    if not seps:
        return digits, ""
    idx = seps[-1]
    head, tail = digits[:idx], digits[idx + 1:]
    plain = digits.replace(".", "").replace(",", "")
    if not head or not tail.isdigit():
        return plain, ""
    if len(tail) == 3 and head.strip("0.,") != "":
        return plain, ""                      # 1,058,400 / 1.058.400
    return head.replace(".", "").replace(",", ""), tail


def _as_number(token: str) -> "tuple[str, Decimal, int] | None":
    """(kind, value, decimals shown) for a raw figure token, else None.

    `kind` is "%" or the currency symbol (empty for a bare number), so a
    percent can never be covered by a dollar amount that shares its digits.
    """
    m = _TOKEN_NUM.match(_numeric_text(token))
    if not m:
        return None
    whole, frac = _decimal_parts(m.group("num"))
    try:
        value = Decimal(whole + ("." + frac if frac else ""))
    except InvalidOperation:
        return None
    return m.group("pct") or m.group("sym") or "", value, len(frac)


def _significant_digits(value: Decimal) -> int:
    """Digits that actually carry information; leading and trailing zeros do
    not. 0.007 has one, 281.085113 has nine."""
    return len(value.normalize().as_tuple().digits)


def _is_covered(token: str, covered_tokens: "set[str]",
                covered_numbers: "list[tuple[str, Decimal]]") -> bool:
    """Exact match, or the body figure is a correct rounding of a covered one.

    Evidence rule 6 tells the prose to round what the artifact records to full
    precision, so an exact-string check would flag the skill's own house style.
    The tolerance is half a unit of the last digit the body shows — 1.8%
    accepts 1.84%, and 1.8% still rejects 7.3%. A figure that appears in no
    covered region at all has nothing to round from and is still reported.
    """
    if _normalize(token) in covered_tokens:
        return True
    parsed = _as_number(token)
    if parsed is None:
        return False
    kind, value, decimals = parsed
    tolerance = Decimal(1).scaleb(-decimals) / 2
    return any(
        ckind == kind and abs(cvalue - value) <= tolerance
        for ckind, cvalue in covered_numbers
    )


def _body_prose_lines(lines: "list[str]", body_start: int):
    """Yield (index, line) for the lines that carry the argument itself.

    Skipped: the frontmatter block, headings, every line under a
    sources/inputs/assumptions-style heading, table lines, and any line
    preceded by the allow comment. Both figure checks walk the document
    through this one generator, so "body prose" means the same thing to the
    rule that forbids unsourced figures and to the rule that forbids
    over-precise ones.
    """
    in_covered_section = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#"):
            in_covered_section = bool(_COVERED_HEADING_PAT.search(line))
            continue
        if i < body_start or in_covered_section or "|" in line:
            continue
        if i > 0 and lines[i - 1].strip() == ALLOW_COMMENT:
            continue
        yield i, line


def _parse_frontmatter(lines: "list[str]") -> "tuple[dict, int]":
    """Return ({key: value}, index of the line after the closing ---).
    ({}, 0) when there is no frontmatter block."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    fm: dict = {}
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return fm, i + 1
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", lines[i])
        if m:
            fm[m.group(1)] = m.group(2).strip().strip("\"'")
    return {}, 0  # opening --- never closed: treat as no frontmatter


class Linter:
    def __init__(self) -> None:
        self.violations: "list[dict]" = []
        self.truncated = False

    def report(self, path: str, line: "int | None", check: str,
               detail: str) -> None:
        if len(self.violations) >= MAX_VIOLATIONS:
            self.truncated = True
            return
        self.violations.append({
            "file": os.path.basename(path), "line": line,
            "check": check, "detail": detail,
        })

    # -- checks ---------------------------------------------------------------

    def check_frontmatter(self, path: str, fm: dict, has_block: bool) -> None:
        if not has_block:
            self.report(path, 1, "frontmatter",
                        "no YAML frontmatter block (--- ... ---) at the top")
            return
        for key in REQUIRED_KEYS:
            if key not in fm:
                self.report(path, 1, "frontmatter",
                            f"missing required key '{key}'")
        if "research_sources" in fm:
            raw = fm["research_sources"]
            if not re.fullmatch(r"\d+", raw):
                self.report(path, 1, "frontmatter",
                            f"research_sources = {raw!r} must be an integer "
                            ">= 0")
        if "confidence_level" in fm and \
                fm["confidence_level"] not in CONFIDENCE_LEVELS:
            self.report(path, 1, "frontmatter",
                        f"confidence_level = {fm['confidence_level']!r} must "
                        f"be one of {CONFIDENCE_LEVELS}")

    def check_assumptions(self, path: str, lines: "list[str]") -> None:
        for line in lines:
            if line.lstrip().startswith("#") and _ASSUMPTIONS_PAT.search(line):
                return
        self.report(path, None, "assumptions_section",
                    'no heading contains "Assumptions & Limitations" / '
                    '"Premissas e Limitações" / "Premisas y Limitaciones"')

    def check_orphans(self, path: str, lines: "list[str]",
                      body_start: int) -> None:
        covered_tokens: "set[str]" = set()
        covered_numbers: "list[tuple[str, Decimal]]" = []
        in_covered_section = False
        # Pass 1: collect tokens from covered regions (frontmatter, covered
        # sections, table lines).
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                in_covered_section = bool(_COVERED_HEADING_PAT.search(line))
            covered = (
                i < body_start or in_covered_section or "|" in line
            )
            if covered:
                for tok in _FIGURE_PAT.findall(line):
                    covered_tokens.add(_normalize(tok))
                    parsed = _as_number(tok)
                    if parsed is not None:
                        covered_numbers.append((parsed[0], parsed[1]))
        # Pass 2: flag body figures with no covered occurrence.
        for i, line in _body_prose_lines(lines, body_start):
            for tok in _FIGURE_PAT.findall(line):
                if not _is_covered(tok, covered_tokens, covered_numbers):
                    self.report(
                        path, i + 1, "orphan_figure",
                        f"{tok.strip()!r} appears in the body but in no "
                        "sources/inputs/tagged-table section — cite it, tag "
                        f"it, or precede the line with {ALLOW_COMMENT}",
                    )

    def check_prose_precision(self, path: str, lines: "list[str]",
                              body_start: int) -> None:
        """Evidence rule 6: machine precision stays in the artifact.

        Only body prose is read — a table cell, a sources section or the
        frontmatter is where the unrounded value is SUPPOSED to live, and
        check_orphans depends on it living there.
        """
        for i, line in _body_prose_lines(lines, body_start):
            for tok in _PROSE_FIGURE_PAT.findall(line):
                parsed = _as_number(tok)
                if parsed is None:
                    continue
                decimals = parsed[2]
                if decimals <= MAX_PROSE_DECIMALS:
                    continue
                if _significant_digits(parsed[1]) <= MAX_PROSE_SIGDIGS:
                    continue   # nothing left to round to; see module docstring
                self.report(
                    path, i + 1, "prose_precision",
                    f"{tok.strip()!r} shows {decimals} decimal places in "
                    f"body prose — the saved artifact keeps the full "
                    f"precision, the sentence rounds to at most "
                    f"{MAX_PROSE_DECIMALS} (evidence rule 6: machine "
                    "precision stays in the artifact; prose rounds). Round "
                    "it here and state the band, or precede the line with "
                    f"{ALLOW_COMMENT}",
                )

    def lint_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        fm, body_start = _parse_frontmatter(lines)
        self.check_frontmatter(path, fm, has_block=body_start > 0)
        self.check_assumptions(path, lines)
        self.check_orphans(path, lines, body_start)
        self.check_prose_precision(path, lines, body_start)


def _targets(path: str) -> "list[str]":
    if os.path.isfile(path):
        if not path.endswith(".md"):
            raise SystemExit(f"{path} is not a .md file or a directory")
        return [path]
    if os.path.isdir(path):
        return sorted(
            os.path.join(path, n) for n in os.listdir(path)
            if n.endswith(".md") and n != "sources.md"
            and os.path.isfile(os.path.join(path, n))
        )
    raise SystemExit(f"{path} does not exist")


def _run(args, warnings: "list[str]") -> Result:
    res = Result(script=SCRIPT)
    files = _targets(args.path)
    if not files:
        res.warn(f"no lintable .md artifacts found in {args.path} "
                 "(sources.md and subdirectories are excluded by design)")

    linter = Linter()
    for path in files:
        linter.lint_file(path)

    res.add("files_linted", len(files), "count of linted .md artifacts",
            [], unit="files")
    res.add("violation_count", len(linter.violations),
            f"violations found (capped at {MAX_VIOLATIONS})", [])
    if linter.truncated:
        res.warn(f"violation list truncated at {MAX_VIOLATIONS} — fix these "
                 "and re-run")
    if linter.violations:
        res.add_table("violations", linter.violations,
                      "frontmatter / assumptions-section / orphan-figure / "
                      "prose-precision checks")
        res.invariant(
            "artifacts lint-clean", False,
            f"{len(linter.violations)} violation(s)"
            + ("+" if linter.truncated else ""),
        )
    else:
        res.invariant("artifacts lint-clean", True,
                      f"{len(files)} file(s) checked")
    return res


def _add_args(parser) -> None:
    parser.add_argument("path", help="bp_<slug>/ directory or a single .md file")


if __name__ == "__main__":
    cli(SCRIPT, "Lint plan artifacts: frontmatter keys, Assumptions section, "
                "orphan currency/percent figures, over-precise prose figures",
        _run, add_args=_add_args)
