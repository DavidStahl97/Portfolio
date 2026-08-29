import { error } from '@sveltejs/kit';
import { loadReport, stampOf } from '$lib/data';
import type { PageLoad } from './$types';

// Ein Stichtag ist ein Parameter, diese Seite wird also nicht vorgerendert - GitHub
// Pages erreicht sie ueber die 404.html, die adapter-static schreibt.
export const prerender = false;

export const load: PageLoad = async ({ fetch, params, parent }) => {
	const { index } = await parent();
	const i = index.stichtage.findIndex((s) => stampOf(s.asOf) === params.date);
	if (i < 0) error(404, `Kein Stichtag "${params.date}".`);
	const before = index.stichtage[i + 1]; // die Liste ist absteigend sortiert
	return {
		report: await loadReport(fetch, params.date),
		previous: before ? await loadReport(fetch, stampOf(before.asOf)) : null
	};
};
