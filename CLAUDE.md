# CLAUDE.md

Hinweise für Claude Code (claude.ai/code) zur Arbeit in diesem Repository.

@README.md

Das README erklärt Zweck, Datenquelle, Bedienung und die Workflows – es wird oben
importiert und hier nicht wiederholt. Was folgt, ist nur das, worüber man beim
Arbeiten im Code stolpert.

## Sprache

Prosa ist deutsch: Kommentare, Docstrings, CLI-Hilfe, Fehlermeldungen, alles
Sichtbare in der App, README und Commit-Nachrichten. Bezeichner sind englisch:
Funktions- und Variablennamen, CSV-Spalten (`as_of`, `net_mcap_usdm_gdp`),
JSON-Felder (`asOf`, `mcap`, `consGdp`). Ein deutscher Kommentar über einer
englisch benannten Funktion ist richtig so; ein deutscher Variablenname nicht.

In Commit-Nachrichten keine Umlaute (`ue`, `ae`, `oe`) – das Terminal, aus dem
sie geschrieben werden, verträgt sie nicht zuverlässig. In Dateien dagegen
schon: dort gehören richtige Umlaute hin.

## Die Trennlinie, um die es geht

**Python liest und prüft. Es rechnet nichts aus.** Was es erzeugt, sind die
Rohdaten des Factsheets und das Protokoll ihrer Prüfung. Die Gewichtung des
Portfolios steht an genau einer Stelle: `web/src/lib/weights.ts`.

Diese Grenze ist der Grund, warum es dieses Projekt in dieser Form gibt, und sie
wurde einmal bewusst hergestellt (`build_portfolio.py` und die
`target_weights_*.csv` sind deshalb gelöscht worden). Wenn eine Aufgabe dazu
verführt, in Python eine Mischung, ein Zielgewicht oder eine Kappung zu
berechnen, gehört sie in die App. Umgekehrt: Wenn in der App etwas aus dem PDF
gelesen oder geprüft werden soll, gehört es nach Python.

`export_data.py` steht auf der Python-Seite und **formt nur um** – jede Zahl, die
es schreibt, steht so schon in `data/`. Wenn dort eine Rechnung entsteht, ist das
ein Fehler.

## Was versioniert ist

| | |
|---|---|
| `data/ftse_country_weights_<date>.csv` | eine Zeile je Land, versioniert |
| `data/run_<date>.json` | `totals` aus dem PDF + die neun Prüfergebnisse, versioniert |
| `data/factsheets/*.pdf` | ignoriert, jederzeit neu ladbar |
| `web/static/data/`, `web/static/csv/` | ignoriert, von `export_data.py` erzeugt |
| `web/static/favicon.svg` | **Quelle**, versioniert – nicht mit dem Rest von `static/` ignorieren |
| `web/build/`, `preview/` | ignoriert |

`data/` ist die Wahrheit. Die Seite wird bei jedem Deploy komplett daraus neu
gebaut, auch jeder frühere Stichtag – deshalb wirkt eine Layoutänderung rückwirkend
auf die ganze Historie, und deshalb darf kein generiertes HTML im Repository
liegen.

## Prüfen

Es gibt keine Testsuite. Geprüft wird so:

1. **Python:** `python scripts/update.py --pdf data/factsheets/<datei>.pdf`
   läuft durch und meldet neun grüne Prüfungen, oder es bricht ab. Ein PDF liegt
   nach dem ersten Lauf unter `data/factsheets/`; ohne Netz ist `--pdf` der Weg.
2. **App:** `npm run check --prefix web` ist `svelte-check` gegen
   `web/src/lib/types.ts`. Das ist die einzige Stelle, an der ein in
   `export_data.py` umbenanntes Feld auffällt, bevor die Seite leer bleibt.
   CI führt es aus.
3. **Im Browser, und zwar wirklich.** Punkt 1 und 2 waren grün, als der Regler
   beim ersten Besuch auf 0 statt 50 stand und die Seite reines BIP-Gewicht
   zeigte. Was nicht angesehen wurde, gilt als ungeprüft.

Für Punkt 3 reicht `npm run dev --prefix web`. Wer den Produktionsstand ansehen
will, braucht einen Server, der sich wie GitHub Pages verhält – also unter
`/<repository>/` liefert und unbekannte Pfade mit der `404.html` beantwortet,
sonst sind die Stichtagsadressen nicht direkt aufrufbar:

```python
# unbekannte Pfade -> 404.html, so wie Pages es tut
import http.server, os, socketserver
ROOT = "/tmp/serve"        # darin: Portfolio/ = Inhalt von web/build
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

Der Build ohne Pfadpräfix (`BASE_PATH="" BUILD_DIR="../preview" npm run build`)
lässt sich dagegen einfach an der Wurzel servieren – das ist die Fassung, die im
Artefakt liegt.

Ein Stichtag reicht nicht, um alles zu sehen: Verlaufsdiagramm und Δ-Spalte
brauchen zwei. Zum Prüfen kann man Vormonate synthetisch erzeugen (CSV kopieren,
`as_of` ändern, Gewichte leicht streuen, `run_*.json` mitkopieren) – **danach
wieder löschen**, sie gehören nicht ins Repository.

## Der Parser

`ROW_RE` in `parse_factsheet.py` liest Zeilen der Form
`Australia 105 1,060,680 1.08 105 1,687,922 1.62`. Ändert FTSE das Layout, ist
das die Stelle. Die Ländernamen kommen aus dem PDF und sind englisch
(`Turkiye`, `Czech Rep.`) – nicht eindeutschen, sie sind der Schlüssel, über den
Stichtage verglichen werden.

Die neun Prüfungen sind kein Zierat, sie sind der halbe Zweck des Projekts. Zwei
Toleranzen sind gerechnet und nicht geraten:

* `WGT_TOL_PP = 0.5` – die Gewichtsspalten sind auf zwei Nachkommastellen
  gerundet, bei ~48 Ländern also bis zu 0,24 pp Rauschen.
* `MCAP_TOL_REL = 1e-6` – die Net-MCap-Summe weicht durch dieselbe Rundung um
  einzelne Millionen ab.

Die vierte Prüfung (`Wgt %` gegen `Net MCap / Total`) ist keine Wiederholung der
Summenprüfung: Sie fängt vertauschte oder verschobene Spalten ab, die eine reine
Summe überleben würden.

## Die App

SvelteKit 5 mit Runen, `adapter-static`, `ssr = false`. Vorbild und Ursprung des
Aufbaus ist `DavidStahl97/Komoot-Collection`.

* **`base`** kommt aus `GITHUB_REPOSITORY`, `BASE_PATH` gewinnt. Jeder Pfad in
  Markup und `fetch` braucht ihn – ein vergessenes `base` ist der Fehler, der
  lokal funktioniert und auf Pages 404 liefert.
* **`BUILD_DIR`** in `svelte.config.js` erlaubt den zweiten Build daneben
  (`preview`). `--outDir` tut das *nicht* – `adapter-static` schreibt nicht
  dorthin, wohin Vite baut.
* Die Startseite und `/daten/`, `/verlauf/` sind vorgerendert; ein Stichtag ist
  ein Parameter und wird über die `404.html` erreicht. Pages antwortet dabei mit
  Status 404 und die App rendert trotzdem – das ist die Konstruktion, kein Fehler.
* **Fehlende Daten sind ein Zustand, kein Fehler.** `+layout.ts` behandelt 404
  auf `data/index.json` als „noch keine Stichtage" und zeigt `Leer.svelte`. Ein
  geworfener Fehler wird in Produktionsbauten zu einem nackten „500 Internal
  Error" – das war schon einmal da.
* **Die Mischung** liegt in `split.svelte.ts` als gemeinsamer Zustand, Standard
  0,5, im `localStorage` gemerkt. Vorsicht: `Number(null)` ist `0`, nicht `NaN` –
  ohne Abfrage auf `null` steht der Regler beim ersten Besuch auf 0.
* Die Δ-Spalte rechnet den Vorstichtag mit **derselben** Mischung wie den
  aktuellen; sonst zeigt sie die Verstellung des Reglers als Marktbewegung.
* `let x = $state(irgendwas_reaktives)` erzeugt die Warnung
  `state_referenced_locally`. Entweder `untrack(...)` im Initialisierer oder den
  Wert ableiten.

## Diagramme

Die acht Serienfarben in `app.css` sind gegen Farbfehlsichtigkeit und Kontrast
geprüft und in dieser Reihenfolge zu vergeben – die Farbe gehört dem Land, nicht
seinem Rang. Weiter gilt:

* Eine Achse, nie zwei. Alle drei Serien im Balkendiagramm teilen sich eine Skala,
  das ist der Vergleich, um den es geht.
* Text trägt nie die Serienfarbe; die Farbe steckt im Balken oder im Schlüssel
  daneben.
* Δ-Werte sind **neutral** eingefärbt. Ein steigendes Ländergewicht ist weder gut
  noch schlecht, nur Rebalancing-Bedarf – Grün/Rot wäre eine Behauptung.
* Beschriftungen am Linienende werden auseinandergeschoben (`labels` in
  `History.svelte`), verschobene bekommen eine Führungslinie. Nicht abschneiden.

## Workflows

Drei Stück, mit klaren Zuständigkeiten:

| Datei | Auslöser | Tut |
|---|---|---|
| `pages.yml` | Push auf `main` | baut und veröffentlicht die Seite |
| `daten.yml` | von Hand | Factsheet holen, prüfen, Branch + Commit + Pull Request, Seite als Artefakt |
| `pr.yml` | Pull Request | baut die Seite und hängt sie als Artefakt an |

Fallen, die dabei schon zugeschnappt sind:

* Ein mit dem `GITHUB_TOKEN` geöffneter Pull Request **löst keine weiteren
  Workflows aus** – `pr.yml` läuft für die Datenläufe also nicht. Deshalb baut
  `daten.yml` die Seite selbst und verlinkt das Artefakt im Text des Pull
  Requests.
* `--force-with-lease` scheitert nach einem flachen Checkout mit „stale info",
  wenn der Branch nicht bekannt ist. Vorher `git fetch origin <branch> || true`.
* GitHub Pages kennt **eine** Site pro Repository. Vorschau-URLs je Pull Request
  gäbe es nur über einen `gh-pages`-Branch mit Unterordnern; bewusst nicht
  gemacht – die Vorschau ist das Artefakt.
* Nötige Repo-Einstellungen: Pages-Quelle „GitHub Actions"; unter
  *Actions → General* muss „Allow GitHub Actions to create and approve pull
  requests" an sein, sonst scheitert `gh pr create`. Am Environment
  `github-pages` dürfen **keine** Required reviewers stehen – der Merge ist die
  Freigabe.

## Umgebung

Die Kommandos gehören ins Repository-Wurzelverzeichnis; `npm` mit
`--prefix web`. Nach einem `cd web` in einem Befehl bleibt die Shell unter
Umständen dort – im nächsten Befehl absolute Pfade verwenden oder das
Verzeichnis prüfen. Das hat schon eine README ins falsche Verzeichnis geschrieben.
