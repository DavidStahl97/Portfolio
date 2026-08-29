import { base } from '$app/paths';
import type { Index } from '$lib/types';
import type { LayoutLoad } from './$types';

// A single-page app: nothing is rendered on a server, the pages without a parameter
// are prerendered as empty shells so that GitHub Pages answers them with a real 200.
export const ssr = false;
export const prerender = true;
export const trailingSlash = 'always';

export const load: LayoutLoad = async ({ fetch }) => {
	const res = await fetch(`${base}/data/index.json`);
	// Before the first run there is no data yet. That is not an error but a state - the
	// pages then show what to do instead of a 500.
	if (res.status === 404) return { index: { generated: '', dates: [] } as Index };
	if (!res.ok) throw new Error(`data/index.json could not be read (${res.status}).`);
	return { index: (await res.json()) as Index };
};
