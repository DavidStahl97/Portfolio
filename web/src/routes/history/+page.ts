import { loadReport, stampOf } from '$lib/data';
import type { Report } from '$lib/types';
import type { PageLoad } from './$types';

// The history needs every as-of date - one file each, ~10 kB.
export const load: PageLoad = async ({ fetch, parent }) => {
	const { index } = await parent();
	const reports = await Promise.all(index.dates.map((s) => loadReport(fetch, stampOf(s.asOf))));
	return { reports: reports.filter((r): r is Report => r !== null).reverse() }; // old -> new
};
