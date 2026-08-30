"""Downloads FTSE Russell factsheets (PDF).

The download endpoint always serves the latest published issue (month end). A file is
stored as data/factsheets/<ISSUE>_<YYYYMMDD>.pdf, with the date taken from the PDF
content (see parse_factsheet).

    python scripts/fetch_factsheet.py                 # the blend, GDPWLDS
    python scripts/fetch_factsheet.py --regions       # the five regional indices
    python scripts/fetch_factsheet.py --all           # all six
    python scripts/fetch_factsheet.py --issue WIJPN   # any other issue

Every download of a registered issue is checked against the index name in the PDF, so
a wrong or renamed issue name shows up here instead of producing a plausible-looking
file of the wrong index.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

import indices

URL = "https://research.ftserussell.com/Analytics/FactSheets/Home/DownloadSingleIssue"
DEFAULT_ISSUE = indices.BLEND.issue  # FTSE All-World GDP Weighted
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


def verify_title(data: bytes, index: indices.Index) -> None:
    """Checks that the PDF really is the index we asked for.

    The endpoint answers an unknown issue name with a PDF of something else rather
    than with an error, so without this check a typo becomes a silently wrong file.
    An unregistered issue carries no title and is not checked.
    """
    if not index.title:
        return

    from parse_factsheet import pages_text  # local, keeps the import cost off --help

    first = next(iter(pages_text(data)), "")
    if index.title not in first:
        raise SystemExit(
            f"{index.issue}: the PDF does not name '{index.title}' on its first page - "
            f"the issue name is wrong or the index has been renamed."
        )


def save(data: bytes, issue: str, as_of: dt.date, out: Path | None = None) -> Path:
    """Writes the PDF to data/factsheets/<ISSUE>_<YYYYMMDD>.pdf and reports."""
    path = out or REPO / "data" / "factsheets" / f"{issue}_{as_of:%Y%m%d}.pdf"
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and hashlib.md5(path.read_bytes()).digest() == hashlib.md5(data).digest():
        print(f"unchanged: {path.relative_to(REPO)}")
    else:
        path.write_bytes(data)
        print(f"saved:     {path.relative_to(REPO)} ({len(data)} bytes)")
    return path


def fetch_index(index: indices.Index, out: Path | None = None) -> tuple[Path, dt.date]:
    """Download, check the index name, store - the whole way for one issue."""
    from parse_factsheet import extract_as_of_date  # local, avoids a circular import

    data = fetch(index.issue)
    verify_title(data, index)
    as_of = extract_as_of_date(data)
    return save(data, index.issue, as_of, out), as_of


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--issue", action="append", default=[],
                    help="FTSE issue name, e.g. GDPWLDS; may be repeated")
    ap.add_argument("--regions", action="store_true",
                    help="the five regional indices of the Vanguard ETFs")
    ap.add_argument("--all", action="store_true",
                    help="the blend and the five regional indices")
    ap.add_argument("--out", type=Path, default=None,
                    help="target path of the PDF; only for a single issue")
    args = ap.parse_args()

    wanted: list[indices.Index] = [indices.get(i) for i in args.issue]
    if args.all:
        wanted = list(indices.ALL)
    elif args.regions:
        wanted += list(indices.REGIONS)
    if not wanted:
        wanted = [indices.BLEND]

    if args.out and len(wanted) > 1:
        ap.error("--out works for a single issue only")

    for index in wanted:
        print(f"{index.issue}: {index.label or 'unregistered issue'}")
        path, _ = fetch_index(index, args.out)
        print(f"           {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
