"""Parst die Länder-Aufstellung aus dem FTSE-Factsheet-PDF in eine CSV.

Das Factsheet enthaelt beide Gewichtungen nebeneinander:
  - FTSE All-World GDP Weighted  -> BIP-Gewicht
  - FTSE All-World               -> Marktkapitalisierungs-Gewicht

Jeder Parse-Lauf wird geprüft (Summe aller Länder vs. Totals-Zeile im PDF);
bei Abweichung ausserhalb der Toleranz endet das Skript mit Exit-Code 1.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

REPO = Path(__file__).resolve().parent.parent

# "Australia 105 1,060,680 1.08 105 1,687,922 1.62"
ROW_RE = re.compile(
    r"^(?P<country>[A-Za-z][A-Za-z .'\-()&/]*?)\s+"
    r"(?P<cons_gdp>\d{1,5})\s+(?P<mcap_gdp>[\d,]+)\s+(?P<wgt_gdp>\d+\.\d{2})\s+"
    r"(?P<cons_mc>\d{1,5})\s+(?P<mcap_mc>[\d,]+)\s+(?P<wgt_mc>\d+\.\d{2})\s*$"
)
DATE_RE = re.compile(r"Data as at:\s*(\d{1,2}\s+\w+\s+\d{4})")

# Toleranzen: die Wgt-Spalten sind auf 2 Nachkommastellen gerundet, d.h. pro
# Land bis zu 0.005 Prozentpunkte Rundungsfehler.
WGT_TOL_PP = 0.5     # Prozentpunkte, Summe Länder vs. 100.00
MCAP_TOL_REL = 1e-6  # relative Abweichung der Net-MCap-Summe


@dataclass
class Row:
    country: str
    cons_gdp: int
    mcap_gdp: int
    wgt_gdp: float
    cons_mc: int
    mcap_mc: int
    wgt_mc: float


@dataclass
class Factsheet:
    as_of: dt.date
    rows: list[Row]
    totals: Row
    checks: list[tuple[str, bool, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(passed for _, passed, _ in self.checks)


def _open(pdf: bytes | Path):
    if isinstance(pdf, (bytes, bytearray)):
        return pdfplumber.open(io.BytesIO(pdf))
    return pdfplumber.open(str(pdf))


def _pages_text(pdf: bytes | Path) -> list[str]:
    with _open(pdf) as doc:
        return [p.extract_text() or "" for p in doc.pages]


def extract_as_of_date(pdf: bytes | Path) -> dt.date:
    for text in _pages_text(pdf):
        m = DATE_RE.search(text)
        if m:
            return dt.datetime.strptime(m.group(1), "%d %B %Y").date()
    raise ValueError("Kein 'Data as at:'-Datum im PDF gefunden.")


def _to_row(m: re.Match) -> Row:
    g = m.groupdict()
    return Row(
        country=g["country"].strip(),
        cons_gdp=int(g["cons_gdp"]),
        mcap_gdp=int(g["mcap_gdp"].replace(",", "")),
        wgt_gdp=float(g["wgt_gdp"]),
        cons_mc=int(g["cons_mc"]),
        mcap_mc=int(g["mcap_mc"].replace(",", "")),
        wgt_mc=float(g["wgt_mc"]),
    )


def parse(pdf: bytes | Path) -> Factsheet:
    pages = _pages_text(pdf)
    as_of = None
    for text in pages:
        m = DATE_RE.search(text)
        if m:
            as_of = dt.datetime.strptime(m.group(1), "%d %B %Y").date()
            break
    if as_of is None:
        raise ValueError("Kein 'Data as at:'-Datum im PDF gefunden.")

    page = next((t for t in pages if "Country/Market Breakdown" in t), None)
    if page is None:
        raise ValueError("Seite 'Country/Market Breakdown' nicht gefunden.")

    rows: list[Row] = []
    totals: Row | None = None
    for line in page.splitlines():
        line = line.strip()
        m = ROW_RE.match(line)
        if not m:
            continue
        row = _to_row(m)
        if row.country.lower() == "totals":
            totals = row
        else:
            rows.append(row)

    if totals is None:
        raise ValueError("Totals-Zeile nicht gefunden - PDF-Layout hat sich geändert?")

    fs = Factsheet(as_of=as_of, rows=rows, totals=totals)
    _validate(fs)
    return fs


def _check(fs: Factsheet, name: str, passed: bool, detail: str) -> None:
    fs.checks.append((name, passed, detail))


def _validate(fs: Factsheet) -> None:
    r, t = fs.rows, fs.totals

    _check(fs, "Anzahl Länder plausibel", len(r) >= 30, f"{len(r)} Länder geparst")

    for label, attr, tot in (
        ("Konstituenten GDP", "cons_gdp", t.cons_gdp),
        ("Konstituenten MCap", "cons_mc", t.cons_mc),
    ):
        s = sum(getattr(x, attr) for x in r)
        _check(fs, f"Summe {label} == Totals", s == tot, f"{s} vs. {tot}")

    for label, attr, tot in (
        ("Net MCap GDP", "mcap_gdp", t.mcap_gdp),
        ("Net MCap MCap", "mcap_mc", t.mcap_mc),
    ):
        s = sum(getattr(x, attr) for x in r)
        rel = abs(s - tot) / tot if tot else 1.0
        _check(fs, f"Summe {label} == Totals", rel <= MCAP_TOL_REL,
               f"{s:,} vs. {tot:,} (Delta {s - tot:+,})")

    for label, attr, tot in (
        ("Gewichte GDP", "wgt_gdp", t.wgt_gdp),
        ("Gewichte MCap", "wgt_mc", t.wgt_mc),
    ):
        s = sum(getattr(x, attr) for x in r)
        _check(fs, f"Summe {label} == 100 %", abs(s - tot) <= WGT_TOL_PP,
               f"{s:.2f} vs. {tot:.2f} (Delta {s - tot:+.2f} pp)")

    # Gewicht muss dem MCap-Anteil entsprechen (unabhaengige Gegenprobe)
    worst = max(
        (abs(x.wgt_gdp - 100 * x.mcap_gdp / t.mcap_gdp) for x in r), default=0.0
    )
    _check(fs, "Wgt % konsistent mit Net MCap (GDP)", worst <= 0.02,
           f"max. Abweichung {worst:.3f} pp")

    dupes = {x.country for x in r if [y.country for y in r].count(x.country) > 1}
    _check(fs, "Keine doppelten Länder", not dupes, ", ".join(sorted(dupes)) or "-")


def write_csv(fs: Factsheet, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "as_of", "country",
            "cons_gdp", "net_mcap_usdm_gdp", "weight_gdp_pct",
            "cons_mcap", "net_mcap_usdm_mcap", "weight_mcap_pct",
        ])
        for x in sorted(fs.rows, key=lambda r: r.country):
            w.writerow([fs.as_of.isoformat(), x.country,
                        x.cons_gdp, x.mcap_gdp, f"{x.wgt_gdp:.2f}",
                        x.cons_mc, x.mcap_mc, f"{x.wgt_mc:.2f}"])


def print_report(fs: Factsheet) -> None:
    print(f"Stichtag: {fs.as_of:%d.%m.%Y} | Länder: {len(fs.rows)}")
    print("Prüfungen:")
    for name, passed, detail in fs.checks:
        print(f"  [{'OK ' if passed else 'FEHL'}] {name}: {detail}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path, help="Pfad zum Factsheet-PDF")
    ap.add_argument("--out", type=Path, default=None, help="Ziel-CSV")
    args = ap.parse_args()

    fs = parse(args.pdf)
    out = args.out or REPO / "data" / f"ftse_country_weights_{fs.as_of:%Y%m%d}.csv"
    write_csv(fs, out)
    print_report(fs)
    print(f"CSV: {out}")
    return 0 if fs.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
