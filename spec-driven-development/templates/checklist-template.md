# Checklist: [DOMAIN] — [FEATURE NAME]

**Purpose:** validate the *quality of the requirements themselves* — NOT implementation behavior.
**Created:** [YYYY-MM-DD] · **Spec:** [link]

> CRITICAL: every item asks about the requirement, never the code.
> ❌ "Verify the button click works" / "Test error handling"
> ✅ "Are visual-hierarchy requirements quantified?" / "Is edge-case behavior documented for empty input?"
> Tag each item with a quality dimension and a `[Spec §X.Y]` reference (aim ≥80% traceable; use `[Gap]`/`[Ambiguity]` markers otherwise).

## Completeness
- [ ] CHK001 Are all primary user workflows covered by functional requirements? [Completeness] [Spec §…]
- [ ] CHK002 Is every error/edge case from the scenarios reflected as a requirement? [Coverage] [Spec §…]

## Clarity & Measurability
- [ ] CHK003 Are success criteria measurable (numbers, thresholds, time)? [Measurability] [Spec §…]
- [ ] CHK004 Are ambiguous terms ("fast", "secure", "user-friendly") quantified? [Clarity] [Ambiguity]

## Consistency
- [ ] CHK005 Do requirements avoid contradicting each other or the constitution? [Consistency] [Spec §…]
- [ ] CHK006 Is terminology used consistently across the spec? [Clarity] [Spec §…]

## Gaps
- [ ] CHK007 Are non-functional constraints (performance, security, scale) stated? [Gap]
- [ ] CHK008 Are out-of-scope items explicitly listed? [Completeness] [Spec §…]
