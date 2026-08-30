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
# "Australia 105 1,687,922 1.62" - most regional factsheets have one set of columns
# where the blend has two side by side.
REGION_ROW_RE = re.compile(
    r"^(?P<country>[A-Za-z][A-Za-z .'\-()&/]*?)\s+"
    r"(?P<cons>\d{1,5})\s+(?P<mcap>[\d,]+)\s+(?P<wgt>\d+\.\d{2})\s*$"
)
# ... but not all: the Developed Europe factsheet prints FTSE World Europe beside
# itself and writes a dash where a country belongs to that second index only.
#   "Austria 9 75,954 0.59 9 75,954 0.58"
#   "Czech Rep. - - - 4 13,530 0.10"        <- not in FTSE Developed Europe
_SET = r"(?:(?P<cons>\d{1,5})\s+(?P<mcap>[\d,]+)\s+(?P<wgt>\d+\.\d{2})|-\s+-\s+-)"
REGION_PAIR_RE = re.compile(
    r"^(?P<country>[A-Za-z][A-Za-z .'\-()&/]*?)\s+" + _SET +
    r"\s+(?:\d{1,5}|-)\s+(?:[\d,]+|-)\s+(?:\d+\.\d{2}|-)\s*$"
)
DATE_RE = re.compile(r"Data as at:\s*(\d{1,2}\s+\w+\s+\d{4})")
BREAKDOWN = "Country/Market Breakdown"
# "Country/Market No. of Cons Net MCap (EURm) Wgt %" - not every factsheet is in USD,
# the Developed Europe one is in EUR. The column header is the only place that says so.
CURRENCY_RE = re.compile(r"Net MCap\s*\(([A-Z]{3})m\)")

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


def breakdown_page(pages: list[str]) -> str:
    """The page with the country table, out of the pages of a factsheet."""
    page = next((t for t in pages if BREAKDOWN in t), None)
    if page is None:
        raise ValueError(f"Page '{BREAKDOWN}' not found - has the PDF layout changed?")
    return page


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

    page = breakdown_page(pages)

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


# --- factsheets of a single index -------------------------------------------------
#
# The five regional factsheets (see indices.py) have one set of columns where the
# blend has two, so they need their own row pattern - but the same checks: a sum that
# misses the Totals row means the table was read incompletely, whichever factsheet it
# came from.


@dataclass
class RegionRow:
    country: str
    cons: int
    mcap: int
    wgt: float


@dataclass
class RegionFactsheet:
    issue: str
    title: str
    as_of: dt.date
    currency: str
    rows: list[RegionRow]
    totals: RegionRow
    checks: list[tuple[str, bool, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(passed for _, passed, _ in self.checks)

    @property
    def countries(self) -> list[str]:
        return sorted(r.country for r in self.rows)


def parse_region(pdf: bytes | Path, issue: str = "", title: str = "") -> RegionFactsheet:
    """Reads the country table of a factsheet that covers a single index."""
    pages = pages_text(pdf)
    as_of = None
    for text in pages:
        m = DATE_RE.search(text)
        if m:
            as_of = dt.datetime.strptime(m.group(1), "%d %B %Y").date()
            break
    if as_of is None:
        raise ValueError("No 'Data as at:' date found in the PDF.")

    page = breakdown_page(pages)
    currency = CURRENCY_RE.search(page)
    if currency is None:
        raise ValueError("No 'Net MCap (<CUR>m)' column header - which currency is this?")

    rows: list[RegionRow] = []
    totals: RegionRow | None = None
    for line in page.splitlines():
        row = region_row(line.strip())
        if row is None:
            continue
        if row.country.lower() == "totals":
            totals = row
        else:
            rows.append(row)

    if totals is None:
        raise ValueError("Totals row not found - has the PDF layout changed?")

    fs = RegionFactsheet(issue=issue, title=title, as_of=as_of,
                         currency=currency.group(1), rows=rows, totals=totals)
    _validate_region(fs)
    return fs


def region_row(line: str) -> RegionRow | None:
    """One line of the country table, or None if the line is not one.

    None also for a country that carries dashes in the columns of the index we are
    reading: it belongs to the index printed next to it, not to this one. That is how
    the Developed Europe factsheet lists Greece, Turkiye and the rest of FTSE World
    Europe - and dropping them is the whole point, they are in FTSE Emerging.
    """
    m = REGION_PAIR_RE.match(line) or REGION_ROW_RE.match(line)
    if m is None or m.group("cons") is None:
        return None
    return RegionRow(country=m.group("country").strip(), cons=int(m.group("cons")),
                     mcap=int(m.group("mcap").replace(",", "")), wgt=float(m.group("wgt")))


def _validate_region(fs: RegionFactsheet) -> None:
    r, t = fs.rows, fs.totals

    _check(fs, "At least one country", bool(r), f"{len(r)} countries parsed")

    s = sum(x.cons for x in r)
    _check(fs, "Sum of constituents == totals", s == t.cons, f"{s} vs. {t.cons}")

    s = sum(x.mcap for x in r)
    rel = abs(s - t.mcap) / t.mcap if t.mcap else 1.0
    _check(fs, "Sum of net MCap == totals", rel <= MCAP_TOL_REL,
           f"{s:,} vs. {t.mcap:,} (delta {s - t.mcap:+,})")

    s = sum(x.wgt for x in r)
    _check(fs, "Sum of weights == 100 %", abs(s - t.wgt) <= WGT_TOL_PP,
           f"{s:.2f} vs. {t.wgt:.2f} (delta {s - t.wgt:+.2f} pp)")

    worst = max((abs(x.wgt - 100 * x.mcap / t.mcap) for x in r), default=0.0)
    _check(fs, "Wgt % consistent with net MCap", worst <= 0.02,
           f"max. deviation {worst:.3f} pp")

    dupes = {x.country for x in r if [y.country for y in r].count(x.country) > 1}
    _check(fs, "No duplicate countries", not dupes, ", ".join(sorted(dupes)) or "-")


REGION_CSV = "region_{issue}_{stamp}.csv"


def region_csv_path(fs: RegionFactsheet, data: Path) -> Path:
    return data / REGION_CSV.format(issue=fs.issue, stamp=f"{fs.as_of:%Y%m%d}")


def write_region_csv(fs: RegionFactsheet, path: Path) -> None:
    """One CSV per regional factsheet - the country table as it stands in the PDF.

    `currency` is a column because the factsheets do not agree on one: Developed Europe
    is in EUR, the others in USD. Weights are per index and unaffected, but a net mcap
    added across two of these files without looking at that column would be nonsense.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["as_of", "issue", "index", "currency", "country",
                    "cons", "net_mcap", "weight_pct"])
        for x in sorted(fs.rows, key=lambda r: r.country):
            w.writerow([fs.as_of.isoformat(), fs.issue, fs.title, fs.currency,
                        x.country, x.cons, x.mcap, f"{x.wgt:.2f}"])


def read_region_csv(path: Path) -> dict:
    """The header fields and the country list of one region CSV.

    Deliberately not a RegionFactsheet: the checks of a run belong to the run, and
    what is read back is what the export needs - which index, and which countries.
    """
    with path.open(encoding="utf-8") as fh:
        recs = list(csv.DictReader(fh))
    if not recs:
        raise ValueError(f"{path.name} has no rows.")
    head = recs[0]
    return {
        "as_of": dt.date.fromisoformat(head["as_of"]),
        "issue": head["issue"],
        "index": head["index"],
        "currency": head["currency"],
        "countries": sorted(r["country"] for r in recs),
    }


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
