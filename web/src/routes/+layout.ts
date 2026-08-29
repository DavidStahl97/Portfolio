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
	// Vor dem ersten Lauf gibt es noch keine Daten. Das ist kein Fehler, sondern ein
	// Zustand - die Seiten zeigen dann, was zu tun ist, statt einer 500.
	if (res.status === 404) return { index: { generated: '', stichtage: [] } as Index };
	if (!res.ok) throw new Error(`data/index.json nicht lesbar (${res.status}).`);
	return { index: (await res.json()) as Index };
};
