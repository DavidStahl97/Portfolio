# Portfolio: 50 % Marktkapitalisierung / 50 % BIP

Länder-Zielgewichte für ein Weltportfolio, das je zur Hälfte nach
Marktkapitalisierung und nach Bruttoinlandsprodukt (BIP, kaufkraftbereinigt)
gewichtet ist – als Zeitreihe im Repository und als Seite im Browser.

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

## Was wo lebt

Python lädt, prüft und rechnet; es schreibt weder Markup noch Stylesheet noch
Skript. Alles, was es erzeugt, sind Daten – und die App unter `web/` macht daraus
die Seite. Damit entstehen neue Diagramme im Browser aus vorhandenen Daten,
ohne dass ein Lauf nötig wäre.

| Datei | Aufgabe |
|---|---|
| `scripts/fetch_factsheet.py` | lädt das aktuelle Factsheet-PDF |
| `scripts/parse_factsheet.py` | parst die Ländertabelle, prüft sie, schreibt CSV + `run_*.json` |
| `scripts/build_portfolio.py` | 50/50-Mix (Split frei wählbar), Δ zum Vorlauf |
| `scripts/export_data.py` | schreibt aus den versionierten Daten `web/static/data/` |
| `scripts/update.py` | Gesamtlauf: laden → parsen → prüfen → rechnen → exportieren |
| `web/` | die Single-Page-App (SvelteKit, `adapter-static`) |
| `web/src/lib/types.ts` | der Datenvertrag zu `export_data.py` – beide Seiten zusammen ändern |

## Bedienung

```bash
pip install -r requirements.txt

python scripts/update.py                 # Download → Prüfen → Zielgewichte → Export
python scripts/update.py --split 0.6     # 60 % MCap / 40 % BIP
python scripts/update.py --pdf data/factsheets/GDPWLDS_20260731.pdf   # ohne Netz

npm ci --prefix web
npm run dev --prefix web                 # http://localhost:5173
```

`export_data.py` muss vor der App gelaufen sein – sie wird aus dem gebaut, was
es schreibt. `npm run build --prefix web` legt die fertige Seite in `web/build`,
`npm run preview --prefix web` serviert sie.

Einzelschritte, falls gewünscht:

```bash
python scripts/fetch_factsheet.py                       # nur PDF laden
python scripts/parse_factsheet.py <pdf>                 # nur CSV + run.json
python scripts/build_portfolio.py --split 0.5           # nur Gewichte rechnen
python scripts/build_portfolio.py --min-weight 0.5      # Kleinstpositionen kappen
python scripts/export_data.py --out web/static          # nur exportieren
```

## Die Seite

* **Startseite** – der neueste Stichtag: Kennzahlen, Prüfungen, die 15 größten
  Positionen als Balken, die vollständige Ländertabelle.
* **Stichtagsleiste** – jeder frühere Stichtag ist eine eigene Adresse
  (`/stichtage/20260731/`); die Δ-Spalte vergleicht dort mit dem jeweiligen
  Vorgänger, nicht mit dem neuesten Stand.
* **Verlauf** – Zielgewicht der acht größten Länder über alle Stichtage.
* **Daten** – alle Stichtage mit ihren CSVs zum Herunterladen.
* **Mischungsregler** – der Split ist im Browser verstellbar, die Seite rechnet
  sofort neu. Die versionierten CSVs bleiben davon unberührt: sie tragen die
  Mischung, mit der der Lauf gerechnet hat.

## Ausgaben

Die **CSVs und `run_*.json` sind versioniert**: aus ihnen baut `export_data.py`
die Daten der App, und `git log data/` ist die Rebalancing-Historie. Das
Factsheet-PDF ist ein Wegwerfdatum und liegt als Actions-Artefakt.

| Datei | Inhalt |
|---|---|
| `data/ftse_country_weights_<date>.csv` | Rohdaten je Land: Konstituenten, Net MCap, beide Gewichte |
| `data/target_weights_<date>.csv` | Zielgewicht je Land, kumuliert, Δ zum Vorlauf |
| `data/run_<date>.json` | Totals und Prüfergebnisse des Laufs |
| `data/factsheets/<issue>_<date>.pdf` | Original-Factsheet (nicht versioniert) |

## Prüfungen

`parse_factsheet.py` bricht mit Exit-Code 1 ab (und `update.py` rechnet dann
nicht weiter), wenn eine dieser Prüfungen fehlschlägt:

1. Summe der Konstituenten aller Länder == `Totals`-Zeile (beide Indizes, exakt)
2. Summe der Net MCap aller Länder == `Totals` (beide Indizes, rel. Toleranz 1e-6)
3. Summe der Gewichtsspalten == 100,00 % (Toleranz 0,5 pp; die Wgt-Spalten sind
   auf zwei Nachkommastellen gerundet, bei ~48 Ländern also bis zu 0,24 pp
   Rundungsrauschen)
4. Gegenprobe: gemeldetes `Wgt %` == eigener Anteil `Net MCap / Total`
   (max. 0,02 pp Abweichung) – fängt vertauschte oder verlorene Spalten ab
5. Mindestens 30 Länder, keine Dubletten

Damit fällt sowohl ein Layout-Wechsel des PDFs als auch eine unvollständig
geparste Tabelle sofort auf, statt still ein falsches Portfolio zu erzeugen. Die
Ergebnisse wandern in `run_*.json` und stehen auf der Seite unter „Prüfungen" –
auch für jeden früheren Stichtag.

## GitHub Action mit Freigabe

**Actions → „Portfolio-Report" → Run workflow.** Eingaben: `split`, `issue`,
`commit`, `publish`. Der Workflow besteht aus zwei Jobs:

1. **`report`** – lädt, prüft, rechnet, committet die Daten, baut die App und
   legt sie als Artefakt ab. Läuft ohne Freigabe durch.
2. **`deploy`** – veröffentlicht die Seite auf GitHub Pages.

Dazwischen sitzt das Environment `github-pages`. Sind dort **Required
reviewers** hinterlegt, bleibt `deploy` stehen: im Actions-Lauf erscheint
„Review deployments" → „Approve and deploy". Bis dahin ist auf der Seite
weiterhin der vorige Stand zu sehen. Den neuen siehst du vorher aus dem Artefakt
desselben Laufs – es enthält den Ordner `preview`, dieselbe Seite ohne
Pfadpräfix:

```bash
npx serve preview          # oder: python3 -m http.server -d preview
```

Bei grünem Lauf committet die Action die aktualisierten CSVs und `run_*.json`
zurück auf den Branch, auf dem sie lief (per Eingabe `commit` abschaltbar).
Ändert sich inhaltlich nichts, entsteht auch kein Commit; bei fehlgeschlagener
Prüfung wird nichts committet, damit die Zeitreihe sauber bleibt. Mit
`publish = false` läuft `deploy` gar nicht erst an.

Ein monatlicher `schedule`-Trigger liegt auskommentiert im Workflow bereit.

### Einmalige Einrichtung (in den Repo-Settings, nicht im Code möglich)

1. **Settings → Pages → Source: „GitHub Actions"**
2. **Settings → Environments → `github-pages` → Required reviewers**: dich
   selbst eintragen. Ohne diesen Schritt deployt der Job **ohne** Nachfrage.
3. Optional unter *Deployment branches* den Branch einschränken, von dem aus
   veröffentlicht werden darf.

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
* Ist das Repository öffentlich, ist es auch die Pages-Seite.
* Keine Anlageberatung; die PDFs unterliegen den LSEG/FTSE-Nutzungsbedingungen.
