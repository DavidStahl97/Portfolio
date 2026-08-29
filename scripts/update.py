"""Full run: download the factsheet -> parse -> check -> export for the app.

    python scripts/update.py
    python scripts/update.py --pdf data/factsheets/GDPWLDS_20260731.pdf

Nothing is weighted and nothing is optimised here. What comes out are the raw data of
the factsheet and the record of their checks; the portfolio mix is set in the app.
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
                    help="use a local PDF instead of downloading one")
    ap.add_argument("--no-export", action="store_true",
                    help="do not export the data for the app")
    args = ap.parse_args()

    if args.pdf:
        source: bytes | Path = args.pdf
        print(f"1/3 local PDF: {args.pdf}")
    else:
        print("1/3 downloading the factsheet ...")
        data = fetch_factsheet.fetch(args.issue)
        as_of = parse_factsheet.extract_as_of_date(data)
        pdf_path = REPO / "data" / "factsheets" / f"{args.issue}_{as_of:%Y%m%d}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(data)
        print(f"    {pdf_path.relative_to(REPO)} ({len(data)} bytes)")
        source = pdf_path

    print("2/3 parsing and checking ...")
    fs = parse_factsheet.parse(source)
    csv_path = REPO / "data" / f"ftse_country_weights_{fs.as_of:%Y%m%d}.csv"
    parse_factsheet.write_csv(fs, csv_path)
    parse_factsheet.write_meta(fs, parse_factsheet.meta_path(csv_path))
    parse_factsheet.print_report(fs)
    print(f"    {csv_path.relative_to(REPO)}")

    if not fs.ok:
        print("\nABORTED: checks failed, no data exported for the app.")
        return 1

    if args.no_export:
        return 0

    # The app is built from data/ - the export is the last step of every run, so that
    # `npm run dev` shows the new as-of date right away.
    print("3/3 exporting the data for the app ...")
    return export_data.main([])


if __name__ == "__main__":
    raise SystemExit(main())
