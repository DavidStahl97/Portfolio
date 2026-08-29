import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

// GitHub Pages does not serve from the domain root but from /<repository>/ - every
// generated URL has to carry that prefix. BASE_PATH wins, otherwise it comes from the
// repository the workflow runs in; locally it stays empty.
const fromRepo = process.env.GITHUB_REPOSITORY
	? '/' + process.env.GITHUB_REPOSITORY.split('/')[1]
	: '';
const base = (process.env.BASE_PATH ?? fromRepo).replace(/\/$/, '');

/** @type {import('@sveltejs/kit').Config} */
export default {
	preprocess: vitePreprocess(),
	kit: {
		// The start page is prerendered as an empty shell so that Pages answers it with
		// a real 200. An as-of date is a parameter and is reached through the 404.html -
		// that is how a single-page app is served on GitHub Pages.
		// BUILD_DIR allows a second build next to it (the version without a path prefix
		// that goes into the artifact for review).
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
