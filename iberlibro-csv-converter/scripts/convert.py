#!/usr/bin/env python3
"""
Iberlibro / AbeBooks CSV → TXT converter.

Reads a bookseller CSV, cleans it, writes a tab-delimited TXT in the strict
format the marketplace expects, and verifies the output by re-reading it.

Usage:
    python convert.py <input.csv> <output.txt>

Exit codes:
    0  → output is 100% correct, ready for upload
    1  → input is missing required fields or unreadable
    2  → output failed verification (this should never happen — bug)
"""

import csv
import sys
from collections import Counter
from pathlib import Path

# ── Canonical 30-field schema. Order is mandatory. ──────────
FIELDS = [
    'listingid', 'title', 'author', 'illustrator', 'price', 'quantity',
    'producttype', 'description', 'bindingtext', 'bookcondition',
    'publishername', 'placepublished', 'yearpublished', 'isbn',
    'sellercatalog1', 'sellercatalog2', 'sellercatalog3', 'abecategory',
    'keywords', 'jacketcondition', 'editiontext', 'printingtext',
    'signedtext', 'volume', 'size', 'imgurl', 'weight', 'weightunit',
    'shippingtemplateid', 'language',
]

REQUIRED_NON_EMPTY = ['title', 'description']  # ISBN handled separately
CONTROL_CHARS = ('\n', '\r', '\t')


def clean_cell(value: str) -> str:
    """Strip control chars and collapse whitespace. Empty string if None."""
    if not value:
        return ''
    for ch in CONTROL_CHARS:
        value = value.replace(ch, ' ')
    return ' '.join(value.split())


def normalize_price(value: str) -> str:
    """`49.9` → `49.90`. Leaves invalid input untouched (caller will flag it)."""
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return value


def normalize_quantity(value: str) -> str:
    """`1.0` → `1`. Leaves invalid input untouched."""
    try:
        return str(int(float(value)))
    except (ValueError, TypeError):
        return value


def read_input(path: Path) -> tuple[list[dict], list[str]]:
    """Read CSV with BOM-tolerant encoding. Returns (rows, fieldnames)."""
    with path.open('r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def check_schema(fieldnames: list[str]) -> list[str]:
    """Return list of missing required fields (empty list = OK)."""
    return [f for f in FIELDS if f not in fieldnames]


def transform(rows: list[dict]) -> tuple[list[dict], int]:
    """Clean and normalize every row. Returns (rows, cells_modified_count)."""
    modified = 0
    for r in rows:
        for k in list(r.keys()):
            original = r[k] or ''
            cleaned = clean_cell(original)
            if cleaned != original:
                modified += 1
            r[k] = cleaned
        r['price'] = normalize_price(r.get('price', ''))
        r['quantity'] = normalize_quantity(r.get('quantity', ''))
    return rows, modified


def write_output(path: Path, rows: list[dict]) -> None:
    """Write TXT: UTF-8 no BOM, LF endings, TAB delimiter, exact field order."""
    lines = ['\t'.join(FIELDS)]
    for r in rows:
        lines.append('\t'.join(r.get(f, '') for f in FIELDS))
    # newline='' prevents Python from converting \n to \r\n on Windows
    with path.open('w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(lines))


def verify_output(path: Path) -> dict:
    """Re-read the written file and run all checks. Returns a report dict."""
    raw = path.read_bytes()
    has_bom = raw[:3] == b'\xef\xbb\xbf'
    has_crlf = b'\r\n' in raw

    with path.open('r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))

    n = len(rows)

    def count_with(fn) -> int:
        return sum(1 for r in rows if fn(r))

    n_newline = sum(1 for r in rows for v in r.values() if v and '\n' in v)
    n_tab = sum(1 for r in rows for v in r.values() if v and '\t' in v)
    n_cr = sum(1 for r in rows for v in r.values() if v and '\r' in v)

    titles = count_with(lambda r: bool(r.get('title', '').strip()))
    isbns = count_with(lambda r: bool(r.get('isbn', '').strip()))
    descs = count_with(lambda r: bool(r.get('description', '').strip()))

    def safe_float(v: str) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

    def safe_int(v: str) -> int:
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    prices_ok = count_with(lambda r: safe_float(r.get('price', '')) > 0)
    qty_ok = count_with(lambda r: safe_int(r.get('quantity', '')) > 0)

    prices = [safe_float(r.get('price', '')) for r in rows]
    qtys = [safe_int(r.get('quantity', '')) for r in rows]
    langs = Counter(r.get('language', '') for r in rows)

    return {
        'n': n,
        'size_bytes': len(raw),
        'has_bom': has_bom,
        'has_crlf': has_crlf,
        'n_newline': n_newline,
        'n_tab': n_tab,
        'n_cr': n_cr,
        'titles': titles,
        'isbns': isbns,
        'descs': descs,
        'prices_ok': prices_ok,
        'qty_ok': qty_ok,
        'prices': prices,
        'qtys': qtys,
        'langs': langs,
        'rows': rows,
    }


def all_checks_pass(report: dict) -> bool:
    n = report['n']
    return (
        not report['has_bom'] and not report['has_crlf']
        and report['n_newline'] == 0 and report['n_tab'] == 0 and report['n_cr'] == 0
        and report['titles'] == n and report['isbns'] == n
        and report['prices_ok'] == n and report['qty_ok'] == n
        and report['descs'] == n
    )


def print_report(report: dict, output_path: Path, cells_modified: int) -> None:
    n = report['n']
    prices = report['prices']
    qtys = report['qtys']
    langs = report['langs']

    print("╔═══════════════════════════════════════════════════════════╗")
    print(f"║   {output_path.name:^53}   ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")

    print("── ARCHIVO ──────────────────────────────────────────────")
    print(f"  Tamaño     : {report['size_bytes']:,} bytes ({report['size_bytes']/1024:.1f} KB)")
    print(f"  Encoding   : UTF-8 {'❌ BOM presente' if report['has_bom'] else '✅ sin BOM'}")
    print(f"  Endings    : {'❌ CRLF' if report['has_crlf'] else '✅ LF (Unix)'}")
    print(f"  Delimitador: TAB ✅")
    print(f"  Campos     : 30 ✅")

    print("\n── DATOS ────────────────────────────────────────────────")
    print(f"  Libros   : {n}")
    print(f"  Unidades : {sum(qtys)}")
    print(f"  Celdas limpiadas: {cells_modified}")

    print("\n── CAMPOS OBLIGATORIOS ──────────────────────────────────")
    for label, val in [('Título', report['titles']), ('ISBN', report['isbns']),
                       ('Precio>0', report['prices_ok']), ('Cantidad>0', report['qty_ok']),
                       ('Descripción', report['descs'])]:
        ok = '✅' if val == n else '⚠️ '
        print(f"  {ok} {label}: {val}/{n}")

    print("\n── CARACTERES PROBLEMÁTICOS ─────────────────────────────")
    for label, val in [('Newlines', report['n_newline']),
                       ('Tabs', report['n_tab']),
                       ('CR', report['n_cr'])]:
        ok = '✅' if val == 0 else '❌'
        print(f"  {ok} {label} en datos: {val}")

    if prices:
        print("\n── PRECIOS ──────────────────────────────────────────────")
        print(f"  Promedio   : {sum(prices)/len(prices):.2f} EUR")
        print(f"  Mín / Máx  : {min(prices):.2f} / {max(prices):.2f} EUR")
        print(f"  Valor total: {sum(prices):,.2f} EUR")

    print("\n── IDIOMAS ──────────────────────────────────────────────")
    for lang, cnt in langs.most_common():
        print(f"  {lang or '(sin idioma)'}: {cnt} ({cnt/n*100:.1f}%)")

    print("\n╔═══════════════════════════════════════════════════════════╗")
    if all_checks_pass(report):
        print("║  ✅  ARCHIVO 100 % CORRECTO  ·  LISTO PARA IBERLIBRO    ║")
    else:
        print("║  ❌  HAY PROBLEMAS — REVISAR ANTES DE SUBIR             ║")
    print("╚═══════════════════════════════════════════════════════════╝")


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python convert.py <input.csv> <output.txt>", file=sys.stderr)
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}", file=sys.stderr)
        return 1

    rows, fieldnames = read_input(input_path)

    missing = check_schema(fieldnames)
    if missing:
        print(f"❌ Missing required fields: {missing}", file=sys.stderr)
        return 1

    rows, cells_modified = transform(rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_output(output_path, rows)

    report = verify_output(output_path)
    print_report(report, output_path, cells_modified)

    return 0 if all_checks_pass(report) else 2


if __name__ == '__main__':
    sys.exit(main())
