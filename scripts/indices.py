"""The FTSE issues this project downloads.

Two kinds, and the difference matters:

* `BLEND` is the one factsheet that carries both weightings side by side
  (`FTSE All-World GDP Weighted` and `FTSE All-World`). It is the source of
  `data/ftse_country_weights_<date>.csv` - the country data the app weights.
* `REGIONS` are the five indices behind the five Vanguard UCITS ETFs the portfolio
  is meant to be built from. Together they tile the same universe as the All-World,
  which is why their factsheets are worth having next to the blend.

Nothing is weighted or combined here. This is a list of what to download and how to
recognise a PDF once it has arrived - the split of the world into regions is FTSE's,
not ours.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Index:
    """One FTSE issue.

    `issue` is the key of the download endpoint (`issueName=`), `title` a piece of
    the index name as it stands on the first page of the PDF - that is what
    `fetch_factsheet` matches to notice a wrong or renamed issue, and `etf` the
    Vanguard UCITS ETF that tracks the index, empty for the blend.
    """

    issue: str
    title: str
    etf: str = ""

    @property
    def label(self) -> str:
        return f"{self.title} ({self.etf})" if self.etf else self.title


# The factsheet the country data come from.
BLEND = Index("GDPWLDS", "FTSE All-World GDP Weighted")

# The five regional indices, in the order of their weight in the All-World. Their
# universes do not overlap; Israel is developed but sits in FTSE's Middle East &
# Africa region and is therefore in none of the five.
REGIONS = (
    Index("AWNAMERS", "FTSE North America", "VNRT"),
    Index("AWDEURS", "FTSE Developed Europe", "VEUR"),
    Index("AWALLE", "FTSE Emerging", "VFEM"),
    Index("WIJPN", "FTSE Japan", "VJPN"),
    Index("AWDPACXJ", "FTSE Developed Asia Pacific ex Japan", "VAPX"),
)

ALL = (BLEND, *REGIONS)

BY_ISSUE = {index.issue: index for index in ALL}


def get(issue: str) -> Index:
    """The registered index for an issue name, or a bare entry for an unknown one.

    An unknown issue is not an error - the factsheet endpoint serves far more issues
    than the six listed here, and `--issue` is meant to stay usable for them. Such an
    issue simply carries no title to check against.
    """
    return BY_ISSUE.get(issue) or Index(issue, "")
