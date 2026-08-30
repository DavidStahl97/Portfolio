"""Parses the country breakdown out of the FTSE factsheet PDF into a CSV.

The factsheet carries both weightings side by side:
  - FTSE All-World GDP Weighted  -> GDP weight
  - FTSE All-World               -> market capitalisation weight

Every parse run is checked (sum over all countries vs. the Totals row in the PDF);
if a deviation exceeds the tolerance, the script exits with code 1.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
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

# Tolerances: the Wgt columns are rounded to two decimals, i.e. up to 0.005
# percentage points of rounding error per country.
WGT_TOL_PP = 0.5     # percentage points, sum over countries vs. 100.00
MCAP_TOL_REL = 1e-6  # relative deviation of the net mcap sum


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


def pages_text(pdf: bytes | Path) -> list[str]:
    with _open(pdf) as doc:
        return [p.extract_text() or "" for p in doc.pages]


def extract_as_of_date(pdf: bytes | Path) -> dt.date:
    for text in pages_text(pdf):
        m = DATE_RE.search(text)
        if m:
            return dt.datetime.strptime(m.group(1), "%d %B %Y").date()
    raise ValueError("No 'Data as at:' date found in the PDF.")


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
    pages = pages_text(pdf)
    as_of = None
    for text in pages:
        m = DATE_RE.search(text)
        if m:
            as_of = dt.datetime.strptime(m.group(1), "%d %B %Y").date()
            break
    if as_of is None:
        raise ValueError("No 'Data as at:' date found in the PDF.")

    page = next((t for t in pages if "Country/Market Breakdown" in t), None)
    if page is None:
        raise ValueError("Page 'Country/Market Breakdown' not found.")

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
        raise ValueError("Totals row not found - has the PDF layout changed?")

    fs = Factsheet(as_of=as_of, rows=rows, totals=totals)
    _validate(fs)
    return fs


def _check(fs: Factsheet, name: str, passed: bool, detail: str) -> None:
    fs.checks.append((name, passed, detail))


def _validate(fs: Factsheet) -> None:
    r, t = fs.rows, fs.totals

    _check(fs, "Number of countries plausible", len(r) >= 30, f"{len(r)} countries parsed")

    for label, attr, tot in (
        ("constituents GDP", "cons_gdp", t.cons_gdp),
        ("constituents MCap", "cons_mc", t.cons_mc),
    ):
        s = sum(getattr(x, attr) for x in r)
        _check(fs, f"Sum of {label} == totals", s == tot, f"{s} vs. {tot}")

    for label, attr, tot in (
        ("net MCap GDP", "mcap_gdp", t.mcap_gdp),
        ("net MCap MCap", "mcap_mc", t.mcap_mc),
    ):
        s = sum(getattr(x, attr) for x in r)
        rel = abs(s - tot) / tot if tot else 1.0
        _check(fs, f"Sum of {label} == totals", rel <= MCAP_TOL_REL,
               f"{s:,} vs. {tot:,} (delta {s - tot:+,})")

    for label, attr, tot in (
        ("weights GDP", "wgt_gdp", t.wgt_gdp),
        ("weights MCap", "wgt_mc", t.wgt_mc),
    ):
        s = sum(getattr(x, attr) for x in r)
        _check(fs, f"Sum of {label} == 100 %", abs(s - tot) <= WGT_TOL_PP,
               f"{s:.2f} vs. {tot:.2f} (delta {s - tot:+.2f} pp)")

    # The weight has to match the mcap share (independent cross-check)
    worst = max(
        (abs(x.wgt_gdp - 100 * x.mcap_gdp / t.mcap_gdp) for x in r), default=0.0
    )
    _check(fs, "Wgt % consistent with net MCap (GDP)", worst <= 0.02,
           f"max. deviation {worst:.3f} pp")

    dupes = {x.country for x in r if [y.country for y in r].count(x.country) > 1}
    _check(fs, "No duplicate countries", not dupes, ", ".join(sorted(dupes)) or "-")


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


def meta_path(csv_path: Path) -> Path:
    """data/ftse_country_weights_20260731.csv -> data/run_20260731.json"""
    return csv_path.with_name(csv_path.name.replace("ftse_country_weights_", "run_")
                              ).with_suffix(".json")


def write_meta(fs: Factsheet, path: Path) -> None:
    """Keeps totals and check results - everything the CSV does not carry. That makes
    an as-of date complete from CSV + JSON alone, without the PDF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "as_of": fs.as_of.isoformat(),
        "totals": {
            "cons_gdp": fs.totals.cons_gdp, "mcap_gdp": fs.totals.mcap_gdp,
            "wgt_gdp": fs.totals.wgt_gdp, "cons_mc": fs.totals.cons_mc,
            "mcap_mc": fs.totals.mcap_mc, "wgt_mc": fs.totals.wgt_mc,
        },
        "checks": [{"name": n, "passed": p, "detail": d} for n, p, d in fs.checks],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def load_run(csv_path: Path) -> Factsheet:
    """Rebuilds a factsheet from CSV + JSON metadata."""
    with csv_path.open(encoding="utf-8") as fh:
        recs = list(csv.DictReader(fh))
    rows = [Row(country=r["country"],
                cons_gdp=int(r["cons_gdp"]), mcap_gdp=int(r["net_mcap_usdm_gdp"]),
                wgt_gdp=float(r["weight_gdp_pct"]),
                cons_mc=int(r["cons_mcap"]), mcap_mc=int(r["net_mcap_usdm_mcap"]),
                wgt_mc=float(r["weight_mcap_pct"])) for r in recs]
    meta = json.loads(meta_path(csv_path).read_text(encoding="utf-8"))
    t = meta["totals"]
    fs = Factsheet(
        as_of=dt.date.fromisoformat(meta["as_of"]),
        rows=rows,
        totals=Row(country="Totals", **t),
        checks=[(c["name"], c["passed"], c["detail"]) for c in meta["checks"]],
    )
    return fs


def print_report(fs: Factsheet) -> None:
    print(f"As-of date: {fs.as_of:%Y-%m-%d} | countries: {len(fs.rows)}")
    print("Checks:")
    for name, passed, detail in fs.checks:
        print(f"  [{'OK  ' if passed else 'FAIL'}] {name}: {detail}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path, help="path to the factsheet PDF")
    ap.add_argument("--out", type=Path, default=None, help="target CSV")
    args = ap.parse_args()

    fs = parse(args.pdf)
    out = args.out or REPO / "data" / f"ftse_country_weights_{fs.as_of:%Y%m%d}.csv"
    write_csv(fs, out)
    write_meta(fs, meta_path(out))
    print_report(fs)
    print(f"CSV: {out}")
    return 0 if fs.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
