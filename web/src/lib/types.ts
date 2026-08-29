/** Der Datenvertrag mit scripts/export_data.py.
 *
 * Jedes Feld hier wird von diesem Skript geschrieben und von sonst nichts. Ein auf der
 * Python-Seite umbenanntes Feld, das hier nicht mitgezogen wird, ist genau der Fehler,
 * der sonst erst als leere Seite auffaellt - dafuer gibt es diese Datei. `npm run check`
 * laeuft in CI.
 */

/** Eine Pruefung aus parse_factsheet.py, so wie sie beim Lauf protokolliert wurde. */
export interface Check {
	name: string;
	passed: boolean;
	detail: string;
}

/** Ein Land zum Stichtag. Gewichte in Prozent, Marktkapitalisierung in Mio. USD. */
export interface Country {
	country: string;
	/** FTSE All-World: Gewicht nach Marktkapitalisierung */
	mcap: number;
	/** FTSE All-World GDP Weighted: Gewicht nach BIP */
	gdp: number;
	consMcap: number;
	consGdp: number;
	netMcap: number;
	netGdp: number;
}

export interface Totals {
	consGdp: number;
	consMcap: number;
	netGdp: number;
	netMcap: number;
}

/** Ein Stichtag mit allem, was der Report zeigt. Rohdaten des Factsheets plus das
 *  Protokoll ihrer Pruefung - gewichtet wird erst in der App. */
export interface Report {
	asOf: string;
	ok: boolean;
	totals: Totals;
	checks: Check[];
	countries: Country[];
}

export interface Stichtag {
	asOf: string;
	ok: boolean;
	countries: number;
}

export interface Index {
	/** Zeitpunkt des Datenexports, ISO-8601 */
	generated: string;
	/** neuester zuerst */
	stichtage: Stichtag[];
}
