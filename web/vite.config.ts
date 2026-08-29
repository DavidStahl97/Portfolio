import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	define: {
		// what the footer names: the repository of the site and when it was built
		__REPO__: JSON.stringify(process.env.GITHUB_REPOSITORY || 'DavidStahl97/Portfolio'),
		__BUILT__: JSON.stringify(process.env.BUILD_DATE || '')
	},
	plugins: [sveltekit()]
});
