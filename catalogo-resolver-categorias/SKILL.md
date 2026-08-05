---
name: catalogo-resolver-categorias
description: >-
  Resolves the leftover `Sin clasificar` book categories that `catalogo-normalize` could not
  classify, using a verified 30-agent classify+verify Workflow. PAID and non-deterministic — state
  the cost and get explicit opt-in before running. Produces a REVIEW-candidate override module that
  `catalogo-normalize` applies on a re-run, and runs a reinforcement loop: reflects (problem-solving +
  SAT) on what the agents resolved, surfaces candidate deterministic hints (publisher/author/title
  patterns) so the FREE classifier gets smarter and needs fewer paid passes over time, and records the
  learnings + `Sin clasificar` trend to project memory. Use ONLY when a normalized batch still has
  `Sin clasificar` rows AND the user opts into the paid pass; triggers on "resolver as categorias",
  "classificar as que sobraram", "rodar os agentes de categoria", "resolve categories". Never
  auto-runs, never auto-edits the classifier, never auto-trusts new hints — everything is a candidate
  for human review.
---

# catalogo-resolver-categorias

Second, **paid**, occasional step: takes the `Sin clasificar` rows left by `catalogo-normalize` and
resolves them with a verified agent Workflow, then feeds a self-improvement loop back into the free
classifier. `normalize → THIS → (re-normalize) → price → export`.

## ⚠️ Cost gate — always, before anything

This runs **~2 agents per batch of 14 rows** (a 30-agent pass for ~200 rows). It is **paid and
non-deterministic**. Do **not** start it without: (1) confirming the batch actually has
`Sin clasificar` rows, and (2) an explicit user "yes, run the paid pass". State the rough agent count
first. If there are 0 `Sin clasificar` rows, say so and stop — no pass needed.

## The loop (run from the Iberlibros project root)

1. **Split** the unresolved rows into agent batches:
   ```
   .venv/bin/python3 scripts/split_sinclasificar.py "<batch>/<batch>_Inventario_fixed.csv"
   ```
   It prints `batch_count=N  batch_dir=<...>/_cat_batches`. (0 rows → stop, nothing to do.)

2. **Run the Workflow** (this is the paid step) via the `Workflow` tool:
   `scriptPath: scripts/wf_resolve_categories.js`, `args: {"batchDir": "<...>/_cat_batches", "batchCount": N}`.
   Each batch gets a Classify agent (assigns a closed-set `BISAC_ES` category) then an adversarial
   Verify agent (confirms / corrects / reverts to `Sin clasificar`). It returns
   `{ overrides, verification, assignedCount, stillUnclassified }`.

3. **Persist as a REVIEW candidate** (never the live module directly). Save the Workflow return to a
   JSON, then:
   ```
   .venv/bin/python3 scripts/persist_category_overrides.py <workflow_return.json> --slug DD_MM
   ```
   It validates every value ∈ `BISAC_ES` (aborts otherwise, R3) and writes
   `scripts/_agent_category_overrides_<slug>_CANDIDATE.py`.

4. **Human review, then promote.** Show the user the candidate mappings (watch the LEARNINGS traps:
   mononyms over-matching, coincidental token overlap). Only after approval:
   `mv scripts/_agent_category_overrides_<slug>_CANDIDATE.py scripts/_agent_category_overrides_<slug>.py`

5. **Re-run `catalogo-normalize`** — now the module imports and the rows resolve; a small honest
   `Sin clasificar` remainder is expected and fine.

## Phase 5 — Memory + reinforcement (the self-improvement part)

The point of this loop is to need the paid agents **less** each batch. After promoting the overrides:

1. **Surface the patterns** (deterministic seed):
   ```
   .venv/bin/python3 scripts/reflect_categories.py "<batch>/<batch>_Inventario_fixed.csv" --slug DD_MM
   ```
   It reports candidate **publisher / author / title-token → category** hints (strong, high-purity
   associations among what the agents resolved) → `_reflection_<slug>.json`.
2. **Reflect with the frameworks** (this is judgment, not a script):
   - `/problem-solving` — a MECE issue tree of *why* those rows slipped the classifier (a whole
     publisher? an author the hints miss? a title pattern?). Push past "N resolved" to the synthesis.
   - `/sat` Key Assumptions Check — which classifier assumptions the agent decisions disconfirm.
3. **Propose hints for review** — turn the high-confidence patterns into new `AUTHOR_HINTS` /
   title-patterns / publisher-hints for `hbimport_fix_categories.py`. Gate with
   `/verification-before-completion`. **Never auto-edit** the classifier — the user promotes hints.
4. **Persist to memory** — write the learnings to the project memory (`memory/` + `MEMORY.md`) and
   `docs/LEARNINGS.md` (R7); record this batch's `Sin clasificar` count as the trend metric
   (via `agentmemory:remember`). Periodically run `/consolidate-memory`.
5. **Reinforcement signal** — `Sin clasificar` should trend **down** batch-over-batch as good hints
   land → fewer paid passes. That trend is how you know the loop is working.

## Edge cases

| Condition | Action |
|---|---|
| 0 `Sin clasificar` rows | stop before spending — report "nothing to resolve" |
| User hasn't opted into cost | do not run the Workflow; ask first |
| Workflow value not in BISAC_ES | `persist` aborts (R3) — surface it, don't force |
| Candidate looks wrong on review | do NOT promote; fix or drop the bad mappings |
| Re-running the paid pass | avoid — the agents are non-deterministic and cost money; only re-run if new rows appeared |

## What success looks like

The batch's hard categories resolved (via a **reviewed** override module), a handful of honest
`Sin clasificar` remaining, and — the real win — a set of **reviewed deterministic hints** added to
the classifier plus a memory entry showing the `Sin clasificar` trend dropping, so the next batch
leans less on the paid agents.
