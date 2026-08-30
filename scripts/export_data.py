"""Writes what the app is built from, out of the versioned raw data.

    python scripts/export_data.py --out web/static

This only reshapes, it does not compute: the portfolio weighting happens in the app.
Markup, stylesheet and script are not produced here either.
Everything under `web/static/data/` is, file by file, what `web/src/lib/types.ts`
describes - the other side of the same contract, and it has to be changed along
whenever a field name changes here.

The sources are the versioned `ftse_country_weights_<date>.csv` files together with
their `run_<date>.json`, plus `regions.json` for the grouping into the five regional
indices. The factsheet PDF is not needed, so the whole history can be re-exported at
any time.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parse_factsheet

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
REGIONS_JSON = DATA / "regions.json"


def report_payload(fs) -> dict:
    return {
        "asOf": fs.as_of.isoformat(),
        "ok": fs.ok,
        "totals": {
            "consGdp": fs.totals.cons_gdp,
            "consMcap": fs.totals.cons_mc,
            "netGdp": fs.totals.mcap_gdp,
            "netMcap": fs.totals.mcap_mc,
        },
        "checks": [{"name": n, "passed": p, "detail": d} for n, p, d in fs.checks],
        "countries": [
            {
                "country": r.country,
                "mcap": r.wgt_mc,
                "gdp": r.wgt_gdp,
                "consMcap": r.cons_mc,
                "consGdp": r.cons_gdp,
                "netMcap": r.mcap_mc,
                "netGdp": r.mcap_gdp,
            }
            for r in sorted(fs.rows, key=lambda r: r.country)
        ],
    }


def regions_payload() -> dict:
    """The grouping into the five regional indices, as the app needs it.

    Reshaped, not decided: which country is in which index was read out of the five
    factsheets and is checked against them by check_sources.py. The countries of the
    All-World that are in none of the five stay unlisted - the app shows them as their
    own slice rather than silently dropping them.
    """
    stored = json.loads(REGIONS_JSON.read_text(encoding="utf-8"))
    return {
        "readFrom": stored["read_from"],
        "regions": [
            {
                "issue": r["issue"],
                "index": r["index"],
                "etf": r["etf"],
                "countries": sorted(r["countries"]),
            }
            for r in stored["regions"]
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=REPO / "web" / "static")
    args = ap.parse_args(argv)

    runs = []
    for path in sorted(DATA.glob("ftse_country_weights_*.csv")):
        if not parse_factsheet.meta_path(path).exists():
            print(f"skipped (no run_*.json): {path.name}")
            continue
        runs.append(parse_factsheet.load_run(path))
    if not runs:
        raise SystemExit(
            "No usable as-of dates in data/ - run `python scripts/update.py` first."
        )

    runs.sort(key=lambda fs: fs.as_of, reverse=True)      # newest first
    out = args.out / "data"
    out.mkdir(parents=True, exist_ok=True)

    for fs in runs:
        stamp = f"{fs.as_of:%Y%m%d}"
        (out / f"{stamp}.json").write_text(
            json.dumps(report_payload(fs), ensure_ascii=False) + "\n", encoding="utf-8"
        )

    (out / "regions.json").write_text(
        json.dumps(regions_payload(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    index = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "dates": [
            {"asOf": fs.as_of.isoformat(), "ok": fs.ok, "countries": len(fs.rows)}
            for fs in runs
        ],
    }
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")

    # The CSVs are copied over unchanged: the site is also the data download.
    csvs = args.out / "csv"
    csvs.mkdir(parents=True, exist_ok=True)
    for src in sorted(DATA.glob("*.csv")):
        (csvs / src.name).write_bytes(src.read_bytes())

    print(f"exported {len(runs)} as-of date(s) to {out}, "
          f"newest {runs[0].as_of:%Y-%m-%d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
