# Web-research protocol

Rules adapted and condensed from founder-os by Vinicius Carvalho
(github.com/vinicius91carvalho/founder-os, MIT: research quality rules, source
hierarchy, recency and cross-referencing rules) and from
codex-startup-business-planner (github.com/Kappaemme-git/codex-startup-business-planner,
MIT: evidence order, research modes, pricing-anchor discipline). Read this
file before sourcing ANY public number, in every route.

## When NOT to use

- Numbers the user already has. Tag them `user` and move on; research does not
  outrank the user's own operating data.
- Private-company internals. Never infer revenue, customers, churn, or costs
  from traffic, GitHub stars, downloads, followers, review counts, or
  headcount. If it is not published, it is `unknown`.
- Willingness to pay. Research produces pricing anchors; only the user's own
  conversations, pre-orders, or actual sales are evidence anyone will pay.
- Primary research. Customer interviews are Mom Test work
  (`references/market-gtm.md`), not web research.
- Claims that no decision rests on. Research what the verdict depends on;
  leave decoration unsourced and unwritten.

## Input checklist

- The claims needing evidence, each phrased as a testable statement ("the
  segment contains N eligible accounts"), ranked by how much the verdict
  depends on them.
- Industry, geography, segment, currency. A US market figure is not evidence
  for a Brazilian plan without an explicit bridge assumption.
- The research mode (see Method) and the time box it implies.
- `bp_<slug>/sources.md` open for archiving as you go, not at the end.

## Method

### Evidence order

Prefer higher rungs; drop down only when a rung is empty (adapted from
codex-startup-business-planner):

1. User-supplied operating numbers and transaction evidence
2. Official product, pricing, documentation, and terms pages
3. Official company announcements or public repositories
4. Direct customer pain, switching, or workaround signals
5. High-quality secondary analysis

Use direct pages, never search-result snippets.

### Source tiers

Label every source with one of the closed tiers (vocabulary from the
interface contract):

| Tier | What qualifies | Examples |
|---|---|---|
| `gov_industry` | Government statistics, regulators, industry bodies, census data | national statistics offices, central banks, trade associations |
| `analyst` | Research firms and analyst reports | Gartner, Forrester, CB Insights and peers |
| `press` | Reputable press coverage, company announcements | business press, official press releases |
| `blog` | Blogs, vendor content, forums, community posts | company blogs, Reddit, HN threads |

The hierarchy is `gov_industry` >= `analyst` > `press` > `blog`. A `blog`
source can prove a pain signal exists; it cannot carry a market-size claim on
its own.

### The two-source rule

Every market claim (size, growth, segment counts, adoption rates) needs at
least 2 independent sources. Independent means separately produced: two
articles citing the same analyst report are one source. A claim that cannot
meet the bar inside the time box is downgraded to `assumption` with the
single source named in `basis`, never silently kept as `public`.

### Citation format and archive

Inline in deliverables: "According to [Source] (URL, accessed YYYY-MM-DD),
[claim]." Every public claim is also archived in `bp_<slug>/sources.md`:

```markdown
| # | Claim it supports | Source | Tier | URL | Published | Accessed |
|---|---|---|---|---|---|---|
| 1 | eligible accounts in segment | <source name> | gov_industry | <URL> | 2025-11 | 2026-08-19 |
```

The artifact frontmatter's `research_sources` is the count of rows here.

### Staleness

Prefer data under 2 years old. Older data may be used only with an explicit
flag in the deliverable ("2022 figure; no newer public source found") and it
caps the claim's confidence at `medium`. Undated sources count as stale.

### Conflicting sources

When sources disagree, report the range, never a silent average: "Source A
reports X, Source B reports Y." If a working value is needed, choose one,
tag the choice `assumption`, and state the basis ("midpoint of the two
published figures" or "lower bound, conservative"). The range stays visible
in the deliverable and both sources stay in `sources.md`.

### Confidence rubric

`confidence_level` in frontmatter is HIGH, MEDIUM, or LOW; per-input
`confidence` is `low | medium | high`; evidence levels are the closed set
`validated | researched | assumption_heavy | unsupported`. They map:

| Claim situation | Input confidence | Evidence level | Frontmatter contribution |
|---|---|---|---|
| User's own primary evidence (sales, cohorts, signed pilots) | high | `validated` | HIGH |
| 2+ independent sources, `gov_industry` or `analyst`, under 2 years | high | `researched` | HIGH |
| One reputable source, or 2+ sources at `press` tier, or stale-but-flagged data | medium | `researched` | MEDIUM |
| Labeled assumption with a stated basis (anchor, midpoint, proxy) | low | `assumption_heavy` | LOW |
| No source and no basis | none: this is not usable | `unsupported` | forces LOW, or INSUFFICIENT_DATA if load-bearing |

The artifact-level `confidence_level` is the LOWEST rating among the claims
the verdict rests on, not an average. One load-bearing guess makes the whole
plan LOW, and the frontmatter says so.

### INSUFFICIENT_DATA criteria

When research comes up empty on a load-bearing claim: record the input as
`unknown` (value null), state in the deliverable that it is unknown, and list
what evidence would settle it ("a count of accounts meeting X, from a
`gov_industry` or `analyst` source, or the user's own channel test"). Never
fill the gap with a plausible number. A section, or a whole plan, honestly
returning INSUFFICIENT_DATA is a legitimate deliverable; the scripts treat it
the same way (exit 2).

### Competitor pricing is an anchor

Tag competitor prices `public` with the pricing-page URL and access date.
They anchor the `price` driver and the tier design; they are never
willingness-to-pay evidence, and no deliverable may present them as proof
anyone will pay. Normalize only comparable units; keep regional pricing,
annual-prepay discounts, and "contact sales" gaps explicit.

### How tags enter the state file

`public` requires `source_url` AND `source_date`. The runtime
(`bp_common.parse_inputs`) downgrades an uncited `public` input to
`assumption` with a warning; the validator is strict and fails (exit 3). Run
it before computing:

```bash
BP=~/.claude/skills/business-planning/scripts/bp.sh
$BP validate bp_acme/acme.bp.json
```

Format illustration (placeholder values, not data):

```json
{"inputs": {
  "eligible_accounts": {"value": 100000, "status": "public",
    "source_url": "https://<official-source>", "source_date": "2026-08-19",
    "confidence": "medium"},
  "pct_reachable": {"value": 0.2, "status": "assumption",
    "basis": "midpoint of the two published channel figures; range 0.1 to 0.3"},
  "serviceable_segment": {"value": null, "status": "unknown"}
}}
```

### Research modes

Mode vocabulary adapted from codex-startup-business-planner (MIT); record the
mode in `.bp.json` meta and the artifact frontmatter.

| Mode | When | Bar |
|---|---|---|
| `quick` | Time-boxed first pass | Up to 3 comparables. The two-source rule still holds: what misses it becomes `assumption`, not waived `public`. |
| `standard` | Default | 3 to 8 comparables; 2+ sources per market claim; all tiers labeled. |
| `deep` | High-stakes or `innovation` depth | 5 to 8+ comparables, broader substitute set, granular cost evidence, contradiction checks rerun after drafting. |
| `pre-revenue` | No revenue history exists | Comparable pricing anchors plus validation evidence; forward numbers enter only as scenario drivers (see full-plan.md pre-revenue substitutions). |
| `audit` | EVALUATE route | Verify the existing plan's citations before proposing changes; every uncited figure in the audited plan is a finding, not something to repair silently. |

## Benchmarks with provenance

This protocol file carries no market figures, deliberately. A benchmark may
enter a deliverable in exactly two forms:

1. A cited figure: source name, tier label, URL, access date, archived in
   `sources.md`, subject to the two-source rule if it is a market claim.
2. A labeled framework heuristic with its origin named, for example
   "LTV > 3x CAC, SaaS viability heuristic" as documented with provenance in
   `financial-analysis/references/viability.md`. Quote bands from that file,
   never from memory: any band cited from memory is an `assumption` and gets
   tagged as one.

## Handoffs

- **`references/market-gtm.md`**: turning researched counts into the
  bottom-up sizing chain, and Mom Test interviews when the missing evidence
  is primary.
- **`references/full-plan.md`**: where researched claims land per part, and
  the frontmatter this protocol feeds.
- **financial-analysis** (`references/viability.md`): localization research
  for payroll burden and tax, done with the user, component by component.
- **sat**: challenge assumption-heavy claims before they become load-bearing.
- **`references/evaluate.md`**: the `audit` mode's full procedure.
