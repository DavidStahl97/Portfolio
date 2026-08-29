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

## Ausgaben

| Datei | Inhalt |
|---|---|
| `data/factsheets/GDPWLDS_<YYYYMMDD>.pdf` | Original-Factsheet (Archiv/Nachvollziehbarkeit) |
| `data/ftse_country_weights_<YYYYMMDD>.csv` | Rohdaten je Land: Konstituenten, Net MCap, beide Gewichte |
| `data/target_weights_<YYYYMMDD>.csv` | Zielgewicht je Land, kumuliert, Δ zum Vormonat |

Die Δ-Spalte vergleicht mit dem zuletzt erzeugten `target_weights_*.csv` und
zeigt damit direkt den Rebalancing-Bedarf.

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
