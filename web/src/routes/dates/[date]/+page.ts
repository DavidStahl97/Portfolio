import { error } from '@sveltejs/kit';
import { loadReport, stampOf } from '$lib/data';
import type { PageLoad } from './$types';

// An as-of date is a parameter, so this page is not prerendered - GitHub Pages reaches
// it through the 404.html that adapter-static writes.
export const prerender = false;

export const load: PageLoad = async ({ fetch, params, parent }) => {
	const { index } = await parent();
	const i = index.dates.findIndex((s) => stampOf(s.asOf) === params.date);
	if (i < 0) error(404, `No as-of date "${params.date}".`);
	const before = index.dates[i + 1]; // the list is sorted descending
	return {
		report: await loadReport(fetch, params.date),
		previous: before ? await loadReport(fetch, stampOf(before.asOf)) : null
	};
};
