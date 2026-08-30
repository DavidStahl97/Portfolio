"""Downloads every registered issue and checks that it can still be read.

    python scripts/check_sources.py

This is the smoke test of the fetch layer. It needs a network and writes nothing into
`data/` except the throwaway PDFs, so it can be run whenever the question is "do the
factsheets still arrive and does the parser still recognise them".

Three things are checked, in this order:

1. every issue in `indices.py` downloads and names the index we asked for,
2. every regional factsheet parses, with the same checks as the blend,
3. `data/regions.json` still says what the factsheets say, and the five regions cover
   the countries of the blend - each country in exactly one region, with the gaps and
   any overlaps named.

Point 3 is the one worth having. `data/regions.json` is what the app groups countries
by, and it is a list: without this check it would quietly go stale the first time FTSE
moves a country, which happens with every reclassification - Greece moves from Emerging
to Developed Europe in September 2026. The list is written by hand once and proved
right here, against FTSE's own documents, on every run. Nothing is weighted here; what
comes out is a report.

On a parse failure the lines of the country table are dumped, because a layout change
is the likely cause and the lines are what you need to see to fix the pattern.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_factsheet
import indices
import parse_factsheet

REPO = Path(__file__).resolve().parent.parent
REGIONS_JSON = REPO / "data" / "regions.json"
DUMP_LINES = 60


def _report(checks: list[tuple[str, bool, str]], indent: str = "    ") -> None:
    for name, passed, detail in checks:
        print(f"{indent}[{'OK  ' if passed else 'FAIL'}] {name}: {detail}")


def _dump(pdf: Path) -> None:
    """The country table as the parser sees it - the evidence for a layout change."""
    print(f"    --- {parse_factsheet.BREAKDOWN}, as extracted ---")
    try:
        page = parse_factsheet.breakdown_page(parse_factsheet.pages_text(pdf))
    except Exception as exc:
        print(f"    (no such page: {exc})")
        return
    for line in page.splitlines()[:DUMP_LINES]:
        print(f"    | {line}")
    print("    --- end ---")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep-going", action="store_true",
                    help="report everything instead of stopping at the blend")
    args = ap.parse_args()

    failed: list[str] = []

    print(f"{indices.BLEND.issue}: {indices.BLEND.label}")
    try:
        blend_pdf, _ = fetch_factsheet.fetch_index(indices.BLEND)
        blend = parse_factsheet.parse(blend_pdf)
    except Exception as exc:
        print(f"    [FAIL] {exc}")
        if not args.keep_going:
            return 1
        blend = None
    else:
        print(f"    as-of {blend.as_of:%Y-%m-%d}, {len(blend.rows)} countries")
        _report(blend.checks)
        if not blend.ok:
            failed.append(indices.BLEND.issue)
            _dump(blend_pdf)

    parsed: dict[str, list[str]] = {}
    for index in indices.REGIONS:
        print(f"\n{index.issue}: {index.label}")
        pdf: Path | None = None
        try:
            pdf, as_of = fetch_factsheet.fetch_index(index)
            if index.covers:
                # A single-country index has nothing to break down, so its factsheet
                # has no country table. Fetching and naming it is all there is to do.
                countries = list(index.covers)
                print(f"    as-of {as_of:%Y-%m-%d}, no country table (single-country "
                      f"index), covers: {', '.join(countries)}")
            else:
                region = parse_factsheet.parse_region(pdf, index.issue, index.title)
                countries = region.countries
                print(f"    as-of {as_of:%Y-%m-%d}, {len(countries)} countries: "
                      f"{', '.join(countries)}")
                _report(region.checks)
                if not region.ok:
                    failed.append(index.issue)
                    _dump(pdf)
        except Exception as exc:
            print(f"    [FAIL] {exc}")
            failed.append(index.issue)
            if pdf is not None:
                _dump(pdf)
            continue
        parsed[index.issue] = countries
        if blend and as_of != blend.as_of:
            print(f"    [FAIL] as-of date {as_of:%Y-%m-%d} instead of "
                  f"{blend.as_of:%Y-%m-%d} - the issues are out of step.")
            failed.append(index.issue)

    if len(parsed) == len(indices.REGIONS):
        print("\ndata/regions.json against the factsheets")
        stored = json.loads(REGIONS_JSON.read_text(encoding="utf-8"))
        by_issue = {r["issue"]: r for r in stored["regions"]}
        for issue, countries in parsed.items():
            entry = by_issue.get(issue)
            if entry is None:
                print(f"    [FAIL] {issue}: missing from data/regions.json")
                failed.append("regions.json")
                continue
            gone = sorted(set(entry["countries"]) - set(countries))
            new = sorted(set(countries) - set(entry["countries"]))
            passed = not gone and not new
            detail = "unchanged" if passed else (
                f"no longer in the index: {', '.join(gone) or '-'}; "
                f"newly in it: {', '.join(new) or '-'}")
            print(f"    [{'OK  ' if passed else 'FAIL'}] {issue}: {detail}")
            if not passed:
                failed.append("regions.json")
        for issue in by_issue.keys() - parsed.keys():
            print(f"    [FAIL] {issue}: in data/regions.json but not among the indices")
            failed.append("regions.json")

    if blend and len(parsed) == len(indices.REGIONS):
        print("\nCoverage of the blend by the five regions")
        home: dict[str, list[str]] = {}
        for issue, countries in parsed.items():
            for country in countries:
                home.setdefault(country, []).append(issue)

        blend_countries = {r.country for r in blend.rows}
        uncovered = sorted(blend_countries - home.keys())
        overlapping = sorted(c for c, w in home.items() if len(w) > 1)
        unknown = sorted(home.keys() - blend_countries)

        print(f"    [{'OK  ' if not overlapping else 'FAIL'}] No country in two "
              f"regions: {', '.join(overlapping) or '-'}")
        print(f"    [INFO] In the blend, in no region: {', '.join(uncovered) or '-'}")
        print(f"    [INFO] In a region, not in the blend: {', '.join(unknown) or '-'}")
        if overlapping:
            failed.append("coverage")

    print()
    if failed:
        print(f"FAILED: {', '.join(sorted(set(failed)))}")
        return 1
    print("All factsheets fetched, read and consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
