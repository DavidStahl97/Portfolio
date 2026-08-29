import type { Country } from './types';

/** Target weight per country: split * market capitalisation + (1 - split) * GDP,
 *  normalised to 100 %.
 *
 *  This is the only place in the project where the portfolio is weighted. Python only
 *  delivers the checked raw weights of the factsheet. */
export function targets(countries: Country[], split: number): Map<string, number> {
	const blended = countries.map((c) => [c.country, split * c.mcap + (1 - split) * c.gdp] as const);
	const sum = blended.reduce((a, [, w]) => a + w, 0);
	return new Map(blended.map(([name, w]) => [name, sum > 0 ? (100 * w) / sum : 0]));
}

/** Descending by target weight, with the cumulative share. */
export function ranked(countries: Country[], split: number) {
	const t = targets(countries, split);
	const rows = [...countries].sort((a, b) => (t.get(b.country) ?? 0) - (t.get(a.country) ?? 0));
	let cum = 0;
	return rows.map((c) => {
		const target = t.get(c.country) ?? 0;
		cum += target;
		return { ...c, target, cum };
	});
}

export type RankedCountry = ReturnType<typeof ranked>[number];
