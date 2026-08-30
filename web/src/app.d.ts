/// <reference types="vite-plugin-pwa/info" />
/// <reference types="vite-plugin-pwa/client" />

declare global {
	namespace App {}
	/** from vite.config.ts: the repository of the site and the build date */
	const __REPO__: string;
	const __BUILT__: string;
}

export {};
