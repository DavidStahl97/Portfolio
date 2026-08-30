import { base } from '$app/paths';
import type { Index, Regions } from '$lib/types';
import type { LayoutLoad } from './$types';

// A single-page app: nothing is rendered on a server, the pages without a parameter
// are prerendered as empty shells so that GitHub Pages answers them with a real 200.
export const ssr = false;
export const prerender = true;
export const trailingSlash = 'always';

/** The grouping into the five regional indices. Missing is a state, not an error: the
 *  charts then simply offer no region view. */
async function loadRegions(fetcher: typeof fetch): Promise<Regions> {
	const empty: Regions = { readFrom: '', regions: [] };
	try {
		const res = await fetcher(`${base}/data/regions.json`);
		return res.ok ? ((await res.json()) as Regions) : empty;
	} catch {
		return empty;
	}
}

export const load: LayoutLoad = async ({ fetch }) => {
	const regions = await loadRegions(fetch);
	const res = await fetch(`${base}/data/index.json`);
	// Before the first run there is no data yet. That is not an error but a state - the
	// pages then show what to do instead of a 500.
	if (res.status === 404) return { index: { generated: '', dates: [] } as Index, regions };
	if (!res.ok) throw new Error(`data/index.json could not be read (${res.status}).`);
	return { index: (await res.json()) as Index, regions };
};
