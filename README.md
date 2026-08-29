# Portfolio: 50 % Marktkapitalisierung / 50 % BIP

Länder-Zielgewichte für ein Weltportfolio, das je zur Hälfte nach
Marktkapitalisierung und nach Bruttoinlandsprodukt (BIP, kaufkraftbereinigt)
gewichtet ist.

## Datenquelle

Ein einziges Dokument liefert beide Hälften: das monatliche Factsheet des
**FTSE All-World GDP Weighted Index** (IssueName `GDPWLDS`). Die Seite
„Country/Market Breakdown" stellt pro Land nebeneinander

* `FTSE All-World GDP Weighted` → BIP-Gewicht (IMF-PPP-Prognosen, jährliches
  Review im März), und
* `FTSE All-World` → Marktkapitalisierungs-Gewicht (Free Float).

Beides ist also identisch abgegrenzt (gleiches Universum, gleicher Stichtag) –
genau das, was ein 50/50-Mix braucht. Das PDF ist frei abrufbar, der
Download-Endpunkt liefert immer die neueste Ausgabe.

## Bedienung

```bash
pip install -r requirements.txt

python scripts/update.py                 # Download → Parsen → Prüfen → Zielgewichte
python scripts/update.py --split 0.6     # 60 % MCap / 40 % BIP
python scripts/update.py --pdf data/factsheets/GDPWLDS_20260731.pdf   # ohne Netz
```

Einzelschritte, falls gewünscht:

```bash
python scripts/fetch_factsheet.py                       # nur PDF laden
python scripts/parse_factsheet.py <pdf>                 # nur CSV erzeugen
python scripts/build_portfolio.py --split 0.5           # nur Gewichte rechnen
python scripts/build_portfolio.py --min-weight 0.5      # Kleinstpositionen kappen,
                                                        # Rest auf 100 % normieren
```

## GitHub Action (manuell anstoßen)

**Actions → „Portfolio-Report" → Run workflow.** Zwei optionale Eingaben:
`split` (Default `0.5`) und `issue` (Default `GDPWLDS`).

Der Lauf macht genau das, was `scripts/update.py` lokal tut – Factsheet laden,
parsen, prüfen, Zielgewichte rechnen – und hängt alles als Artefakt
**`portfolio-report-<YYYYMMDD>`** an den Lauf:

* `report_<YYYYMMDD>.html` – der Report (eine Datei, keine externen Ressourcen,
  hell/dunkel), mit Prüfstatus, Kennzahlen, Balkendiagramm der 15 größten
  Positionen und vollständiger Ländertabelle inkl. Δ zum Vorlauf
* die beiden CSVs und das Original-PDF
* `run.log`, dessen Inhalt zusätzlich in der Job-Summary steht

Schlägt eine Prüfung fehl, **endet der Job rot, der Report wird aber trotzdem
erzeugt und hochgeladen** – er ist dann genau das Dokument, das zeigt, welche
Prüfung gerissen ist. Zielgewichte werden in dem Fall nicht berechnet.

Ein monatlicher `schedule`-Trigger liegt auskommentiert im Workflow bereit.

## GitHub Pages mit Freigabe

Der Workflow besteht aus zwei Jobs:

1. **`report`** – lädt, prüft, rechnet, committet die CSVs und legt alles als
   Artefakt ab. Läuft ohne Freigabe durch.
2. **`deploy`** – veröffentlicht die Seite auf GitHub Pages.

Die Seite zeigt **alle Stichtage**, nicht nur den aktuellen:

```
index.html            neuester Report
reports/<date>.html   je Stichtag, über die Leiste oben erreichbar
data/                 CSVs und Prüfprotokolle zum Direktabruf
```

`scripts/build_site.py` baut jeden Report bei jedem Lauf aus den versionierten
Daten neu – `ftse_country_weights_<date>.csv` plus `run_<date>.json` (Totals und
Prüfergebnisse). Das PDF wird dafür nicht gebraucht. So wächst die Historie auf
der Seite automatisch mit, ohne dass generiertes HTML im Repo liegt. Die
Δ-Spalte jedes Reports vergleicht mit seinem jeweiligen Vorgänger, nicht mit
dem neuesten Stand.

Lokal ansehen:

```bash
python scripts/build_site.py --out site
python -m http.server -d site 8000
```

Dazwischen sitzt das Environment `github-pages`. Sind dort **Required
reviewers** hinterlegt, bleibt `deploy` stehen und wartet: im Actions-Lauf
erscheint „Review deployments" → „Approve and deploy". Bis dahin ist auf der
Seite weiterhin der vorige Report zu sehen. Den neuen prüfst du vorher aus dem
Artefakt desselben Laufs (`report_<YYYYMMDD>.html`, eine Datei, lokal
öffnenbar). Lehnst du ab, passiert nichts – die Seite bleibt, wie sie war.

Mit `publish = false` beim Start läuft der Job `deploy` gar nicht erst an.

### Einmalige Einrichtung (in den Repo-Settings, nicht im Code möglich)

1. **Settings → Pages → Source: „GitHub Actions"**
2. **Settings → Environments → `github-pages` → Required reviewers**: dich
   selbst eintragen. Ohne diesen Schritt deployt der Job **ohne** Nachfrage.
3. Optional unter *Deployment branches* den Branch einschränken, von dem aus
   veröffentlicht werden darf.

## Ausgaben

Die **CSVs und `run_*.json` sind versioniert**: sie sind die Zeitreihe der Zielgewichte, `git log
data/` ist damit die Rebalancing-Historie. Das Factsheet-PDF und der HTML-Report
sind Wegwerfdaten (bei jedem Lauf reproduzierbar) und stehen in `.gitignore` –
aus der Action kommen sie als Artefakt am jeweiligen Lauf.

| Datei | Inhalt |
|---|---|
| `data/factsheets/GDPWLDS_<YYYYMMDD>.pdf` | Original-Factsheet (Archiv/Nachvollziehbarkeit) |
| `data/ftse_country_weights_<YYYYMMDD>.csv` | Rohdaten je Land: Konstituenten, Net MCap, beide Gewichte |
| `data/target_weights_<YYYYMMDD>.csv` | Zielgewicht je Land, kumuliert, Δ zum Vormonat |
| `data/run_<YYYYMMDD>.json` | Totals und Prüfergebnisse des Laufs (versioniert, für den Neubau der Historie) |
| `data/report_<YYYYMMDD>.html` | Report zum Lauf (auch einzeln: `scripts/render_report.py <pdf>`) |

Die Δ-Spalte vergleicht mit dem zuletzt erzeugten `target_weights_*.csv` und
zeigt damit direkt den Rebalancing-Bedarf – lokal wie in der Action, da die CSVs
im Repo liegen und beim Checkout mitkommen. Sie ist bewusst neutral eingefärbt:
ein steigendes Ländergewicht ist weder gut noch schlecht.

## Prüfungen

`parse_factsheet.py` bricht mit Exit-Code 1 ab (und `update.py` erzeugt dann
keine Zielgewichte), wenn eine dieser Prüfungen fehlschlägt:

1. Summe der Konstituenten aller Länder == `Totals`-Zeile (beide Indizes, exakt)
2. Summe der Net MCap aller Länder == `Totals` (beide Indizes, rel. Toleranz 1e-6)
3. Summe der Gewichtsspalten == 100,00 % (Toleranz 0,5 pp; die Wgt-Spalten sind
   auf zwei Nachkommastellen gerundet, bei ~48 Ländern also bis zu 0,24 pp
   Rundungsrauschen)
4. Gegenprobe: gemeldetes `Wgt %` == eigener Anteil `Net MCap / Total`
   (max. 0,02 pp Abweichung) – fängt vertauschte oder verlorene Spalten ab
5. Mindestens 30 Länder, keine Dubletten

Damit fällt sowohl ein Layout-Wechsel des PDFs als auch eine unvollständig
geparste Tabelle sofort auf, statt still ein falsches Portfolio zu erzeugen.

## Aktueller Stand (31.07.2026, 50/50)

| Land | MCap % | BIP % | Ziel % |
|---|---:|---:|---:|
| USA | 61,66 | 17,80 | 39,73 |
| China | 2,82 | 22,98 | 12,90 |
| Indien | 1,63 | 11,60 | 6,62 |
| Japan | 5,95 | 3,65 | 4,80 |
| UK | 3,28 | 2,38 | 2,83 |

Vollständig in `data/target_weights_20260731.csv`.

## Turnus

Das Factsheet erscheint monatlich zum Monatsende; die Länder-BIP-Gewichte
selbst werden nur einmal jährlich im März-Review neu gesetzt, die
Marktkapitalisierungs-Seite bewegt sich laufend. Ein monatlicher Lauf reicht
also vollkommen; für die Umsetzung genügt in der Praxis ein quartalsweises
oder jährliches Rebalancing.

## Hinweise

* Die FTSE-Gewichte sind auf 5 % je *Einzelwert* gekappt (Annual Review) – das
  betrifft die Länderebene hier nicht, erklärt aber Abweichungen zu selbst
  gerechneten BIP-Anteilen.
* Das Universum umfasst nur Länder mit investierbaren FTSE-All-World-Titeln;
  BIP-Anteile von Ländern ohne Index-Vertretung fallen heraus und werden
  implizit auf die übrigen verteilt.
* Keine Anlageberatung; die PDFs unterliegen den LSEG/FTSE-Nutzungsbedingungen.
