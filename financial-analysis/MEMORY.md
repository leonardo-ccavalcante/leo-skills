# financial-analysis — skill memory

Read at Step 0 of every analysis. Written by the Step 7 retrospective.
Entry format: `- [YYYY-MM-DD · domain] lesson. Apply: how.`
Consolidate when this file exceeds ~150 lines (merge duplicates, prune superseded;
calibration lessons age best — prune them last).

## Calibration lessons

(none yet)

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
