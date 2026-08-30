# CLAUDE.md

Notes for Claude Code (claude.ai/code) when working in this repository.

@README.md

The README explains purpose, data source, usage and the workflows – it is imported
above and not repeated here. What follows is only what you stumble over while working
in the code.

## Language

**Everything in this repository is English, without exception.** Prose as well as
identifiers: comments, docstrings, CLI help, error messages, everything visible in the
app, the README, commit messages, pull request texts, workflow and job names,
route names and file names. There is no German anywhere – if you find some, translate
it.

The country names are the one thing that is not translated: they come from the PDF
(`Turkiye`, `Czech Rep.`) and are the key by which as-of dates are compared.

Keep identifiers as they are unless the task is a rename: `as_of`,
`net_mcap_usdm_gdp` in the CSV, `asOf`, `mcap`, `consGdp` in the JSON. They are part
of the data contract between `export_data.py` and `web/src/lib/types.ts`.

Commit messages stay plain ASCII – the terminal they are written from does not handle
anything else reliably.

## The line this is all about

**Python reads and checks. It computes nothing.** What it produces are the raw data of
the factsheet and the record of their checks. The weighting of the portfolio lives in
exactly one place: `web/src/lib/weights.ts`.

That boundary is the reason this project exists in this form, and it was drawn
deliberately once (`build_portfolio.py` and the `target_weights_*.csv` were deleted for
it). If a task tempts you to compute a mix, a target weight or a cap in Python, it
belongs in the app. And the other way round: if something is to be read out of the PDF
or checked, it belongs in Python.

`export_data.py` sits on the Python side and **only reshapes** – every figure it writes
already stands like that in `data/`. If a computation appears there, that is a bug.

## What is versioned

| | |
|---|---|
| `data/ftse_country_weights_<date>.csv` | one row per country, versioned |
| `data/run_<date>.json` | `totals` from the PDF + the nine check results, versioned |
| `data/factsheets/*.pdf` | ignored, downloadable again at any time |
| `web/static/data/`, `web/static/csv/` | ignored, produced by `export_data.py` |
| `web/static/favicon.svg`, `web/static/pwa/` | **source**, versioned – do not ignore them with the rest of `static/` |
| `web/build/`, `preview/` | ignored |

`data/` is the truth. The site is rebuilt completely from it on every deploy, including
every earlier as-of date – which is why a layout change acts retroactively on the whole
history, and why no generated HTML may live in the repository.

## Checking

There is no test suite. Checking works like this:

1. **Python:** `python scripts/update.py --pdf data/factsheets/<file>.pdf`
   runs through and reports nine green checks, or it aborts. A PDF is under
   `data/factsheets/` after the first run; without a network, `--pdf` is the way.
2. **App:** `npm run check --prefix web` is `svelte-check` against
   `web/src/lib/types.ts`. That is the only place where a field renamed in
   `export_data.py` shows up before the site stays empty. CI runs it.
3. **In the browser, and really.** Points 1 and 2 were green when the slider sat at 0
   instead of 50 on the first visit and the site showed pure GDP weighting. What has
   not been looked at counts as unchecked.

For point 3, `npm run dev --prefix web` is enough. Anyone who wants to look at the
production state needs a server that behaves like GitHub Pages – that is, serves under
`/<repository>/` and answers unknown paths with the `404.html`, otherwise the as-of
date addresses cannot be opened directly:

```python
# unknown paths -> 404.html, the way Pages does it
import http.server, os, socketserver
ROOT = "/tmp/serve"        # containing: Portfolio/ = the content of web/build
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def send_error(self, code, message=None, explain=None):
        if code == 404 and os.path.exists(ROOT + "/Portfolio/404.html"):
            body = open(ROOT + "/Portfolio/404.html", "rb").read()
            self.send_response(404); self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body); return
        super().send_error(code, message, explain)
socketserver.TCPServer.allow_reuse_address = True
socketserver.TCPServer(("", 8771), H).serve_forever()
```

The build without a path prefix (`BASE_PATH="" BUILD_DIR="../preview" npm run build`)
can simply be served at the root – that is the version that goes into the artifact.

One as-of date is not enough to see everything: the history chart and the Δ column need
two. For checking you can produce synthetic previous months (copy the CSV, change
`as_of`, scatter the weights a little, copy the `run_*.json` along) – **delete them
afterwards**, they do not belong in the repository.

The progressive web app cannot be checked over `file://` – a service worker needs an
origin. `npm run preview --prefix web` and `http://localhost:4173/` are enough,
`localhost` counts as secure. Checked means: under *Application* the service worker is
*activated*, and with *Network → Offline* switched on all four page types still open –
the start page, an as-of date reached directly by its address, `/history/` and
`/data/`. The `python3` server above does the same for the build with the path prefix.

## The issue registry

`scripts/indices.py` lists the six FTSE issues that get downloaded: the blend
(`GDPWLDS`, the one the country data come from) and the five regional indices behind
Vanguard's five UCITS ETFs. It holds names, not numbers - the regional split is FTSE's,
and combining anything out of it would belong in the app anyway.

**The five issue names have not yet been confirmed against a live download.** They were
read off FTSE's own factsheet URLs, but the download endpoint is unreachable from the
development container, so the first run that has a network is the one that proves them.
That is what `verify_title` is for: the endpoint answers an unknown issue name with a
PDF of some other index rather than with an error, so without the check a typo becomes
a plausible-looking file of the wrong index. If a title check fails, correct the issue
name in `indices.py` - do not loosen the check.

Fetching a regional factsheet is deliberately allowed to fail: it is a side dataset and
must not hold the country data of a run hostage, so `update.py` warns and keeps its exit
code. `check_sources.py` is the opposite - it exists to find such problems, so there
everything is a failure.

## The five regions in the app

Which country belongs to which of the five is **not written anywhere by hand**. Each
regional factsheet's country table becomes `data/region_<ISSUE>_<date>.csv`, written by
`update.py`, and the grouping is whatever those files say. A reclassification therefore
arrives on its own - **Greece moves from FTSE Emerging to FTSE Developed Europe on 21
September 2026** - and `check_sources.py` compares the fresh factsheet against the
newest committed CSV and names what moved. That difference is an `[INFO]`, not a
failure: the next run writes the new table, and that is the fix.

The one exception is FTSE Japan. Its factsheet has no country table at all, so
`indices.py` carries `covers=("Japan",)`. `check_sources.py` prints that factsheet's
page headings on every run, so the exception stays checkable rather than believed - as
of July 2026 they are `FTSE Japan Index`, `Top 10 Constituents`, `bmkImage1 bmkImage2
bmkImage3`, and there is nothing to read a country from. If a breakdown page ever
appears there, drop the `covers` and let the CSV take over.

`export_data.py` builds `web/static/data/regions.json` out of the CSVs of the newest
as-of date - all or nothing, since Japan alone would draw one tiny region and the whole
rest as uncovered. `+layout.ts` loads it alongside `index.json`, and a missing file is a
state, not an error: the charts then simply do not offer the region view.

The grouping and the summing live in `weights.ts` with the rest of the weighting:
`regionGroups` cuts the world into the five indices plus one group for what none of
them covers, `countryGroups` does the same per country, and `shares` sums either under
whichever way of valuing a country a chart asks for. `PieCharts.svelte` only draws.
Two things there are deliberate and easy to undo by accident:

* **The region order is the file order, not the weight order.** The colour belongs to
  the region; sorting by weight would let a region change colour when the slider moves.
* **The uncovered group is never a series colour**, it gets `--baseline` like the
  remainder. A country the five ETFs cannot buy must not look like one they can.

## What the five ETFs deliver

`viaRegions` and `activeShare` in `weights.ts` answer the question the region view
raises: if the portfolio is *held* as the five regional ETFs, what country weights come
out? The five hit their region exactly, and then weight the countries inside it by
market capitalisation - that is what an index fund tracking a regional index holds.
So the GDP half of the mix survives between the regions and is undone within them.

Two properties are worth keeping, because they are what makes the figure trustworthy:

* **At `split = 1` the active share is exactly 0.** Pure market capitalisation is what
  the ETFs hold anyway, so there is nothing left to distort. If that number ever comes
  out non-zero, the weighting is wrong, not the display.
* **It is linear in the tilt** - 0, 6.18, 12.37, 18.55, 24.74 % at 100/75/50/25/0 %
  market capitalisation. Same reason: both sides of the difference are linear in
  `split`.

Countries in none of the five keep their target weight; they are not bought through a
regional ETF, so there is nothing to distort. Israel is the case.

## The parser

`ROW_RE` in `parse_factsheet.py` reads lines of the form
`Australia 105 1,060,680 1.08 105 1,687,922 1.62`. If FTSE changes the layout, that is
the place. The country names come from the PDF and are English (`Turkiye`,
`Czech Rep.`) – do not translate them, they are the key by which as-of dates are
compared.

`REGION_ROW_RE` is the same line one column set shorter, for the regional factsheets:
`Australia 105 1,687,922 1.62`. All patterns are anchored at both ends, so a blend row
cannot accidentally match the regional one.

The five regional factsheets are **not** all the same shape - that is the thing to know
before touching `parse_region`:

* **Developed Europe (`AWDEURS`) prints two indices side by side**, itself and FTSE
  World Europe, exactly like the blend. Countries that are only in the second index
  carry dashes in the first three columns (`Czech Rep. - - - 4 13,530 0.10`), and
  dropping those is the point - they are in FTSE Emerging. That is what
  `REGION_PAIR_RE` and the `None` return of `region_row` are for.
* **Japan (`WIJPN`) has no `Country/Market Breakdown` page at all.** A single-country
  index has nothing to break down. Its country therefore cannot be read from anywhere
  and is named in `indices.py` as `covers=("Japan",)` - the one hand-kept country list
  in the project, and the only one that cannot go out of date on its own.
* **The Developed Europe factsheet is denominated in EUR**, the others in USD. Weights
  and country lists are unaffected, which is all we take from them - but never add net
  mcap across two regional factsheets without looking at the column header first.
* The breakdown page also carries the ICB Supersector table, whose rows start with the
  ICB code. They are skipped because the patterns require a letter first.

The nine checks are not decoration, they are half the point of the project. Two
tolerances are computed, not guessed:

* `WGT_TOL_PP = 0.5` – the weight columns are rounded to two decimals, so with ~48
  countries there is up to 0.24 pp of noise.
* `MCAP_TOL_REL = 1e-6` – the net mcap sum deviates by single millions through the same
  rounding.

The fourth check (`Wgt %` against `net mcap / total`) is not a repetition of the sum
check: it catches swapped or shifted columns that a plain sum would survive.

## The app

SvelteKit 5 with runes, `adapter-static`, `ssr = false`. The model and origin of the
setup is `DavidStahl97/Komoot-Collection`.

* **`base`** comes from `GITHUB_REPOSITORY`, `BASE_PATH` wins. Every path in markup and
  `fetch` needs it – a forgotten `base` is the mistake that works locally and gives a
  404 on Pages.
* **`BUILD_DIR`** in `svelte.config.js` allows the second build next to it (`preview`).
  `--outDir` does *not* – `adapter-static` does not write where Vite builds.
* The start page and `/data/`, `/history/` are prerendered; an as-of date is a parameter
  and is reached through the `404.html`. Pages answers with status 404 and the app
  renders anyway – that is the construction, not a bug.
* **Missing data is a state, not an error.** `+layout.ts` treats a 404 on
  `data/index.json` as "no as-of dates yet" and shows `Empty.svelte`. A thrown error
  becomes a bare "500 Internal Error" in production builds – that has happened before.
* **Anything that has to exist before JavaScript runs belongs in `app.html`** – the
  manifest link, the icons, the `<noscript>`. Nothing renders on a server, so a
  `<svelte:head>` entry arrives only after hydration. The service worker therefore
  registers itself in `onMount` in `+layout.svelte`: SvelteKit does not run `app.html`
  through Vite's html plugin, so `vite-plugin-pwa` injects nothing for us.
* **The manifest and the service worker are generated**, by `SvelteKitPWA` in
  `vite.config.ts`, out of the finished build – nothing about the precache list is kept
  in step by hand. Its paths are relative throughout because the site lives under
  `/<repository>/`, and `globPatterns` names the `.csv` explicitly: the download links
  of the data page belong to the site as much as the JSON does. Navigations are
  answered from the precached shell, which is what makes an as-of date address open
  offline although its URL was never a file.
* **The mix** lives in `split.svelte.ts` as shared state, default 0.5, remembered in
  `localStorage`. Careful: `Number(null)` is `0`, not `NaN` – without a check for
  `null`, the slider sits at 0 on the first visit.
* The Δ column computes the previous as-of date with the **same** mix as the current
  one; otherwise it would show the movement of the slider as a market movement.
* `let x = $state(something_reactive)` produces the warning
  `state_referenced_locally`. Either `untrack(...)` in the initialiser, or derive the
  value.

## Charts

The eight series colours in `app.css` are checked against colour vision deficiency and
contrast and are to be assigned in that order – the colour belongs to the country, not
to its rank. Beyond that:

* One axis, never two. All three series in the bar chart share one scale, and that is
  the comparison this is about.
* Text never carries the series colour; the colour is in the bar or in the key next to
  it.
* Δ values are coloured **neutrally**. A rising country weight is neither good nor bad,
  only a need to rebalance – green/red would be an assertion.
* End labels are pushed apart (`labels` in `History.svelte`), and shifted ones get a
  leader line. Do not truncate them.

## Workflows

Three of them, with clear responsibilities:

| File | Trigger | Does |
|---|---|---|
| `pages.yml` | push to `main` | builds and publishes the site |
| `data.yml` | manual | fetch the factsheet, check it, branch + commit + pull request, site as an artifact |
| `pr.yml` | pull request | builds the site and attaches it as an artifact |
| `sources.yml` | push to `scripts/`, manual | fetches all six factsheets and reads them |

Traps that have already sprung:

* A pull request opened with the `GITHUB_TOKEN` **triggers no further workflows** – so
  `pr.yml` does not run for the data runs. That is why `data.yml` builds the site
  itself and links the artifact in the text of the pull request.
* `--force-with-lease` fails after a shallow checkout with "stale info" when the branch
  is unknown. Run `git fetch origin <branch> || true` first.
* GitHub Pages knows **one** site per repository. Per-pull-request preview URLs would
  only be possible through a `gh-pages` branch with subfolders; deliberately not done –
  the preview is the artifact.
* Required repo settings: Pages source "GitHub Actions"; under *Actions → General*,
  "Allow GitHub Actions to create and approve pull requests" has to be on, otherwise
  `gh pr create` fails. The `github-pages` environment must have **no** required
  reviewers – the merge is the approval.

## Environment

The commands belong in the repository root; `npm` with `--prefix web`. After a `cd web`
inside a command, the shell may stay there – use absolute paths in the next command or
check the directory. That has already written a README into the wrong directory.
