"""Schreibt aus den versionierten Rohdaten das, woraus die App gebaut wird.

    python scripts/export_data.py --out web/static

Hier wird nur umgeformt, nicht gerechnet: die Gewichtung des Portfolios entsteht in
der App. Markup, Stylesheet und Skript entstehen hier ohnehin nicht.
Alles unter `web/static/data/` ist Datei für Datei das, was `web/src/lib/types.ts`
beschreibt – die andere Seite desselben Vertrags, und sie muss mitgezogen werden, wenn
sich hier ein Feldname ändert.

Quelle sind die versionierten `ftse_country_weights_<date>.csv` samt `run_<date>.json`.
Das Factsheet-PDF wird nicht gebraucht, deshalb lässt sich die komplette Historie
jederzeit neu exportieren.
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=REPO / "web" / "static")
    args = ap.parse_args(argv)

    runs = []
    for path in sorted(DATA.glob("ftse_country_weights_*.csv")):
        if not parse_factsheet.meta_path(path).exists():
            print(f"übersprungen (kein run_*.json): {path.name}")
            continue
        runs.append(parse_factsheet.load_run(path))
    if not runs:
        raise SystemExit(
            "Keine auswertbaren Stichtage in data/ - erst `python scripts/update.py` laufen lassen."
        )

    runs.sort(key=lambda fs: fs.as_of, reverse=True)      # neuester zuerst
    out = args.out / "data"
    out.mkdir(parents=True, exist_ok=True)

    for fs in runs:
        stamp = f"{fs.as_of:%Y%m%d}"
        (out / f"{stamp}.json").write_text(
            json.dumps(report_payload(fs), ensure_ascii=False) + "\n", encoding="utf-8"
        )

    index = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "stichtage": [
            {"asOf": fs.as_of.isoformat(), "ok": fs.ok, "countries": len(fs.rows)}
            for fs in runs
        ],
    }
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n",
                                    encoding="utf-8")

    # Die CSVs wandern unveraendert mit: die Seite ist zugleich der Datenabruf.
    csvs = args.out / "csv"
    csvs.mkdir(parents=True, exist_ok=True)
    for src in sorted(DATA.glob("*.csv")):
        (csvs / src.name).write_bytes(src.read_bytes())

    print(f"{len(runs)} Stichtag(e) nach {out} exportiert, "
          f"neuester {runs[0].as_of:%d.%m.%Y}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
