"""Full run: download the factsheet -> parse -> check -> export for the app.

    python scripts/update.py
    python scripts/update.py --pdf data/factsheets/GDPWLDS_20260731.pdf

Nothing is weighted and nothing is optimised here. What comes out are the raw data of
the factsheet and the record of their checks; the portfolio mix is set in the app.

Alongside the blended factsheet the run also fetches the five regional factsheets -
the indices behind the five Vanguard ETFs - and writes each country table to its own
versioned CSV, so the regional split is read off FTSE's own documents instead of a
mapping kept by hand. One of the five, FTSE Japan, has no country table; indices.py
names its country.
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
    """Downloads the five regional factsheets, reads them, writes one CSV each.

    A regional factsheet is a side dataset: it may not hold the country data of the
    run hostage. So a problem here is reported and returned, not raised.

    FTSE Japan gets no CSV - a single-country index has nothing to break down and its
    factsheet has no country table. It is named in indices.py instead, and that is the
    one place in this project where a country list is not read out of a document.

    The tally line always starts with `regions:` - that is what data.yml pulls out of
    the log to put into the pull request, so a run that is only read as a pull request
    says on its own whether the region view will be there. Nothing is computed in it,
    it counts the files just written.
    """
    ok = True
    written: list[str] = []   # issues whose country table became a CSV
    named: list[str] = []     # issues without a country table, covered by indices.py
    missing: list[str] = []   # issues this run has no CSV from at all
    suspect: list[str] = []   # CSV written, but its own checks did not pass
    for index in indices.REGIONS:
        print(f"    {index.issue:9s} {index.label}")
        try:
            pdf, region_as_of = fetch_factsheet.fetch_index(index)
        except Exception as exc:  # network, wrong issue name, unreadable PDF
            print(f"    [WARN] {index.issue}: {exc}")
            missing.append(index.issue)
            ok = False
            continue

        if region_as_of != as_of:
            print(f"    [WARN] {index.issue}: as-of date {region_as_of:%Y-%m-%d} "
                  f"instead of {as_of:%Y-%m-%d} - the issues are out of step.")
            missing.append(index.issue)
            ok = False
            continue

        if index.covers:
            print(f"    {'':9s} no country table (single-country index), "
                  f"covers: {', '.join(index.covers)}")
            named.append(index.issue)
            continue

        try:
            region = parse_factsheet.parse_region(pdf, index.issue, index.title)
        except Exception as exc:
            print(f"    [WARN] {index.issue}: {exc}")
            missing.append(index.issue)
            ok = False
            continue

        csv_path = parse_factsheet.region_csv_path(region, REPO / "data")
        parse_factsheet.write_region_csv(region, csv_path)
        print(f"    {'':9s} {csv_path.relative_to(REPO)} - {len(region.rows)} "
              f"countries, {region.currency}")
        if not region.ok:
            for name, passed, detail in region.checks:
                if not passed:
                    print(f"    [WARN] {index.issue}: {name}: {detail}")
            suspect.append(index.issue)
            ok = False
        written.append(index.issue)

    total = len(indices.REGIONS)
    tally = (f"regions: {len(written) + len(named)}/{total} read, "
             f"{len(written)} CSVs written")
    if named:
        tally += f", {', '.join(named)} covered by name"
    if suspect:
        tally += f", checks failed: {', '.join(suspect)}"
    if missing:
        # export_data.py builds regions.json all or nothing, so a single missing
        # region costs the region view entirely. That belongs in the tally, not only
        # in the warnings above it.
        tally += (f", missing: {', '.join(missing)}"
                  " - the site shows no region view")
    print(f"    {tally}")
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

    # Before the export: the region CSVs written here are what the export groups by.
    # --pdf is the way to run without a network; fetching the regions would defeat it.
    if args.no_regions or args.pdf:
        print("3/4 regional factsheets skipped.")
        print("    regions: skipped - the region CSVs of this as-of date are "
              "whatever the repository already holds")
    else:
        print("3/4 fetching and reading the regional factsheets ...")
        if not fetch_regions(fs.as_of):
            print("    The country data of this run are unaffected by the above.")

    if args.no_export:
        print("4/4 export skipped.")
        return 0

    # The app is built from data/ - the export is the last step that touches the data,
    # so that `npm run dev` shows the new as-of date right away.
    print("4/4 exporting the data for the app ...")
    return export_data.main([])


if __name__ == "__main__":
    raise SystemExit(main())
