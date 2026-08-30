import type { Country, Region } from './types';

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

/** A set of countries shown as one slice: one country, one regional index, or the
 *  remainder. `name` identifies it, `label` names it, `title` says the long form. */
export interface Group {
	name: string;
	label: string;
	title: string;
	countries: string[];
}

/** Everything the five regional indices do not cover. Israel is the case: developed,
 *  but in FTSE's Middle East & Africa region, so in none of the five ETFs. */
export const UNCOVERED = 'uncovered';

/** The largest `n` countries by target weight, each its own group, and the rest.
 *
 *  Which countries get their own slice is decided by the mixed weighting, so charts
 *  drawn from these groups are cut identically and comparable slice by slice. */
export function countryGroups(countries: Country[], split: number, n: number): Group[] {
	const rows = ranked(countries, split);
	const named = rows.slice(0, n).map((c) => ({
		name: c.country,
		label: c.country,
		title: c.country,
		countries: [c.country]
	}));
	const rest = rows.slice(n).map((c) => c.country);
	return rest.length
		? [...named, { name: 'rest', label: 'Other countries', title: 'Other countries', countries: rest }]
		: named;
}

/** The five regional indices as groups, in the order of the file, and one group for
 *  the countries none of them covers.
 *
 *  The order is deliberately not by weight: the colour belongs to the region, and a
 *  region must not change colour because the slider moved. */
export function regionGroups(countries: Country[], regions: Region[]): Group[] {
	const present = new Set(countries.map((c) => c.country));
	const groups = regions.map((r) => ({
		name: r.issue,
		label: r.etf ? `${r.index.replace(/^FTSE /, '')} (${r.etf})` : r.index,
		title: r.index,
		countries: r.countries.filter((c) => present.has(c))
	}));

	const covered = new Set(groups.flatMap((g) => g.countries));
	const rest = [...present].filter((c) => !covered.has(c)).sort();
	return rest.length
		? [
				...groups,
				{
					name: UNCOVERED,
					label: 'In none of the five',
					title: `In none of the five indices: ${rest.join(', ')}`,
					countries: rest
				}
			]
		: groups;
}

/** The share of every group, in percent, under one way of valuing a country.
 *
 *  Normalised to 100 %: the weight columns of the factsheet are rounded to two
 *  decimals, so their sum over ~48 countries is only nearly 100. A country that is in
 *  no group is still in the denominator - dropping it would quietly inflate the rest. */
export function shares(
	countries: Country[],
	groups: Group[],
	value: (c: Country) => number
): { name: string; share: number }[] {
	const by = new Map(countries.map((c) => [c.country, value(c)]));
	const sum = countries.reduce((a, c) => a + value(c), 0) || 1;
	return groups.map((g) => ({
		name: g.name,
		share: (100 * g.countries.reduce((a, c) => a + (by.get(c) ?? 0), 0)) / sum
	}));
}

/** What the five ETFs actually deliver, per country.
 *
 *  The five regional indices are weighted by market capitalisation inside themselves -
 *  that is what an index fund tracking them holds. Buying them at the target weight of
 *  their region therefore hits the region exactly, but leaves every country within it
 *  at its market weight. The GDP half of the mix survives between regions and is undone
 *  inside them.
 *
 *  Countries in none of the five keep their target weight: they are not bought through
 *  a regional ETF at all, so there is nothing to distort. */
export function viaRegions(
	countries: Country[],
	split: number,
	regions: Region[]
): Map<string, number> {
	const target = targets(countries, split);
	const mcap = new Map(countries.map((c) => [c.country, c.mcap]));
	const out = new Map<string, number>();

	for (const group of regionGroups(countries, regions)) {
		const weight = group.countries.reduce((a, c) => a + (target.get(c) ?? 0), 0);
		if (group.name === UNCOVERED) {
			for (const c of group.countries) out.set(c, target.get(c) ?? 0);
			continue;
		}
		const inside = group.countries.reduce((a, c) => a + (mcap.get(c) ?? 0), 0);
		for (const c of group.countries) {
			out.set(c, inside > 0 ? (weight * (mcap.get(c) ?? 0)) / inside : 0);
		}
	}
	return out;
}

/** How much of the portfolio sits in a different country than intended, in percent.
 *
 *  Half the sum of the absolute deviations - the usual way to read it, because every
 *  overweight is somebody else's underweight and the plain sum counts both. */
export function activeShare(
	countries: Country[],
	split: number,
	regions: Region[]
): number {
	const target = targets(countries, split);
	const actual = viaRegions(countries, split, regions);
	let sum = 0;
	for (const c of countries) {
		sum += Math.abs((actual.get(c.country) ?? 0) - (target.get(c.country) ?? 0));
	}
	return sum / 2;
}
