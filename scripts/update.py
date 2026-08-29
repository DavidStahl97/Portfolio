"""Kompletter Lauf: Factsheet laden -> parsen -> prüfen -> für die App exportieren.

    python scripts/update.py
    python scripts/update.py --pdf data/factsheets/GDPWLDS_20260731.pdf

Hier wird nichts gewichtet und nichts optimiert. Was entsteht, sind die Rohdaten des
Factsheets und das Protokoll ihrer Prüfung; die Mischung des Portfolios stellt die App
ein.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_data
import fetch_factsheet
import parse_factsheet

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issue", default=fetch_factsheet.DEFAULT_ISSUE)
    ap.add_argument("--pdf", type=Path, default=None,
                    help="Lokales PDF verwenden statt Download")
    ap.add_argument("--no-export", action="store_true",
                    help="Daten für die App nicht exportieren")
    args = ap.parse_args()

    if args.pdf:
        source: bytes | Path = args.pdf
        print(f"1/3 lokales PDF: {args.pdf}")
    else:
        print("1/3 Factsheet laden ...")
        data = fetch_factsheet.fetch(args.issue)
        as_of = parse_factsheet.extract_as_of_date(data)
        pdf_path = REPO / "data" / "factsheets" / f"{args.issue}_{as_of:%Y%m%d}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(data)
        print(f"    {pdf_path.relative_to(REPO)} ({len(data)} Bytes)")
        source = pdf_path

    print("2/3 parsen und prüfen ...")
    fs = parse_factsheet.parse(source)
    csv_path = REPO / "data" / f"ftse_country_weights_{fs.as_of:%Y%m%d}.csv"
    parse_factsheet.write_csv(fs, csv_path)
    parse_factsheet.write_meta(fs, parse_factsheet.meta_path(csv_path))
    parse_factsheet.print_report(fs)
    print(f"    {csv_path.relative_to(REPO)}")

    if not fs.ok:
        print("\nABBRUCH: Prüfungen fehlgeschlagen, Daten nicht für die App exportiert.")
        return 1

    if args.no_export:
        return 0

    # Die App wird aus data/ gebaut - der Export ist der letzte Schritt jedes Laufs,
    # damit `npm run dev` sofort den neuen Stichtag zeigt.
    print("3/3 Daten für die App exportieren ...")
    return export_data.main([])


if __name__ == "__main__":
    raise SystemExit(main())
