# Portfolio: 50 % market capitalisation / 50 % GDP

Country target weights for a world portfolio weighted half by market capitalisation
and half by gross domestic product (GDP, purchasing power parity).

**The division of labour is the main point of this project:** Python fetches the raw
data out of the factsheet and checks them – nothing more. The weighting happens
exclusively in the app, in the browser, with a slider. That way there is no second
place where a mix would be "fixed", and no computed figures in the repository that
could stop matching the raw data.

## Data source

A single document delivers both halves: the monthly factsheet of the
**FTSE All-World GDP Weighted Index** (issue name `GDPWLDS`). Its
"Country/Market Breakdown" page presents, side by side per country

* `FTSE All-World GDP Weighted` → the GDP weight (IMF PPP forecasts, annual review
  in March), and
* `FTSE All-World` → the market capitalisation weight (free float).

Both are therefore delimited identically (same universe, same as-of date) – exactly
what a 50/50 mix needs. The PDF is freely available, and the download endpoint always
serves the latest issue.

### The five regional factsheets

Next to the blend the run fetches the factsheets of the five indices that together
tile the same universe as the All-World - the indices behind Vanguard's five regional
UCITS ETFs, which is how the portfolio is meant to be held:

| Index | FTSE issue | ETF |
|---|---|---|
| FTSE North America | `AWNAMERS` | VNRT |
| FTSE Developed Europe | `AWDEURS` | VEUR |
| FTSE Emerging | `AWALLE` | VFEM |
| FTSE Japan | `WIJPN` | VJPN |
| FTSE Developed Asia Pacific ex Japan | `AWDPACXJ` | VAPX |

Their country tables are read with the same checks as the blend's - a factsheet of a
single index has one set of columns where the blend has two, so it needs its own row
pattern but not its own idea of what a correct table looks like. Nothing is versioned
from them yet.

The point of having them is that the split of the world into regions is read out of
FTSE's own documents instead of a country list kept by hand: `check_sources.py`
compares the five country tables against the blend's and names every country that ends
up in two regions or in none. Israel is the known gap - developed, but in FTSE's
Middle East & Africa region and therefore in none of the five, which is roughly 0.3 %
of the index.

A regional factsheet that cannot be fetched during `update.py` is a warning, not a
failed run - the country data of the run do not depend on it. `check_sources.py` is
stricter: there any problem is a failure, because looking for one is its whole job.

## What lives where

Python **reads and checks**; it computes nothing and writes neither markup nor
stylesheet nor script. What it produces are the raw data of the factsheet and the
record of their checks. The app under `web/` turns them into the site – and it is the
only place where any weighting happens.

| File | Purpose |
|---|---|
| `scripts/indices.py` | the FTSE issues that are downloaded: the blend and the five regions |
| `scripts/fetch_factsheet.py` | downloads factsheet PDFs |
| `scripts/parse_factsheet.py` | parses the country table, checks it, writes CSV + `run_*.json` |
| `scripts/check_sources.py` | fetches every registered issue and checks it can still be read |
| `scripts/export_data.py` | reshapes the versioned data into `web/static/data/` (without computing) |
| `scripts/update.py` | full run: download → parse → check → export |
| `web/` | the single-page app (SvelteKit, `adapter-static`) |
| `web/src/lib/weights.ts` | **the only place where the portfolio is weighted** |
| `web/src/lib/types.ts` | the data contract with `export_data.py` – change both sides together |
| `web/static/pwa/` | the app icons – source, versioned like `favicon.svg` |

## Usage

```bash
pip install -r requirements.txt

python scripts/update.py                 # download → check → export
python scripts/update.py --pdf data/factsheets/GDPWLDS_20260731.pdf   # without network

npm ci --prefix web
npm run dev --prefix web                 # http://localhost:5173
```

`export_data.py` has to have run before the app – the app is built from what it
writes. `npm run build --prefix web` puts the finished site into `web/build`,
`npm run preview --prefix web` serves it.

Individual steps, if wanted:

```bash
python scripts/fetch_factsheet.py                       # only download the PDF
python scripts/fetch_factsheet.py --regions             # the five regional factsheets
python scripts/check_sources.py                         # fetch and read all six
python scripts/parse_factsheet.py <pdf>                 # only CSV + run.json
python scripts/export_data.py --out web/static          # only export
```

Before the first run `data/` is empty – the site then says so instead of showing an
error. The first as-of date is produced by the first run of "Fetch data".

## The site

* **Start page** – the newest as-of date: key figures, checks, the 15 largest
  positions as bars, the full country table.
* **As-of date bar** – every earlier as-of date is its own address
  (`/dates/20260731/`); the Δ column compares there with the respective predecessor,
  not with the newest state.
* **History** – target weight of the eight largest countries across all as-of dates.
* **Data** – all as-of dates with their CSVs to download.
* **Mix slider** – 50/50 by default, freely adjustable; the site recomputes
  immediately. The setting applies to every page, survives a change of the as-of date
  and is remembered in the browser. It does not touch the data: only the unweighted
  raw figures are in the repository.

### The site as a progressive web app

The page is installable and works offline. The service worker and the manifest are
generated by `vite-plugin-pwa` from the finished build, so the precache list is
whatever was actually written – nothing has to be kept in step by hand:

| File | Purpose |
|---|---|
| `manifest.webmanifest` | Name, colours, icons. All paths relative, because the page lives under `/<repository>/`. |
| `sw.js` | Service worker: precaches every file of the build – shell, data JSON and the CSVs – and serves it when offline. |
| `pwa/icon-*.png` | App icon: the bars of `favicon.svg`, as PNG in the sizes the manifest asks for. |

Installing works from the browser menu ("Install app" / "Add to Home Screen") once the
page is served over HTTPS – GitHub Pages does that. On the first visit the service
worker caches every page, icon and data file; after that every subpage opens without a
network, an as-of date address included. Navigations are answered from the precached
shell, which is why `/dates/20260731/` opens offline although its URL was never a file.

Nothing has to be invalidated by hand: the bundler gives every asset a hash in its
name, so a changed file is a different URL, and `registerType: 'autoUpdate'` fetches a
new service worker in the background and takes it into use on the next load.

Testing this locally needs a server – `file://` has no service worker:

```bash
npm run preview --prefix web    # then http://localhost:4173/
```

`localhost` counts as a secure origin, so registration works there too. In the
developer tools under *Application* the service worker, the manifest and the cache
content are visible; *Network → Offline* plus a reload is the test.

## Output

The **CSVs and `run_*.json` are versioned**: `export_data.py` builds the data of the
app from them, and `git log data/` is the rebalancing history. The factsheet PDF is a
throwaway file and is kept as an Actions artifact.

| File | Content |
|---|---|
| `data/ftse_country_weights_<date>.csv` | raw data per country: constituents, net mcap, both weights |
| `data/run_<date>.json` | totals and check results of the run |
| `data/factsheets/<issue>_<date>.pdf` | original factsheet (not versioned) |

## Checks

Checking the raw data is Python's second job, and the only place where a run can
fail. `parse_factsheet.py` exits with code 1 (and `update.py` then exports nothing) if
one of these checks fails:

1. Sum of the constituents of all countries == the `Totals` row (both indices, exact)
2. Sum of the net mcap of all countries == `Totals` (both indices, relative tolerance 1e-6)
3. Sum of the weight columns == 100.00 % (tolerance 0.5 pp; the Wgt columns are
   rounded to two decimals, which with ~48 countries means up to 0.24 pp of rounding
   noise)
4. Cross-check: the reported `Wgt %` == our own share `net mcap / total`
   (max. 0.02 pp deviation) – catches swapped or lost columns
5. At least 30 countries, no duplicates

That way both a layout change of the PDF and an incompletely parsed table show up
immediately, instead of silently producing a wrong portfolio. The results go into
`run_*.json` and appear on the site under "Checks" – for every earlier as-of date too.

## The three workflows

| File | Trigger | Does |
|---|---|---|
| `.github/workflows/pages.yml` | push to `main` | builds the site from `data/` and publishes it |
| `.github/workflows/data.yml` | manual | fetches the factsheet, checks it, opens a pull request |
| `.github/workflows/pr.yml` | pull request | builds the site and attaches it as an artifact |
| `.github/workflows/sources.yml` | push to `scripts/`, manual | fetches all six factsheets and checks they can be read |

### The monthly run

**Actions → "Fetch data" → Run workflow.** The run

1. downloads the current factsheet and **checks** it – if a check breaks, it ends
   here, with no branch and no pull request,
2. creates `data/<YYYYMMDD>`, commits the CSV and `run_*.json`, pushes,
3. builds the site and uploads it as the artifact **`site-<YYYYMMDD>`**,
4. opens the pull request and links the artifact in it.

You download the artifact, unpack it and look at the site:

```bash
npx serve preview          # or: python3 -m http.server -d preview
```

If it fits, you merge. The merge triggers `pages.yml` and the site is live – there is
no separate approval any more, **the merge is the approval**.

If the as-of date is already in the repository unchanged, the run ends without a
change. If a pull request for that as-of date is already open, it gets new commits
instead of a second pull request.

### Code changes

Every push to `main` publishes the site anew – even without new data, because it is
built completely from `data/` on every deploy. For pull requests with code changes,
`pr.yml` builds the same site as an artifact.

### One-off setup (in the repo settings, not possible in code)

1. **Settings → Pages → Source: "GitHub Actions"**
2. **Settings → Actions → General → Workflow permissions**: turn on "Allow GitHub
   Actions to create and approve pull requests" – otherwise `data.yml` cannot open a
   pull request.
3. Set **no** required reviewers on the `github-pages` environment; otherwise every
   deploy additionally waits for an approval.

## Cadence

The factsheet appears monthly at month end; the country GDP weights themselves are
only reset once a year in the March review, while the market capitalisation side moves
continuously. A monthly run is therefore entirely sufficient; in practice quarterly or
annual rebalancing is enough for implementation.

## Notes

* The FTSE weights are capped at 5 % per *single security* (annual review) – that does
  not affect the country level here, but it explains deviations from self-computed GDP
  shares.
* The universe only covers countries with investable FTSE All-World securities; GDP
  shares of countries without index representation drop out and are implicitly
  distributed over the rest.
* If the repository is public, so is the Pages site.
* Not investment advice; the PDFs are subject to the LSEG/FTSE terms of use.
