# financial-analysis — skill memory

Read at Step 0 of every analysis. Written by the Step 7 retrospective.
Entry format: `- [YYYY-MM-DD · domain] lesson. Apply: how.`
Consolidate when this file exceeds ~150 lines (merge duplicates, prune superseded;
calibration lessons age best — prune them last).

## Calibration lessons

- [2026-08-19 · company] Disclosed FCF can diverge from OCF−capex (Datadog also
  subtracts capitalized software: $915M vs $1,000.6M in FY25). Apply: prefer the
  company's disclosed figure, report both, state the definition gap.
- [2026-08-19 · company] DSO/turnover switch basis (average vs period-end) depending
  on whether a prior period is loaded — never compare across runs with different
  bases. Apply: same-base comparisons only; note the basis next to the number.
- [2026-08-19 · company] Net-debt/EBITDA is mathematically valid but analytically
  meaningless when net debt is negative and EBITDA ≈ 0 (−723x on Datadog). Apply:
  report "net cash position" instead of the multiple in that regime.

## Preferences

- [2026-08-18 · general] Leo works in PT-BR/EN mixed; skill outputs default to
  English per his choice, but he may ask for reports in Portuguese. Apply: match
  the language he uses in the session.
- [2026-08-18 · general] Payroll/taxes are country-dependent by design — never
  assume a country. Apply: ask the country, research components on the web, tag
  each with source (see viability.md localization step).

## Recurring analyses

(none yet)

## Process fixes

- [2026-08-19 · saas] User-stated rates ("~4% churn") block count-based metrics.
  Apply: encode as a synthetic ratio pair (churned 4 / start 100), counts tagged
  `assumption`, at Step 2 — scripts then compute everything downstream.
- [2026-08-19 · general] For a verdict-critical unknown (e.g. ARPA), a break-even
  reversal beats a point assumption — a segment ceiling can make the conclusion
  assumption-independent. Apply: solve the reversal first, compare to the bound.
- [2026-08-19 · general] Threshold/trigger conversions (annual↔monthly, per-quarter)
  are mental-math bait. Apply: put them in a scratch Python file run via Bash, like
  any other calculation.
- [2026-08-19 · company] For US public companies, SEC's XBRL companyfacts API is the
  primary source (curl with a User-Agent header; IR pages and newswires often block
  fetchers — 3 failed fetches before the pivot in the Datadog run). Apply: EDGAR API
  first for statements; the press release/transcript only for NRR, customers, guidance.
