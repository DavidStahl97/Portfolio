"""Lädt das aktuelle FTSE-Russell-Factsheet (PDF) herunter.

Der Download-Endpunkt liefert immer die neueste veröffentlichte Ausgabe
(Monatsende). Die Datei wird unter data/factsheets/<ISSUE>_<YYYYMMDD>.pdf
abgelegt, wobei das Datum aus dem PDF-Inhalt stammt (siehe parse_factsheet).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import requests

URL = "https://research.ftserussell.com/Analytics/FactSheets/Home/DownloadSingleIssue"
DEFAULT_ISSUE = "GDPWLDS"  # FTSE All-World GDP Weighted
REPO = Path(__file__).resolve().parent.parent


def fetch(issue: str = DEFAULT_ISSUE, timeout: int = 60) -> bytes:
    resp = requests.get(
        URL,
        params={"issueName": issue, "IsManual": "false"},
        timeout=timeout,
        headers={"User-Agent": "portfolio-rebalancer/1.0"},
    )
    resp.raise_for_status()
    data = resp.content
    if not data.startswith(b"%PDF"):
        raise SystemExit(
            f"Antwort ist kein PDF (Content-Type: {resp.headers.get('content-type')}, "
            f"{len(data)} Bytes) - Endpunkt oder IssueName pruefen."
        )
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issue", default=DEFAULT_ISSUE, help="FTSE IssueName, z.B. GDPWLDS")
    ap.add_argument("--out", type=Path, default=None, help="Zielpfad des PDFs")
    args = ap.parse_args()

    data = fetch(args.issue)

    out = args.out
    if out is None:
        from parse_factsheet import extract_as_of_date  # lokal, vermeidet Zirkelimport

        as_of = extract_as_of_date(data)
        out = REPO / "data" / "factsheets" / f"{args.issue}_{as_of:%Y%m%d}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and hashlib.md5(out.read_bytes()).hexdigest() == hashlib.md5(data).hexdigest():
        print(f"unveraendert: {out.relative_to(REPO)}")
    else:
        out.write_bytes(data)
        print(f"gespeichert:  {out.relative_to(REPO)} ({len(data)} Bytes)")
    print(out)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
