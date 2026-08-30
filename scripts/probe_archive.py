"""Probes whether the factsheet endpoint hands out earlier issues.

The download endpoint is documented as serving the latest issue only:

    .../Home/DownloadSingleIssue?issueName=GDPWLDS&IsManual=false

Whether it also accepts a date is not documented anywhere, so the only way to
find out is to ask it. This script sends the request once per candidate
parameter name, with the date of an earlier month end, and reports what came
back. It writes nothing into data/ unless --save is given, and it is a probe,
not part of the monthly run: update.py does not call it.

    python scripts/probe_archive.py                      # last month end, one format
    python scripts/probe_archive.py --date 20260630 --all
    python scripts/probe_archive.py --date 20260630 --save

A parameter counts as a hit only if the PDF that comes back is a different one
*and* carries the requested as-of date. Anything that merely differs from the
current issue - an error page, a PDF of some other index - is reported as such
and nothing more. On a hit, --save puts the PDF where update.py expects it:

    python scripts/update.py --pdf data/factsheets/GDPWLDS_20260630.pdf

Exit code 0 means an earlier issue came back, 1 means it did not - either
because no parameter was understood or because the plain request already
failed. Both are answers; only the first one is a way to backfill months.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_factsheet
import parse_factsheet

REPO = Path(__file__).resolve().parent.parent

# Names an ASP.NET endpoint might plausibly bind a date to. Unknown query
# parameters are usually ignored in silence, which is why the answer to every
# one of them has to be compared against the current issue.
PARAMS = [
    "asOfDate", "AsOfDate", "asOf", "asAtDate", "asAt",
    "effectiveDate", "EffectiveDate", "date", "Date",
    "issueDate", "IssueDate", "reportDate", "dataDate", "publishDate",
    "month", "period", "periodEnd", "endDate", "dt",
]

# The format a date arrives in is a second unknown, independent of the name.
FORMATS = ["%Y%m%d", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %B %Y", "%Y%m", "%Y-%m"]

# IsManual is the one flag the endpoint is known to take. "true" reads like the
# manual issue selection of the portal, so it is worth trying on both sides.
MANUAL = ["false", "true"]


def month_end(d: dt.date) -> dt.date:
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


def previous_month_end(d: dt.date) -> dt.date:
    return month_end(d.replace(day=1) - dt.timedelta(days=1))


def request(issue: str, manual: str, extra: dict[str, str], timeout: int) -> requests.Response:
    return requests.get(
        fetch_factsheet.URL,
        params={"issueName": issue, "IsManual": manual, **extra},
        timeout=timeout,
        headers={"User-Agent": "portfolio-rebalancer/1.0"},
    )


def describe(resp: requests.Response, baseline_md5: str) -> tuple[str, dt.date | None]:
    """Classifies one answer: 'latest', 'other', 'no pdf' or an HTTP status."""
    if resp.status_code != 200:
        return f"HTTP {resp.status_code}", None
    body = resp.content
    if not body.startswith(b"%PDF"):
        kind = (resp.headers.get("content-type") or "?").split(";")[0]
        return f"no pdf ({kind}, {len(body)} bytes)", None
    if hashlib.md5(body).hexdigest() == baseline_md5:
        return "latest", None
    try:
        return "other pdf", parse_factsheet.extract_as_of_date(body)
    except ValueError:
        return "other pdf (no date in it)", None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--issue", default=fetch_factsheet.DEFAULT_ISSUE)
    ap.add_argument("--date", default=None,
                    help="month end to ask for, YYYYMMDD "
                         "(default: the month before the current issue)")
    ap.add_argument("--all", action="store_true",
                    help="every date format per parameter, not just %%Y%%m%%d")
    ap.add_argument("--save", action="store_true",
                    help="write a hit to data/factsheets/, ready for update.py")
    ap.add_argument("--delay", type=float, default=1.0,
                    help="seconds between two requests (default 1.0)")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    target = dt.datetime.strptime(args.date, "%Y%m%d").date() if args.date else None

    print(f"issue {args.issue}")
    print("baseline: the current issue, without any date ...")
    baseline = request(args.issue, "false", {}, args.timeout)
    if baseline.status_code != 200 or not baseline.content.startswith(b"%PDF"):
        print(f"  the plain request already fails ({baseline.status_code}, "
              f"{len(baseline.content)} bytes) - nothing to compare against.")
        return 1
    baseline_md5 = hashlib.md5(baseline.content).hexdigest()
    baseline_as_of = parse_factsheet.extract_as_of_date(baseline.content)
    print(f"  {len(baseline.content)} bytes, as of {baseline_as_of:%d %B %Y}, "
          f"md5 {baseline_md5[:12]}")

    # Without --date, the month before the current issue - which is the issue's own
    # as-of date, not today's month: the factsheet appears with a lag, so late in
    # August the current issue is still the one as of 31 July.
    if target is None:
        target = previous_month_end(baseline_as_of)
    if target >= baseline_as_of:
        print(f"  asking for {target:%d %B %Y} is not earlier than that - "
              f"pick an earlier month with --date.")
        return 1
    print(f"asking for {target:%d %B %Y}")

    formats = FORMATS if args.all else FORMATS[:1]
    hits: list[tuple[str, str, str, bytes]] = []
    print(f"\n{len(PARAMS) * len(formats) * len(MANUAL)} requests "
          f"({len(PARAMS)} names x {len(formats)} formats x IsManual false/true)\n")

    for name in PARAMS:
        for fmt in formats:
            value = target.strftime(fmt)
            for manual in MANUAL:
                time.sleep(args.delay)
                try:
                    resp = request(args.issue, manual, {name: value}, args.timeout)
                except requests.RequestException as exc:
                    verdict, as_of = f"failed ({exc.__class__.__name__})", None
                else:
                    verdict, as_of = describe(resp, baseline_md5)
                label = f"{name}={value} IsManual={manual}"
                if as_of == target:
                    print(f"  HIT  {label:52} -> the issue as of {as_of:%d %B %Y}")
                    hits.append((name, value, manual, resp.content))
                elif as_of is not None:
                    print(f"       {label:52} -> {verdict}, as of {as_of:%d %B %Y}")
                elif verdict != "latest":
                    print(f"       {label:52} -> {verdict}")

    print()
    if not hits:
        print("No parameter changed the answer: the endpoint serves the current issue")
        print("and nothing else. Earlier months have to come from PDFs kept elsewhere.")
        return 1

    name, value, manual, body = hits[0]
    print(f"{len(hits)} hit(s). The endpoint does take a date: {name}={value} "
          f"(IsManual={manual}).")
    if args.save:
        out = REPO / "data" / "factsheets" / f"{args.issue}_{target:%Y%m%d}.pdf"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
        print(f"saved: {out.relative_to(REPO)} ({len(body)} bytes)")
        print(f"next:  python scripts/update.py --pdf {out.relative_to(REPO)}")
    else:
        print("Re-run with --save to keep the PDF, then feed it to update.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
