import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

// GitHub Pages liefert nicht von der Domainwurzel, sondern von /<repository>/ - jede
// erzeugte URL muss diesen Praefix tragen. BASE_PATH gewinnt, sonst kommt er aus dem
// Repository, in dem der Workflow laeuft; lokal bleibt er leer.
const fromRepo = process.env.GITHUB_REPOSITORY
	? '/' + process.env.GITHUB_REPOSITORY.split('/')[1]
	: '';
const base = (process.env.BASE_PATH ?? fromRepo).replace(/\/$/, '');

/** @type {import('@sveltejs/kit').Config} */
export default {
	preprocess: vitePreprocess(),
	kit: {
		// Die Startseite wird als leere Huelle vorgerendert, damit Pages sie mit einer
		// echten 200 beantwortet. Ein Stichtag ist ein Parameter und wird ueber die
		// 404.html erreicht - so bedient man eine Single-Page-App auf GitHub Pages.
		// BUILD_DIR erlaubt einen zweiten Build daneben (die Fassung ohne Pfadpraefix,
		// die im Artefakt zum Durchsehen liegt).
		adapter: adapter({
			pages: process.env.BUILD_DIR ?? 'build',
			assets: process.env.BUILD_DIR ?? 'build',
			fallback: '404.html',
			precompress: false,
			strict: false
		}),
		paths: { base, relative: false }
	}
};
