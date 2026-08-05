---
name: catalogo-normalize
description: >-
  Normalizes a Spanish-language book catalog/inventory CSV (the 14-column schema — e.g. an
  Alexandria OS export, a `<date>_Inventario.csv`, or a `Página1.csv`) into the project's canonical
  form. Deterministic, idempotent, free (no agents). Standardizes Autor (`Apellidos, Nombre`),
  Editorial (canonical dedup), Año (YYYY), Categoría (closed 52-entry BISAC_ES set), Sinopsis
  (strips HTML/meta/boilerplate, never invents), Edición (closed vocab). Marketplace-agnostic —
  runs BEFORE pricing and any IberLibro/CDL export. Use whenever a dated catalog batch needs its
  data cleaned/standardized, or when the user says "normalizar o catálogo/lote", "arrumar os
  dados/as colunas", "limpar o CSV do Alexandria", "fix batch", "preparar o inventário", or a fresh
  `<date>_Inventario.csv` appears. Reports the `Sin clasificar` count and points to the paid
  `catalogo-resolver-categorias` skill. Trigger even if the user doesn't name the columns — if it's
  a 14-col Spanish book CSV to clean before sale, this is it.
---

# catalogo-normalize

Normalizes a dated catalog batch's six dirty columns into the project's canonical form. It is the
**first, upstream, marketplace-agnostic** step: `Alexandria OS export → THIS → resolve categories →
price → IberLibro / CDL`. Deterministic, idempotent, and free (no paid agents).

## What it fixes (columns C, D, E, F, G, I)

- **Autor** → `Apellidos, Nombre`; `Varios Autores` and `Autor Desconocido` kept **distinct**.
- **Editorial** → canonical name (deep-dedups variants of the same publisher).
- **Año** → 4-digit `YYYY`; drops the `1900` sentinel and out-of-range values.
- **Categoría** → the closed **52-entry `BISAC_ES`** set (classifier + override module if present).
- **Sinopsis** → cleanup only: strips HTML, Amazon meta-headers, the Al Alimón boilerplate.
  **Never invents** (R2). Empty stays empty.
- **Edición** → closed vocab (`1`–`4`, `5.ª edición o posteriores`, `Traducción`, `Reimpresión`, or empty).

Every other column (ISBN, Título, Páginas, Idioma, Cantidad, Disponible, Ubicación, Precio) is
preserved verbatim. Pricing and page/synopsis enrichment are separate, later steps.

## How to run (the standard case)

From the Iberlibros project root:

```
.venv/bin/python3 scripts/fix_batch.py "<batch_folder>/<batch>_Inventario.csv"
```

It writes, next to the source:
- `<batch>_Inventario_fixed.csv` — the normalized 14-column CSV (input for everything downstream).
- `<batch>_Inventario_audit.csv` — one row per changed cell (ISBN, Columna, Antes, Después).

The `--slug DD_MM` flag overrides the category-override module name (default: the batch folder's
`DD_MM`). Read `scripts/fix_batch.py` to adapt if a batch has a non-standard schema or filename.

## When to run the script vs. reason manually

- **Run the script** for the standard single-file 14-column batch. It reuses the project's
  `hbimport_fix_authors / _publishers / _categories` and `taxonomy` modules — the source of truth
  with ~400 author hints. Do not fork or reinvent those rules.
- **Reason manually** (read the script, adapt) only for: a schema that isn't the canonical 14 columns,
  a source that isn't UTF-8/comma-CSV, or a one-off audit of why a specific row changed.

## The category fail-safe (why re-running is safe)

`fix_category` applies overrides in priority order (dataset verification → generic verification →
dataset agent → keep-valid → classifier → generic agent → `Sin clasificar`). The dataset-specific
override module (`_agent_category_overrides_<slug>.py`) is imported with a `try/except`, so:
- **Before** category resolution: the module is absent → hard rows land on `Sin clasificar`.
- **After** resolution: the module exists → those rows resolve on a re-run.
Same script, both passes — idempotent and never crashes.

## The report you should give the user

Lead with the outcome, then the numbers:
1. Rows processed and total cells changed (per-column breakdown from the run output).
2. **`Sin clasificar` count** — if > 0, say so plainly and point to the next skill:
   "N rows are still `Sin clasificar`; run **`catalogo-resolver-categorias`** (paid agent pass)
   to resolve them, then re-run this."
3. Confirm the invariants: **0** empty Categoría, **0** out-of-BISAC. Note empty Sinopsis (expected).
Do not dump a wall of stats.

## Edge cases (handle without prompting)

| Condition | Action |
|---|---|
| Schema ≠ the 14 canonical headers | the script asserts and stops — report the drift, don't force it |
| Batch folder name isn't `DD_MM_YYYY` | pass `--slug` explicitly |
| Override module absent | expected on the first pass — `Sin clasificar` rows are honest, not an error |
| `VARIOS` / `AA.VV.` author | → `Varios Autores` (never collapse to `Autor Desconocido`) |
| Re-run on already-fixed output | idempotent — same bytes out |

## What success looks like

A `<batch>_fixed.csv` with 14 columns, **0 empty Categoría**, **0 out-of-BISAC**, authors/editorials
normalized, synopses cleaned (none invented), and an honest `Sin clasificar` count — ready for the
category-resolution, pricing, and marketplace-export steps.
