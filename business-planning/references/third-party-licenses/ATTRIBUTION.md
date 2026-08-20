# Third-party attribution

The business-planning skill adapts ideas and structures from four MIT-licensed
repositories and credits one unlicensed source at the concept level only. The
verbatim license texts sit next to this file, fetched from each repository's
default branch on 2026-08-19. No donor code ships in this skill: all scripts
were written for this skill against its own contract; what was adapted is
structure, framework selection, and workflow shape, as listed below.

## codex-startup-business-planner (MIT)

- Repository: https://github.com/Kappaemme-git/codex-startup-business-planner
- Copyright (c) 2026 Francesco Mistero. License: codex-startup-business-planner-LICENSE.
- Adapted: the eight readiness dimensions and their weights used by
  `bp.sh readiness` (problem_evidence 15, icp_specificity 10, reachable_market 10,
  positioning 15, model_pricing 15, gtm 15, unit_economics 10, execution 10),
  per the skill's frozen interface contract. The evidence multipliers layered on
  top (validated 1.00 / researched 0.75 / assumption_heavy 0.50 /
  unsupported 0.25) are this skill's own addition, not the donor's. The donor's
  overall shape (evidence-backed plan, pricing strategy, 90-day roadmap) also
  informed the FULL-PLAN route and the roadmap-90d.csv template.

## founder-os (MIT)

- Repository: https://github.com/vinicius91carvalho/founder-os
- Copyright (c) 2026 Vinicius Carvalho. License: founder-os-LICENSE.
- Adapted: the curation of founder frameworks encoded as skill knowledge,
  informing this skill's market and GTM reference material (Mom Test-style
  interview discipline, MEDDIC/BANT qualification, go/pivot/kill framing) and
  the idea-to-scale route structure.

## pm-skills (MIT)

- Repository: https://github.com/phuryn/pm-skills
- Copyright (c) 2026 Pawel Huryn. License: pm-skills-LICENSE.
- Adapted: conventions for packaging product-management practice as agentic
  skills, informing this skill's discovery-to-strategy structures (ICP and
  anti-ICP schema, positioning and competition framing) and its
  one-artifact-per-module route design.

## ai-business-planner (MIT)

- Repository: https://github.com/shinpr/ai-business-planner
- Copyright (c) 2025 Shinsuke Kagawa. License: ai-business-planner-LICENSE.
- Adapted: the guided multi-artifact workflow shape (market research, plan,
  pitch material produced from one session state) and the concept of carrying
  insights from previous projects forward, which informed this skill's
  MEMORY.md reinforcement loop and per-project bp_<slug>/ workspace.

## FISY (concepts only, no license)

- Source: https://fisy.fr, which has no published license, so nothing was
  copied: no files, no formulas, no sheet layouts.
- Credited concepts: the complexity ladder behind this skill's depth vocabulary
  (starter / essential / innovation) and the idea of a financial-plan line
  checklist (a plan enumerates its financial lines and marks each one covered
  or missing). Both appear here as re-derived concepts; every implementation
  detail is this skill's own, and all financial computation is delegated to the
  separately-built financial-analysis skill.
