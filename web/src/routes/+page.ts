import { loadReport, stampOf } from '$lib/data';
import type { PageLoad } from './$types';

// Die Startseite ist der neueste Stichtag.
export const load: PageLoad = async ({ fetch, parent }) => {
	const { index } = await parent();
	const [newest, before] = index.stichtage;
	if (!newest) return { report: null, previous: null };
	return {
		report: await loadReport(fetch, stampOf(newest.asOf)),
		previous: before ? await loadReport(fetch, stampOf(before.asOf)) : null
	};
};
