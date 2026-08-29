/** Die Mischung des Portfolios - der einzige Knopf, der etwas ausrechnet.
 *
 *  Sie gehoert der Ansicht, nicht den Daten: Python liefert nur die Rohgewichte des
 *  Factsheets, gemischt wird hier. Der Wert gilt fuer alle Seiten und ueberlebt den
 *  Wechsel des Stichtags; im Browser gemerkt, damit er auch den naechsten Besuch
 *  ueberlebt. */
export const DEFAULT_SPLIT = 0.5;

const KEY = 'portfolio.split';

function stored(): number {
	try {
		// Vorsicht: Number(null) ist 0, nicht NaN - ohne diese Abfrage stuende der
		// Regler beim ersten Besuch auf 0 statt auf der Standardmischung.
		const raw = localStorage.getItem(KEY);
		if (raw === null) return DEFAULT_SPLIT;
		const v = Number(raw);
		return Number.isFinite(v) && v >= 0 && v <= 1 ? v : DEFAULT_SPLIT;
	} catch {
		return DEFAULT_SPLIT; // privates Fenster, blockierte Site-Daten
	}
}

export const mix = $state({ split: typeof localStorage === 'undefined' ? DEFAULT_SPLIT : stored() });

export function remember(v: number) {
	try {
		localStorage.setItem(KEY, String(v));
	} catch {
		/* nicht schlimm - dann gilt der Wert nur fuer diesen Besuch */
	}
}
