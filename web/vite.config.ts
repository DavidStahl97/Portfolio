import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	define: {
		// was die Fusszeile nennt: das Repository der Seite und wann sie gebaut wurde
		__REPO__: JSON.stringify(process.env.GITHUB_REPOSITORY || 'DavidStahl97/Portfolio'),
		__BUILT__: JSON.stringify(process.env.BUILD_DATE || '')
	},
	plugins: [sveltekit()]
});
