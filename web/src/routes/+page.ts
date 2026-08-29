import { loadReport, stampOf } from '$lib/data';
import type { PageLoad } from './$types';

// The start page is the newest as-of date.
export const load: PageLoad = async ({ fetch, parent }) => {
	const { index } = await parent();
	const [newest, before] = index.dates;
	if (!newest) return { report: null, previous: null };
	return {
		report: await loadReport(fetch, stampOf(newest.asOf)),
		previous: before ? await loadReport(fetch, stampOf(before.asOf)) : null
	};
};
