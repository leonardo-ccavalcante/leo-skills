# Company Analysis — statement ratios, DuPont, trends

Domain 2: analyzing a real company from its income statement and balance sheet.
The script is `ratios` (`scripts/ratios.py`); reversal thresholds use scratch
Python (see Trend analysis — `fa.sh scenarios` has no statement model, on purpose).
This reference carries the thinking; every number comes from the script.

## When NOT to use

- **Single-period data presented as a trend.** One year of ratios is a snapshot.
  Never write "improving", "deteriorating", or any directional verb without a
  prior period loaded via `--prior-inputs-file` — the YoY table is the only
  licensed source of trend language.
- **Cross-company comparison across different accounting policies or fiscal
  years.** IFRS vs US GAAP, capitalized vs expensed development, operating vs
  finance leases, and misaligned year-ends all shift the same ratio for
  non-economic reasons. Compare companies only when the user confirms comparable
  policies, and say so in the method note.
- **Banks, insurers, and other financial institutions.** Their balance sheets
  invert the meaning of leverage and liquidity — a 10x equity multiplier is
  normal for a bank and alarming for a retailer. This generic ratio set will
  produce confident nonsense; tell the user the framework does not apply.
- **Statements pasted from a PDF or screenshot without an agreed line-item
  mapping.** "Total debt" in a filing may or may not include leases; "cost of
  revenue" may or may not include depreciation. Transcribe together with the
  user (flow below) before computing — a wrong mapping poisons every ratio
  downstream while looking perfectly precise.

## Inputs

Exact field names from `ratios.py`. Every field is optional — the script
computes whatever the given subset supports — but the minimal set below is what
makes an analysis worth reporting.

**Minimal viable set** (unlocks margins, ROA/ROE, DuPont, common-size):
`revenue`, `net_income`, `total_assets`, `total_equity` — plus
`current_liabilities` and `current_assets` if liquidity matters to the decision.

**Full set:**

| Income statement | Balance sheet |
|---|---|
| `revenue`, `cogs`, `gross_profit`, `operating_expenses`, `operating_income`, `depreciation_amortization`, `ebitda`, `interest_expense`, `pretax_income`, `tax_expense`, `net_income` | `cash`, `accounts_receivable`, `inventory`, `current_assets`, `total_assets`, `accounts_payable`, `current_liabilities`, `total_debt`, `total_liabilities`, `total_equity` |

**Derivation cascade** — do not interrogate the user for lines the script can
derive. When absent, the script fills, in order:
`gross_profit = revenue - cogs`, then
`operating_income = gross_profit - operating_expenses`, then
`ebitda = operating_income + depreciation_amortization` — each surfaced as a
warning because a derived line carries the combined uncertainty of its parents.
Relay those warnings: the user should know which numbers they stated and which
were computed. If the user's statement shows a different figure than the
derivation implies (e.g., EBITDA per their reporting excludes stock comp),
prefer their stated line and record the discrepancy.

**Prior period** unlocks the YoY table and switches turnover/days ratios to
proper average balances. Without it the script falls back to period-end values
and warns "using period-end values, not averages" — relay that caveat whenever
you quote a turnover or days figure, because a fast-growing balance sheet makes
period-end turnover look artificially weak.

**PDF/screenshot flow**: never load a PDF and guess. Read the statement with
the user, agree what each filing line maps to (especially `total_debt`,
`operating_expenses`, `cogs`), transcribe values into a tagged JSON file where
every line is tagged `user` (the user is vouching for the transcription), show
the table for confirmation, then compute. Save it as `<company>-fy<yy>.fa.json`.

## Ratio catalog by family

Interpretation guidance plus the guards the script enforces. A guard firing is
information, not a failure — relay its reason verbatim; it is often the most
diagnostic sentence in the analysis.

### Profitability — margins
`gross_margin_pct`, `operating_margin_pct`, `ebitda_margin_pct`,
`net_margin_pct` (each line / revenue × 100). The gap *between* margins is the
story: gross→operating gap is the opex load; operating→net gap is interest and
tax. **Guard:** revenue must be > 0 — a margin on zero or negative revenue is
meaningless division dressed as insight.

### Profitability — returns
- `roa` — net_income / total_assets (average basis when a prior exists,
  period-end otherwise, without a warning: period-end ROA is standard practice
  with one balance sheet).
- `roe` — net_income / total_equity. **Guard: negative equity skips ROE
  entirely** ("negative equity — ROE not meaningful"): with equity below zero,
  a loss produces a *positive* ROE and a profit a negative one — the sign flips
  and any reading misleads. Negative equity is itself the Tier 1 finding
  (accumulated losses or heavy buybacks); report that, not a ratio.
- `effective_tax_rate_pct` — tax_expense / pretax_income, guarded pretax > 0
  (a tax rate on a pretax loss inverts meaning the same way).
- `roic_approx` — operating_income × (1 − effective tax rate) / (total_debt +
  total_equity). Labeled approximate: invested capital here is book debt +
  equity, not the adjusted figure an analyst would build. Use it directionally.

### Liquidity
`current_ratio` (current_assets / current_liabilities), `cash_ratio`
(cash / current_liabilities), `quick_ratio`
((current_assets − inventory) / current_liabilities). **Guards:**
current_liabilities > 0; and **missing inventory skips the quick ratio** —
without knowing inventory, quick and current are indistinguishable, and
silently assuming inventory = 0 would overstate the most conservative
liquidity measure exactly when it matters. If the company genuinely holds no
inventory (pure services/SaaS), have the user state `inventory: 0` tagged
`user` — that is a fact, not a gap.

### Solvency
- `debt_to_equity` — guarded equity > 0 (same sign-flip problem as ROE).
- `debt_to_assets` — the fallback leverage view when equity is negative;
  assets rarely go negative, so this one survives distress cases.
- `net_debt_to_ebitda` — (total_debt − cash) / ebitda. **Guard: EBITDA ≤ 0
  skips the multiple** ("leverage multiple not meaningful"): a leverage
  multiple answers "how many years of earnings to repay debt", and with
  negative earnings the answer is "never at current performance" — a negative
  multiple would look small and benign when the situation is the opposite.
  Negative EBITDA plus material debt is itself a CRITICAL finding.
- `interest_coverage` — operating_income / interest_expense, guarded
  interest_expense > 0: with no debt service there is nothing to cover, and
  the ratio would be division by zero presented as strength.

### Efficiency
`asset_turnover` (revenue / total_assets), `dso`, `dio`, `dpo` (365-day basis
on revenue or cogs), and `ccc` = dso + dio − dpo, computed only when all three
components exist. Guards: revenue > 0 for dso/turnover, cogs > 0 for dio/dpo.
A lengthening CCC means cash is increasingly trapped in the operating cycle —
often the earliest statement-visible sign of channel stuffing or slowing
demand. All use average balances when a prior period exists (see caveat above).

## DuPont — the narrative pattern

ROE alone says nothing about *why*. The script decomposes it:

- **3-way**: `roe_dupont` = net margin × asset turnover × `equity_multiplier`
  (total_assets / total_equity), all period-end so the identity ties to `roe`
  exactly — the script enforces the tie within 0.1pp as an invariant.
- **5-way adds** `tax_burden` (net_income / pretax_income) and
  `interest_burden` (pretax_income / operating_income), guarded pretax > 0 and
  operating_income > 0, isolating tax and financing effects from operations.

**The finding is WHICH lever moved.** With two periods, run ratios on each and
compare components: ROE up on margin is operating improvement; ROE up on the
equity multiplier is added leverage — same headline, opposite risk story; ROE
flat while margin fell and leverage rose is deterioration hiding under a
stable number. In the 5-way, ROE that improved via tax_burden or
interest_burden is financing/tax engineering, not a better business. Read
component deltas from the two script runs — never compute the attribution in
your head.

## Benchmarking rules

- Industry benchmarks must be `public` with a URL (industry aggregates,
  Damodaran datasets, disclosed peer filings) or an explicit `assumption` with
  its basis stated. Ratio norms vary so much by industry (grocery ~2% net
  margin, software ~20%+) that an unsourced "industry average" can flip a
  verdict — which is exactly why memory-pulled numbers get tagged
  `assumption`, including everything in the table below.
- Absent industry data, use only these rough cross-industry sanity anchors —
  never as a verdict source on their own:

| Anchor (as of 2026-08; textbook conventions, directional only) | Band |
|---|---|
| Current ratio | ~1.5–3.0 comfortable; <1.0 WATCH; >3.0 possibly idle capital |
| Quick ratio | ≥1.0 comfortable |
| Interest coverage | >3x comfortable; <1.5x CRITICAL territory |
| Net debt / EBITDA | <3x typical comfort; >4x leveraged |
| Debt-to-equity | <1x conservative; >2x aggressive outside capital-intensive sectors |

These are assumptions to be tagged in the report, and stage/sector context
overrides them — a utility lives happily at leverage that would sink a retailer.

## Trend analysis

With `--prior-inputs-file`, the script emits a `yoy_deltas` table: per line,
current, prior, `delta_pct`, and a `variance_class` on the ladder
**<5% "note" · 5–10% "line" · >10% "paragraph" · >20% "escalate"**. Narrative
depth follows the class — a clause for a note, a sentence for a line, a
paragraph with a cause hypothesis for a paragraph, top-of-report placement for
an escalate. Where prior is zero, `delta_pct` is null and the class reads
"undefined (prior is zero)" — report "new line item", never a percentage.

Any explanation you attach to a variance ("revenue fell because of churn") is
an `assumption` until the user confirms it — the statements show *that* a line
moved, never *why*.

**Reversal thresholds for statements — scratch Python, not `fa.sh scenarios`.**
The scenarios engine deliberately has no `ratios` model: statement lines are
bound by accounting identities the engine cannot know (mutate `revenue` while
`gross_profit` stays stated and the implied COGS goes negative — arithmetic
that computes cleanly and means nothing). Partial mutation of a statement
produces exactly the plausible-but-wrong numbers this skill exists to prevent.
Instead, for the 2–3 deltas driving the verdict, solve the reversal in a small
scratch Python script run via Bash, over the *identity in question* — closed
form when it exists (e.g. the opex growth rate `g` where
`opex_prior × (1+g) = gross_profit_current` is the operating break-even), or
`finmath.bisect_solve` when it doesn't — saving the outputs as JSON like any
other script run. Feed the thresholds into the kill-assumptions table.

## Worked examples

```bash
FA=~/.claude/skills/financial-analysis/scripts/fa.sh

# Quick single-period check, numbers stated in conversation
$FA ratios --inputs '{
  "revenue":             {"value": 12400000, "status": "user"},
  "cogs":                {"value": 5100000,  "status": "user"},
  "operating_expenses":  {"value": 4900000,  "status": "user"},
  "net_income":          {"value": 1350000,  "status": "user"},
  "total_assets":        {"value": 9800000,  "status": "user"},
  "total_equity":        {"value": 4200000,  "status": "user"},
  "current_assets":      {"value": 3600000,  "status": "user"},
  "current_liabilities": {"value": 2100000,  "status": "user"},
  "inventory":           {"value": 0, "status": "user",
                          "basis": "services company, confirmed no inventory"}
}' --json
# Expect warnings: gross_profit and operating_income derived; turnover on
# period-end basis. missing[] will ask for the prior period (priority 3).

# Full two-period analysis from saved tagged files
$FA ratios --inputs-file acme-fy25.fa.json \
  --prior-inputs-file acme-fy24.fa.json --json
# Unlocks yoy_deltas with variance_class and average-basis turnover/days.
```

`--prior-inputs` (inline JSON) and `--prior-inputs-file` are mutually
exclusive — the script exits if both are passed.

## Report body sections (extend the SKILL.md skeleton)

Between "Key numbers" and "Top issues", add:

- **Ratio dashboard** — one table per family (profitability, liquidity,
  solvency, efficiency): value, tag, benchmark band with source and date,
  verdict from the closed vocabulary. Show guarded ratios as "not computed —
  <script reason>", never as blanks.
- **DuPont bridge** — ROE with its 3-way (and 5-way when available)
  components for each period, and one sentence naming which lever moved.
- **Top issues (max 3)** and **Watch items** — issues are findings demanding
  action now; watch items are deltas classed "paragraph"/"escalate" or ratios
  drifting toward a band edge, each paired with the decision trigger that
  would promote it to an issue.
