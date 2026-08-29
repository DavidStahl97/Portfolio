"""Berechnet die Zielgewichte des 50/50-Portfolios (Marktkapitalisierung/BIP).

Gewicht_Land = split * Marktkap.-Gewicht + (1 - split) * BIP-Gewicht

Ausgabe: data/target_weights_<YYYYMMDD>.csv, absteigend sortiert, inkl.
Kumulativspalte und - falls eine Vorperiode existiert - der Veraenderung
gegenueber dem letzten Lauf.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


def read_weights(path: Path) -> tuple[dt.date, dict[str, tuple[float, float]]]:
    with path.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    as_of = dt.date.fromisoformat(rows[0]["as_of"])
    return as_of, {
        r["country"]: (float(r["weight_mcap_pct"]), float(r["weight_gdp_pct"]))
        for r in rows
    }


def latest_country_csv() -> Path:
    files = sorted(DATA.glob("ftse_country_weights_*.csv"))
    if not files:
        raise SystemExit("Keine data/ftse_country_weights_*.csv gefunden - erst update.py laufen lassen.")
    return files[-1]


def previous_targets(exclude: Path) -> dict[str, float]:
    files = [f for f in sorted(DATA.glob("target_weights_*.csv")) if f != exclude]
    if not files:
        return {}
    with files[-1].open(encoding="utf-8") as fh:
        return {r["country"]: float(r["target_weight_pct"]) for r in csv.DictReader(fh)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, default=None, help="Laender-CSV aus parse_factsheet.py")
    ap.add_argument("--split", type=float, default=0.5,
                    help="Anteil Marktkapitalisierung (0.5 = 50/50, Default)")
    ap.add_argument("--min-weight", type=float, default=0.0,
                    help="Laender unter diesem Zielgewicht (%%) ausblenden und Rest normieren")
    args = ap.parse_args()

    if not 0.0 <= args.split <= 1.0:
        raise SystemExit("--split muss zwischen 0 und 1 liegen.")

    src = args.csv or latest_country_csv()
    as_of, weights = read_weights(src)

    blended = {
        c: args.split * mc + (1 - args.split) * gdp for c, (mc, gdp) in weights.items()
    }
    if args.min_weight > 0:
        blended = {c: w for c, w in blended.items() if w >= args.min_weight}
    total = sum(blended.values())
    if total <= 0:
        raise SystemExit("Summe der Gewichte ist 0 - Eingabedaten pruefen.")
    normed = {c: 100.0 * w / total for c, w in blended.items()}

    prev = None
    out = DATA / f"target_weights_{as_of:%Y%m%d}.csv"
    prev_map = previous_targets(exclude=out)

    ordered = sorted(normed.items(), key=lambda kv: -kv[1])
    cum = 0.0
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["as_of", "country", "weight_mcap_pct", "weight_gdp_pct",
                    "target_weight_pct", "cumulative_pct", "delta_vs_prev_pp"])
        for country, tw in ordered:
            cum += tw
            mc, gdp = weights[country]
            prev = prev_map.get(country)
            delta = "" if prev is None else f"{tw - prev:+.2f}"
            w.writerow([as_of.isoformat(), country, f"{mc:.2f}", f"{gdp:.2f}",
                        f"{tw:.2f}", f"{cum:.2f}", delta])

    print(f"Quelle: {src.name} | Stichtag {as_of:%d.%m.%Y} | "
          f"Split {args.split:.0%} MCap / {1 - args.split:.0%} BIP")
    print(f"Summe Zielgewichte: {sum(normed.values()):.2f}% ueber {len(normed)} Laender")
    print("\nTop 15:")
    print(f"  {'Land':<16}{'MCap%':>8}{'BIP%':>8}{'Ziel%':>8}{'Kum%':>8}")
    cum = 0.0
    for country, tw in ordered[:15]:
        cum += tw
        mc, gdp = weights[country]
        print(f"  {country:<16}{mc:>8.2f}{gdp:>8.2f}{tw:>8.2f}{cum:>8.2f}")
    print(f"\nCSV: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
