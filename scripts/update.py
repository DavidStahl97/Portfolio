"""Full run: download the factsheet -> parse -> check -> export for the app.

    python scripts/update.py
    python scripts/update.py --pdf data/factsheets/GDPWLDS_20260731.pdf

Nothing is weighted and nothing is optimised here. What comes out are the raw data of
the factsheet and the record of their checks; the portfolio mix is set in the app.

Alongside the blended factsheet the run also fetches the five regional factsheets -
the indices behind the five Vanguard ETFs. They are not parsed yet and nothing is
versioned from them; they are downloaded so the regional split can be read off FTSE's
own documents instead of a mapping kept by hand.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_data
import fetch_factsheet
import indices
import parse_factsheet

REPO = Path(__file__).resolve().parent.parent


def fetch_regions(as_of: dt.date) -> bool:
    """Downloads the five regional factsheets and reports whether they fit.

    A regional factsheet is a side dataset: it may not hold the country data of the
    run hostage. So a problem here is reported and returned, not raised - the export
    has already happened by the time this runs.
    """
    ok = True
    for index in indices.REGIONS:
        print(f"    {index.issue:9s} {index.label}")
        try:
            _, region_as_of = fetch_factsheet.fetch_index(index)
        except Exception as exc:  # network, wrong issue name, unreadable PDF
            print(f"    [WARN] {index.issue}: {exc}")
            ok = False
            continue
        if region_as_of != as_of:
            print(f"    [WARN] {index.issue}: as-of date {region_as_of:%Y-%m-%d} "
                  f"instead of {as_of:%Y-%m-%d} - the issues are out of step.")
            ok = False
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issue", default=fetch_factsheet.DEFAULT_ISSUE)
    ap.add_argument("--pdf", type=Path, default=None,
                    help="use a local PDF instead of downloading one")
    ap.add_argument("--no-export", action="store_true",
                    help="do not export the data for the app")
    ap.add_argument("--no-regions", action="store_true",
                    help="do not fetch the five regional factsheets")
    args = ap.parse_args()

    if args.pdf:
        source: bytes | Path = args.pdf
        print(f"1/4 local PDF: {args.pdf}")
    else:
        print("1/4 downloading the factsheet ...")
        index = indices.get(args.issue)
        pdf_path, _ = fetch_factsheet.fetch_index(index)
        source = pdf_path

    print("2/4 parsing and checking ...")
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
        print("3/4 export skipped.")
    else:
        # The app is built from data/ - the export is the last step that touches the
        # data, so that `npm run dev` shows the new as-of date right away.
        print("3/4 exporting the data for the app ...")
        if export_data.main([]) != 0:
            return 1

    # --pdf is the way to run without a network; fetching the regions would defeat it.
    if args.no_regions or args.pdf:
        print("4/4 regional factsheets skipped.")
        return 0

    print("4/4 fetching the regional factsheets ...")
    if not fetch_regions(fs.as_of):
        print("    The country data of this run are unaffected by the above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
