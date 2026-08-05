---
name: iberlibro-csv-converter
description: Convert a bookseller CSV export into the strict tab-delimited TXT that Iberlibro and AbeBooks require for inventory bulk-upload, with pre-flight cleaning and post-conversion byte-level verification so the file uploads with zero rejections. Use this skill whenever the user provides a CSV destined for Iberlibro, AbeBooks, Iberlibros, or any AbeBooks-family marketplace; whenever they say things like "convert CSV to TXT for upload", "preparar archivo iberlibro", "subir libros", "process this CSV for AbeBooks"; whenever they say "repite el proceso" / "do the same as last time" and the prior context involved a book CSV; or whenever they attach a CSV whose filename contains 'iberlibro', 'abebooks', or 'libros'. Trigger this skill even when the user does not name the marketplace — if a CSV has the 30-field AbeBooks schema (listingid, title, author, isbn, price, quantity, etc.), this is the right workflow.
---

# Iberlibro / AbeBooks CSV → TXT Converter

## What this skill does

Takes a CSV exported from a book inventory tool and produces a TXT file that the Iberlibro / AbeBooks bulk-upload endpoint will accept on the first try.

The marketplace's parser is strict in three specific ways that break naive conversions:

1. **Format-level**: it expects UTF-8 *without* BOM, Unix line endings (LF, not CRLF), TAB as field delimiter, and exactly 30 columns in the canonical order.
2. **Data-level**: any newline, tab, or carriage return *inside a cell* breaks the row alignment for every subsequent row. Empty title/ISBN/price/quantity/description rejects the row.
3. **Numeric-level**: prices should be normalized decimals (`49.90` not `49.9` or `49,90`); quantities should be integers.

This skill handles all three and verifies the output by re-reading it.

## When to run the script vs. think it through manually

**Run the script (`scripts/convert.py`) directly** when:
- The input is a single CSV file at a known path
- The user wants the standard output (cleaned TXT + verification report)

**Think it through step by step** when:
- The CSV has a non-standard schema (different field names, fewer/more columns)
- The user wants to filter rows (e.g., only books with ISBN, only books over a price threshold, only a specific language)
- Multiple CSVs need to be merged before conversion
- The user reports that a prior upload was rejected and wants to investigate why

In the second case, read the script source to understand the canonical rules, then adapt — don't reinvent the cleaning/verification logic.

## How to invoke the standard workflow

```bash
python /path/to/skill/scripts/convert.py <input.csv> <output.txt>
```

The script:
1. Reads the CSV with `utf-8-sig` encoding (handles BOM gracefully)
2. Verifies the 30 canonical fields are present
3. Cleans every cell (strips control chars, collapses whitespace)
4. Normalizes price to two decimals and quantity to integer
5. Writes UTF-8 without BOM, LF endings, TAB delimiter, exact field order
6. Re-reads the output and runs full verification
7. Prints a structured report ending in either `✅ ARCHIVO 100% CORRECTO` or `❌ HAY PROBLEMAS`

After running, copy the output TXT to `/mnt/user-data/outputs/` and call `present_files` so the user can download it.

## Canonical 30-field schema

These are the fields, in this exact order. The script enforces this — do not change the order even if the input CSV has them differently. Missing fields cause a hard fail; extra fields are dropped silently.

```
listingid, title, author, illustrator, price, quantity,
producttype, description, bindingtext, bookcondition,
publishername, placepublished, yearpublished, isbn,
sellercatalog1, sellercatalog2, sellercatalog3, abecategory,
keywords, jacketcondition, editiontext, printingtext,
signedtext, volume, size, imgurl, weight, weightunit,
shippingtemplateid, language
```

## The verification protocol (why it matters)

The script does not trust its own write step. After writing, it re-opens the file in two modes:

- **Binary mode** to check the first three bytes (BOM detection) and scan for `\r\n` (CRLF detection)
- **Text mode through csv.DictReader** with `delimiter='\t'` to confirm every row parses back into 30 fields, and to scan every cell for residual `\n` / `\t` / `\r`

This catches the failure modes that cost the most time: the conversion looked fine, the file was uploaded, and the upload silently dropped half the rows because one description had an embedded newline that misaligned everything that followed.

## The report you should give the user

After the script runs, summarize the verdict in this structure (Pyramid Principle: governing claim first, then the supporting key lines, then details only if asked):

```
[Filename] — 100% listo. ✅

[N] libros · [N] unidades · [precio range] · [N]% con ISBN · 0 errores.

Distribución de idiomas: [top 3 with percentages].

[Optional: 1-line note on any anomaly worth flagging — outlier price, 
missing ISBNs, very high quantity in one row]

Subir en https://www.iberlibro.com/servlet/UploadBooks. 
Email de confirmación esperado: [N] añadidos, 0 rechazados.
```

Avoid the "wall of stats" anti-pattern. The user has done this dozens of times; they want the verdict, the headline numbers, and the anomalies — not a verbose recap of every check that passed.

## Edge cases to handle without prompting

| Edge case | Action |
|---|---|
| Input CSV has BOM | `utf-8-sig` strips it on read; output is BOM-free regardless |
| Input has CRLF | The cleaner replaces all `\r` with space before writing |
| Price formatted as `49,90` (comma decimal) | Currently fails the float cast — flag it to the user, don't silently fix; locale conventions vary |
| Quantity is `1.0` | Cast through `int(float(...))` — handled |
| `description` field is empty | Required field; the verification step will flag it. Don't synthesize content — ask the user |
| Filename contains spaces or special chars | Use the path as-is; don't rename. Output filename should mirror input date if present (e.g., `iberlibro_2026-02-05.csv` → `Iberlibro_2026-02-05.txt`) |
| Books without ISBN | Iberlibro accepts these but rejects more often. If any rows lack ISBN, mention it in the verdict and offer to produce an ISBN-only version on request — do not produce one preemptively |

## What success looks like

A 30-second turn that produces:
1. A TXT file in `/mnt/user-data/outputs/` named after the date in the input CSV
2. A 4-line verdict ending in "Subir en [URL]"
3. Zero unsolicited stats, zero re-explanation of the format

If the user asks "por qué" something was done a particular way, *then* explain. Until then, deliver the result.
