/** The portfolio mix - the only knob that computes anything.
 *
 *  It belongs to the view, not to the data: Python only delivers the raw weights of
 *  the factsheet, the blending happens here. The value applies to every page and
 *  survives a change of the as-of date; it is remembered in the browser so that it
 *  survives the next visit too. */
export const DEFAULT_SPLIT = 0.5;

const KEY = 'portfolio.split';

function stored(): number {
	try {
		// Careful: Number(null) is 0, not NaN - without this check the slider would
		// sit at 0 on the first visit instead of at the default mix.
		const raw = localStorage.getItem(KEY);
		if (raw === null) return DEFAULT_SPLIT;
		const v = Number(raw);
		return Number.isFinite(v) && v >= 0 && v <= 1 ? v : DEFAULT_SPLIT;
	} catch {
		return DEFAULT_SPLIT; // private window, blocked site data
	}
}

export const mix = $state({ split: typeof localStorage === 'undefined' ? DEFAULT_SPLIT : stored() });

export function remember(v: number) {
	try {
		localStorage.setItem(KEY, String(v));
	} catch {
		/* no harm - the value then only applies to this visit */
	}
}
