"""Downloads the current FTSE Russell factsheet (PDF).

The download endpoint always serves the latest published issue (month end). The
file is stored as data/factsheets/<ISSUE>_<YYYYMMDD>.pdf, with the date taken
from the PDF content (see parse_factsheet).
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
            f"Response is not a PDF (content type: {resp.headers.get('content-type')}, "
            f"{len(data)} bytes) - check the endpoint or the issue name."
        )
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issue", default=DEFAULT_ISSUE, help="FTSE issue name, e.g. GDPWLDS")
    ap.add_argument("--out", type=Path, default=None, help="target path of the PDF")
    args = ap.parse_args()

    data = fetch(args.issue)

    out = args.out
    if out is None:
        from parse_factsheet import extract_as_of_date  # local, avoids a circular import

        as_of = extract_as_of_date(data)
        out = REPO / "data" / "factsheets" / f"{args.issue}_{as_of:%Y%m%d}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and hashlib.md5(out.read_bytes()).hexdigest() == hashlib.md5(data).hexdigest():
        print(f"unchanged: {out.relative_to(REPO)}")
    else:
        out.write_bytes(data)
        print(f"saved:     {out.relative_to(REPO)} ({len(data)} bytes)")
    print(out)
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
