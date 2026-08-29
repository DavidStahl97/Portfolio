"""Baut die GitHub-Pages-Seite: alle Stichtage, nicht nur der aktuelle.

    python scripts/build_site.py --out site

Die Reports werden bei jedem Lauf aus den versionierten Daten neu erzeugt
(`ftse_country_weights_<date>.csv` + `run_<date>.json`) - das PDF wird dafür
nicht gebraucht. Damit wächst die Historie auf der Seite automatisch mit, ohne
dass generiertes HTML im Repo liegen muss.

Ergebnis:
    site/index.html            neuester Report
    site/reports/<date>.html   je Stichtag
    site/data/                 CSVs und Prüfprotokolle zum Direktabruf
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parse_factsheet
import render_report

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


def targets(fs, split: float) -> dict[str, float]:
    blended = {r.country: split * r.wgt_mc + (1 - split) * r.wgt_gdp for r in fs.rows}
    total = sum(blended.values())
    return {c: 100.0 * w / total for c, w in blended.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=REPO / "site")
    ap.add_argument("--split", type=float, default=0.5,
                    help="Fallback, falls run_<date>.json keinen Split enthält")
    args = ap.parse_args()

    csvs = sorted(DATA.glob("ftse_country_weights_*.csv"))
    runs = []
    for path in csvs:
        if not parse_factsheet.meta_path(path).exists():
            print(f"übersprungen (kein run_*.json): {path.name}")
            continue
        fs, split = parse_factsheet.load_run(path)
        runs.append((fs, split if split is not None else args.split))
    if not runs:
        raise SystemExit("Keine auswertbaren Stichtage in data/ gefunden.")

    runs.sort(key=lambda r: r[0].as_of)                  # alt -> neu
    order = list(reversed(runs))                         # Navigation: neu -> alt
    labels = [(f"{fs.as_of:%m/%Y}", f"{fs.as_of:%Y%m%d}") for fs, _ in order]

    out = args.out
    if out.exists():
        shutil.rmtree(out)
    (out / "reports").mkdir(parents=True)
    (out / "data").mkdir()

    for src in sorted(DATA.glob("*.csv")) + sorted(DATA.glob("run_*.json")):
        shutil.copy2(src, out / "data" / src.name)

    prev_targets: dict[str, float] = {}
    pages: dict[str, str] = {}
    for fs, split in runs:                               # chronologisch, für Δ
        nav = [(lab, f"{stamp}.html", stamp == f"{fs.as_of:%Y%m%d}")
               for lab, stamp in labels]
        pages[f"{fs.as_of:%Y%m%d}"] = render_report.build(
            fs, split, prev_targets, nav=nav, data_prefix="../data/")
        prev_targets = targets(fs, split)

    for stamp, html in pages.items():
        (out / "reports" / f"{stamp}.html").write_text(html, encoding="utf-8")

    # Startseite: derselbe Report wie der neueste, nur mit Pfaden ab Wurzel
    newest, newest_split = runs[-1]
    prev = targets(*runs[-2]) if len(runs) > 1 else {}
    nav = [(lab, f"reports/{stamp}.html", stamp == f"{newest.as_of:%Y%m%d}")
           for lab, stamp in labels]
    (out / "index.html").write_text(
        render_report.build(newest, newest_split, prev, nav=nav, data_prefix="data/"),
        encoding="utf-8")

    print(f"Seite in {out}: {len(runs)} Stichtag(e), neuester {newest.as_of:%d.%m.%Y}")
    for fs, split in order:
        print(f"  reports/{fs.as_of:%Y%m%d}.html  (Split {split:.0%} MCap)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
