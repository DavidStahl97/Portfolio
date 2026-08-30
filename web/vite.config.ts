import { sveltekit } from '@sveltejs/kit/vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';
import { defineConfig } from 'vite';

export default defineConfig({
	define: {
		// what the footer names: the repository of the site and when it was built
		__REPO__: JSON.stringify(process.env.GITHUB_REPOSITORY || 'DavidStahl97/Portfolio'),
		__BUILT__: JSON.stringify(process.env.BUILD_DATE || '')
	},
	plugins: [
		sveltekit(),
		SvelteKitPWA({
			registerType: 'autoUpdate',
			manifest: {
				name: 'Portfolio target weights',
				short_name: 'Portfolio',
				description:
					'Country target weights from 50 % market capitalisation and 50 % GDP, out of the FTSE factsheet.',
				lang: 'en',
				// relative throughout, because the site lives under /<repository>/
				start_url: './',
				scope: './',
				id: './',
				display: 'standalone',
				orientation: 'any',
				background_color: '#f9f9f7',
				theme_color: '#2a78d6',
				icons: [
					{ src: 'pwa/icon-192.png', sizes: '192x192', type: 'image/png', purpose: 'any' },
					{ src: 'pwa/icon-512.png', sizes: '512x512', type: 'image/png', purpose: 'any' },
					{
						src: 'pwa/icon-maskable-512.png',
						sizes: '512x512',
						type: 'image/png',
						purpose: 'maskable'
					}
				]
			},
			workbox: {
				// everything the bundler emitted plus what export_data.py wrote next to it -
				// the CSVs of the data page belong to the site as much as the JSON does
				globPatterns: ['**/*.{js,css,html,json,svg,png,csv,webmanifest}']
			}
		})
	]
});
