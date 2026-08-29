/** The data contract with scripts/export_data.py.
 *
 * Every field here is written by that script and by nothing else. A field renamed on
 * the Python side that is not changed along here is exactly the mistake that would
 * otherwise only show up as an empty page - that is what this file is for.
 * `npm run check` runs in CI.
 */

/** One check from parse_factsheet.py, as it was recorded during the run. */
export interface Check {
	name: string;
	passed: boolean;
	detail: string;
}

/** One country at an as-of date. Weights in percent, market cap in USD millions. */
export interface Country {
	country: string;
	/** FTSE All-World: weight by market capitalisation */
	mcap: number;
	/** FTSE All-World GDP Weighted: weight by GDP */
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

/** One as-of date with everything the report shows. The raw factsheet data plus the
 *  record of their checks - the weighting happens in the app. */
export interface Report {
	asOf: string;
	ok: boolean;
	totals: Totals;
	checks: Check[];
	countries: Country[];
}

export interface AsOfDate {
	asOf: string;
	ok: boolean;
	countries: number;
}

export interface Index {
	/** time of the data export, ISO 8601 */
	generated: string;
	/** newest first */
	dates: AsOfDate[];
}
