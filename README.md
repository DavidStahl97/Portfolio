# Portfolio: 50 % Marktkapitalisierung / 50 % BIP

Länder-Zielgewichte für ein Weltportfolio, das je zur Hälfte nach
Marktkapitalisierung und nach Bruttoinlandsprodukt (BIP, kaufkraftbereinigt)
gewichtet ist.

**Die Arbeitsteilung ist die Hauptsache an diesem Projekt:** Python holt die
Rohdaten aus dem Factsheet und prüft sie – mehr nicht. Gewichtet wird
ausschließlich in der App, im Browser, mit einem Regler. Damit gibt es keine
zweite Stelle, an der eine Mischung „festgelegt" wäre, und keine gerechneten
Zahlen im Repository, die zu den Rohdaten nicht mehr passen könnten.

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

Python **liest und prüft**; es rechnet nichts aus und schreibt weder Markup noch
Stylesheet noch Skript. Was es erzeugt, sind die Rohdaten des Factsheets und das
Protokoll ihrer Prüfung. Die App unter `web/` macht daraus die Seite – und sie
ist die einzige Stelle, an der gewichtet wird.

| Datei | Aufgabe |
|---|---|
| `scripts/fetch_factsheet.py` | lädt das aktuelle Factsheet-PDF |
| `scripts/parse_factsheet.py` | parst die Ländertabelle, prüft sie, schreibt CSV + `run_*.json` |
| `scripts/export_data.py` | formt die versionierten Daten nach `web/static/data/` um (ohne zu rechnen) |
| `scripts/update.py` | Gesamtlauf: laden → parsen → prüfen → exportieren |
| `web/` | die Single-Page-App (SvelteKit, `adapter-static`) |
| `web/src/lib/weights.ts` | **die einzige Stelle, an der das Portfolio gewichtet wird** |
| `web/src/lib/types.ts` | der Datenvertrag zu `export_data.py` – beide Seiten zusammen ändern |

## Bedienung

```bash
pip install -r requirements.txt

python scripts/update.py                 # Download → Prüfen → Export
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
python scripts/export_data.py --out web/static          # nur exportieren
```

Vor dem ersten Lauf ist `data/` leer – die Seite sagt das dann auch, statt einen
Fehler zu zeigen. Den ersten Stichtag erzeugt der erste Lauf von „Daten holen".

## Die Seite

* **Startseite** – der neueste Stichtag: Kennzahlen, Prüfungen, die 15 größten
  Positionen als Balken, die vollständige Ländertabelle.
* **Stichtagsleiste** – jeder frühere Stichtag ist eine eigene Adresse
  (`/stichtage/20260731/`); die Δ-Spalte vergleicht dort mit dem jeweiligen
  Vorgänger, nicht mit dem neuesten Stand.
* **Verlauf** – Zielgewicht der acht größten Länder über alle Stichtage.
* **Daten** – alle Stichtage mit ihren CSVs zum Herunterladen.
* **Mischungsregler** – Standard 50/50, frei verstellbar; die Seite rechnet
  sofort neu. Die Einstellung gilt für alle Seiten, überlebt den Wechsel des
  Stichtags und wird im Browser gemerkt. Sie berührt die Daten nicht: im
  Repository stehen nur die ungewichteten Rohzahlen.

## Ausgaben

Die **CSVs und `run_*.json` sind versioniert**: aus ihnen baut `export_data.py`
die Daten der App, und `git log data/` ist die Rebalancing-Historie. Das
Factsheet-PDF ist ein Wegwerfdatum und liegt als Actions-Artefakt.

| Datei | Inhalt |
|---|---|
| `data/ftse_country_weights_<date>.csv` | Rohdaten je Land: Konstituenten, Net MCap, beide Gewichte |
| `data/run_<date>.json` | Totals und Prüfergebnisse des Laufs |
| `data/factsheets/<issue>_<date>.pdf` | Original-Factsheet (nicht versioniert) |

## Prüfungen

Die Prüfung der Rohdaten ist die zweite Aufgabe von Python, und die einzige
Stelle, an der ein Lauf scheitern kann. `parse_factsheet.py` bricht mit
Exit-Code 1 ab (und `update.py` exportiert dann nichts), wenn eine dieser
Prüfungen fehlschlägt:

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

## Die drei Workflows

| Datei | Auslöser | Tut |
|---|---|---|
| `.github/workflows/pages.yml` | Push auf `main` | baut die Seite aus `data/` und veröffentlicht sie |
| `.github/workflows/daten.yml` | von Hand | holt das Factsheet, prüft es, öffnet einen Pull Request |
| `.github/workflows/pr.yml` | Pull Request | baut die Seite und hängt sie als Artefakt an |

### Der Monatslauf

**Actions → „Daten holen" → Run workflow.** Der Lauf

1. lädt das aktuelle Factsheet und **prüft** es – reißt eine Prüfung, endet er
   hier, ohne Branch und ohne Pull Request,
2. legt `daten/<YYYYMMDD>` an, committet CSV und `run_*.json`, pusht,
3. baut die Seite und lädt sie als Artefakt **`seite-<YYYYMMDD>`** hoch,
4. öffnet den Pull Request und verlinkt das Artefakt darin.

Du lädst das Artefakt herunter, entpackst es und siehst dir die Seite an:

```bash
npx serve preview          # oder: python3 -m http.server -d preview
```

Passt es, mergst du. Der Merge löst `pages.yml` aus und die Seite ist live – eine
gesonderte Freigabe gibt es nicht mehr, **der Merge ist die Freigabe**.

Liegt der Stichtag schon unverändert im Repository, endet der Lauf ohne Änderung.
Ist zu diesem Stichtag bereits ein Pull Request offen, bekommt er neue Commits
statt eines zweiten Pull Requests.

### Code-Änderungen

Jeder Push auf `main` veröffentlicht die Seite neu – auch ohne neue Daten, denn
sie wird bei jedem Deploy vollständig aus `data/` gebaut. Für Pull Requests mit
Code-Änderungen baut `pr.yml` dieselbe Seite als Artefakt.

### Einmalige Einrichtung (in den Repo-Settings, nicht im Code möglich)

1. **Settings → Pages → Source: „GitHub Actions"**
2. **Settings → Actions → General → Workflow permissions**: „Allow GitHub Actions
   to create and approve pull requests" einschalten – sonst kann `daten.yml`
   keinen Pull Request öffnen.
3. Am Environment `github-pages` **keine** Required reviewers eintragen; sonst
   wartet jeder Deploy zusätzlich auf eine Freigabe.

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
