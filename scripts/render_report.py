"""Erzeugt einen eigenständigen HTML-Report zum aktuellen Factsheet-Lauf.

    python scripts/render_report.py data/factsheets/GDPWLDS_20260731.pdf --split 0.5

Der Report enthaelt die Pruefergebnisse, Kennzahlen, ein Balkendiagramm der
größten Positionen und die vollständige Ländertabelle. Keine externen
Ressourcen - eine Datei, offline lesbar, als CI-Artefakt geeignet.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parse_factsheet
from parse_factsheet import Factsheet

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
TOP_N = 15

CSS = """
:root {
  color-scheme: light;
  --plane:#f9f9f7; --surface:#fcfcfb;
  --ink:#0b0b0b; --ink-2:#52514e; --ink-muted:#898781;
  --grid:#e1e0d9; --baseline:#c3c2b7; --ring:rgba(11,11,11,0.10);
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a;
  --good:#0ca30c; --critical:#d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --plane:#0d0d0d; --surface:#1a1a19;
    --ink:#ffffff; --ink-2:#c3c2b7; --ink-muted:#898781;
    --grid:#2c2c2a; --baseline:#383835; --ring:rgba(255,255,255,0.10);
    --s1:#3987e5; --s2:#d95926; --s3:#199e70;
  }
}
* { box-sizing: border-box; }
body {
  margin:0; padding:32px 20px 64px; background:var(--plane); color:var(--ink);
  font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
}
.wrap { max-width:1080px; margin:0 auto; }
h1 { font-size:24px; margin:0 0 4px; letter-spacing:-0.01em; }
h2 { font-size:15px; margin:36px 0 12px; letter-spacing:-0.005em; }
.sub { color:var(--ink-2); margin:0 0 28px; }
.card {
  background:var(--surface); border:1px solid var(--ring); border-radius:10px;
  padding:18px 20px;
}
.tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px; }
.tile { background:var(--surface); border:1px solid var(--ring); border-radius:10px; padding:14px 16px; }
.tile .label { color:var(--ink-muted); font-size:12px; text-transform:uppercase; letter-spacing:.04em; }
.tile .value { font-size:26px; margin-top:4px; letter-spacing:-0.02em; }
.tile .note { color:var(--ink-2); font-size:12px; margin-top:2px; }
.status { display:inline-flex; align-items:center; gap:7px; font-weight:600; }
.dot { width:9px; height:9px; border-radius:50%; flex:none; }
.ok .dot { background:var(--good); } .fail .dot { background:var(--critical); }
.ok { color:var(--good); } .fail { color:var(--critical); }
table { border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; }
th, td { padding:7px 10px; text-align:right; border-bottom:1px solid var(--grid); white-space:nowrap; }
th { color:var(--ink-muted); font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:.04em; }
th:first-child, td:first-child { text-align:left; }
tbody tr:hover { background:color-mix(in srgb, var(--ink) 4%, transparent); }
tfoot td { font-weight:600; border-top:2px solid var(--baseline); border-bottom:none; }
.scroll { overflow-x:auto; }
.legend { display:flex; gap:18px; flex-wrap:wrap; margin:0 0 16px; color:var(--ink-2); font-size:13px; }
.legend span { display:inline-flex; align-items:center; gap:7px; }
.key { width:11px; height:11px; border-radius:3px; flex:none; }
.chart { display:grid; grid-template-columns:112px 1fr; gap:6px 12px; align-items:center; }
.chart .name { color:var(--ink-2); overflow:hidden; text-overflow:ellipsis; }
.group { display:flex; flex-direction:column; gap:2px; padding:5px 0; }
.row { display:flex; align-items:center; gap:8px; }
.bar { height:9px; border-radius:0 4px 4px 0; min-width:2px; flex:none; }
.val { font-size:11.5px; color:var(--ink-2); font-variant-numeric:tabular-nums; text-align:left; }
.minibar { display:inline-block; height:8px; border-radius:0 3px 3px 0; background:var(--s1); vertical-align:middle; }
.checks td:first-child { white-space:normal; }
.foot { color:var(--ink-muted); font-size:12px; margin-top:36px; }
.foot a { color:var(--s1); }
.stichtage {
  display:flex; align-items:center; gap:6px; flex-wrap:wrap;
  margin:0 0 28px; padding:10px 14px; background:var(--surface);
  border:1px solid var(--ring); border-radius:10px;
}
.stichtage .navlabel {
  color:var(--ink-muted); font-size:12px; text-transform:uppercase;
  letter-spacing:.04em; margin-right:4px;
}
.stichtage a {
  padding:3px 9px; border-radius:6px; text-decoration:none;
  color:var(--s1); font-variant-numeric:tabular-nums;
}
.stichtage a:hover { background:color-mix(in srgb, var(--ink) 6%, transparent); }
.stichtage a.current {
  color:var(--ink); font-weight:600;
  background:color-mix(in srgb, var(--ink) 8%, transparent);
}
.muted { color:var(--ink-muted); }
"""


def _fmt(x: float, d: int = 2) -> str:
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",")


def _esc(s: str) -> str:
    return html.escape(str(s))


def build(fs: Factsheet, split: float, prev: dict[str, float],
          nav: list[tuple[str, str, bool]] | None = None,
          data_prefix: str | None = None) -> str:
    """nav: (Beschriftung, href, ist_aktuelle_Seite) je Stichtag.
    data_prefix: Pfad zu den CSVs relativ zur erzeugten Datei; None = keine
    Downloadlinks (lokaler Einzelreport)."""
    rows = sorted(fs.rows, key=lambda r: r.country)
    blended = {r.country: split * r.wgt_mc + (1 - split) * r.wgt_gdp for r in rows}
    total = sum(blended.values())
    target = {c: 100.0 * w / total for c, w in blended.items()}
    by_w = sorted(rows, key=lambda r: -target[r.country])
    top10 = sum(target[r.country] for r in by_w[:10])
    scale = max(
        max(r.wgt_mc for r in by_w[:TOP_N]),
        max(r.wgt_gdp for r in by_w[:TOP_N]),
        max(target[r.country] for r in by_w[:TOP_N]),
    )

    ok = fs.ok
    st = ("ok", "Alle Prüfungen bestanden") if ok else ("fail", "Prüfung fehlgeschlagen")

    out: list[str] = []
    a = out.append
    a(f"<!doctype html><html lang=de><meta charset=utf-8>"
      f"<meta name=viewport content='width=device-width,initial-scale=1'>"
      f"<title>Portfolio-Report {fs.as_of:%Y-%m-%d}</title><style>{CSS}</style><div class=wrap>")
    a(f"<h1>Portfolio-Zielgewichte &middot; {fs.as_of:%d.%m.%Y}</h1>")
    a(f"<p class=sub>FTSE All-World GDP Weighted Factsheet &middot; "
      f"{split:.0%} Marktkapitalisierung / {1 - split:.0%} BIP &middot; "
      f"erzeugt {dt.datetime.now():%d.%m.%Y %H:%M} UTC</p>")

    if nav:
        a("<nav class=stichtage><span class=navlabel>Stichtag</span>")
        for label, href, current in nav:
            a(f"<a class=current>{_esc(label)}</a>" if current
              else f"<a href='{_esc(href)}'>{_esc(label)}</a>")
        a("</nav>")

    # --- Kennzahlen ---
    usa = target.get("USA")
    a("<div class=tiles>")
    a(f"<div class=tile><div class=label>Stichtag</div><div class=value>{fs.as_of:%d.%m.%Y}</div>"
      f"<div class=note>{fs.totals.cons_gdp:,} Konstituenten</div></div>".replace(",", " "))
    a(f"<div class=tile><div class=label>Länder</div><div class=value>{len(rows)}</div>"
      f"<div class=note>Top 10 = {_fmt(top10)}&thinsp;%</div></div>")
    if usa is not None:
        a(f"<div class=tile><div class=label>USA-Zielgewicht</div><div class=value>{_fmt(usa)}&thinsp;%</div>"
          f"<div class=note>MCap {_fmt(next(r.wgt_mc for r in rows if r.country=='USA'))}&thinsp;% "
          f"/ BIP {_fmt(next(r.wgt_gdp for r in rows if r.country=='USA'))}&thinsp;%</div></div>")
    a(f"<div class=tile><div class=label>Datenprüfung</div>"
      f"<div class='value status {st[0]}' style='font-size:17px'><span class=dot></span>"
      f"{'bestanden' if ok else 'fehlgeschlagen'}</div>"
      f"<div class=note>{len(fs.checks)} Prüfungen</div></div>")
    a("</div>")

    # --- Prüfungen ---
    a("<h2>Prüfungen</h2><div class='card scroll'><table class=checks><thead><tr>"
      "<th>Prüfung</th><th>Ergebnis</th><th>Status</th></tr></thead><tbody>")
    for name, passed, detail in fs.checks:
        cls = "ok" if passed else "fail"
        a(f"<tr><td>{_esc(name)}</td><td>{_esc(detail)}</td>"
          f"<td><span class='status {cls}'><span class=dot></span>"
          f"{'OK' if passed else 'FEHLER'}</span></td></tr>")
    a("</tbody></table></div>")

    # --- Diagramm ---
    a(f"<h2>Größte {TOP_N} Positionen</h2>")
    a("<div class=card>")
    a(f"<p class=legend>"
      f"<span><i class=key style='background:var(--s1)'></i>Marktkapitalisierung&thinsp;%</span>"
      f"<span><i class=key style='background:var(--s2)'></i>BIP&thinsp;%</span>"
      f"<span><i class=key style='background:var(--s3)'></i>Zielgewicht&thinsp;%</span></p>")
    a("<div class=chart>")
    for r in by_w[:TOP_N]:
        a(f"<div class=name title='{_esc(r.country)}'>{_esc(r.country)}</div><div class=group>")
        for val, var in ((r.wgt_mc, "--s1"), (r.wgt_gdp, "--s2"), (target[r.country], "--s3")):
            pct = 100.0 * val / scale
            a(f"<div class=row><div class=bar style='width:calc((100% - 46px) * "
              f"{pct / 100:.4f});background:var({var})'></div>"
              f"<div class=val>{_fmt(val)}</div></div>")
        a("</div>")
    a("</div></div>")

    # --- Tabelle ---
    a("<h2>Alle Länder</h2><div class='card scroll'><table><thead><tr>"
      "<th>Land</th><th>MCap&thinsp;%</th><th>BIP&thinsp;%</th><th>Ziel&thinsp;%</th>"
      "<th>Kumuliert&thinsp;%</th><th>&Delta; Vorlauf&thinsp;pp</th><th></th>"
      "</tr></thead><tbody>")
    cum = 0.0
    tmax = max(target.values())
    for r in by_w:
        tw = target[r.country]
        cum += tw
        p = prev.get(r.country)
        if p is None:
            delta = "<span class=muted>neu</span>"
        elif abs(tw - p) < 0.005:
            delta = "<span class=muted>&ndash;</span>"
        else:
            # Bewusst neutral eingefaerbt: ein steigendes Laendergewicht ist
            # weder gut noch schlecht, nur Rebalancing-Bedarf.
            delta = f"{tw - p:+.2f}".replace(".", ",")
        a(f"<tr><td>{_esc(r.country)}</td><td>{_fmt(r.wgt_mc)}</td><td>{_fmt(r.wgt_gdp)}</td>"
          f"<td><strong>{_fmt(tw)}</strong></td><td>{_fmt(cum)}</td><td>{delta}</td>"
          f"<td style='width:120px'><span class=minibar style='width:{100*tw/tmax:.1f}%'></span></td></tr>")
    a(f"<tr><td>Summe</td><td>{_fmt(sum(r.wgt_mc for r in rows))}</td>"
      f"<td>{_fmt(sum(r.wgt_gdp for r in rows))}</td><td>{_fmt(sum(target.values()))}</td>"
      f"<td></td><td></td><td></td></tr>")
    a("</tbody></table></div>")

    if data_prefix is not None:
        a(f"<p class=foot>Daten zu diesem Stichtag: "
          f"<a href='{data_prefix}target_weights_{fs.as_of:%Y%m%d}.csv'>Zielgewichte</a> &middot; "
          f"<a href='{data_prefix}ftse_country_weights_{fs.as_of:%Y%m%d}.csv'>Rohdaten des Factsheets</a>"
          f" &middot; <a href='{data_prefix}run_{fs.as_of:%Y%m%d}.json'>Prüfprotokoll</a></p>")
    a("<p class=foot>Quelle: FTSE Russell, FTSE All-World GDP Weighted Index Factsheet. "
      "Die &Delta;-Spalte vergleicht mit dem zuletzt erzeugten target_weights_*.csv. "
      "Keine Anlageberatung.</p>")
    a("</div></html>")
    return "\n".join(out)


def load_prev(as_of: dt.date) -> dict[str, float]:
    files = [f for f in sorted(DATA.glob("target_weights_*.csv"))
             if f.name != f"target_weights_{as_of:%Y%m%d}.csv"]
    if not files:
        return {}
    with files[-1].open(encoding="utf-8") as fh:
        return {r["country"]: float(r["target_weight_pct"]) for r in csv.DictReader(fh)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--split", type=float, default=0.5)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--data-prefix", default=None,
                    help="Pfad zu den CSVs relativ zur Ausgabe, z.B. 'data/'")
    args = ap.parse_args()

    fs = parse_factsheet.parse(args.pdf)
    out = args.out or DATA / f"report_{fs.as_of:%Y%m%d}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(fs, args.split, load_prev(fs.as_of),
                         data_prefix=args.data_prefix), encoding="utf-8")
    print(f"Report: {out}")
    return 0 if fs.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
