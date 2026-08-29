"""Kompletter Lauf: Factsheet laden -> parsen -> pruefen -> Zielgewichte bauen.

    python scripts/update.py            # 50/50
    python scripts/update.py --split 0.6
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_factsheet
import parse_factsheet

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issue", default=fetch_factsheet.DEFAULT_ISSUE)
    ap.add_argument("--split", type=float, default=0.5)
    ap.add_argument("--pdf", type=Path, default=None,
                    help="Lokales PDF verwenden statt Download")
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

    print("2/3 parsen und pruefen ...")
    fs = parse_factsheet.parse(source)
    csv_path = REPO / "data" / f"ftse_country_weights_{fs.as_of:%Y%m%d}.csv"
    parse_factsheet.write_csv(fs, csv_path)
    parse_factsheet.print_report(fs)
    if not fs.ok:
        print("\nABBRUCH: Pruefungen fehlgeschlagen, keine Zielgewichte erzeugt.")
        return 1
    print(f"    {csv_path.relative_to(REPO)}")

    print("3/3 Zielgewichte berechnen ...")
    return subprocess.call([
        sys.executable, str(Path(__file__).with_name("build_portfolio.py")),
        "--csv", str(csv_path), "--split", str(args.split),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
