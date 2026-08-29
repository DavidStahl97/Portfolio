import { base } from '$app/paths';
import type { Index } from '$lib/types';
import type { LayoutLoad } from './$types';

// Eine Single-Page-App: nichts wird auf einem Server gerendert, die Seiten ohne
// Parameter werden als leere Huellen vorgerendert, damit GitHub Pages sie mit einer
// echten 200 beantwortet.
export const ssr = false;
export const prerender = true;
export const trailingSlash = 'always';

export const load: LayoutLoad = async ({ fetch }) => {
	const res = await fetch(`${base}/data/index.json`);
	if (!res.ok)
		throw new Error(
			`data/index.json fehlt (${res.status}) - erst \`python scripts/export_data.py\` laufen lassen.`
		);
	return { index: (await res.json()) as Index };
};
