declare global {
	namespace App {}
	/** aus vite.config.ts: das Repository der Seite und das Baudatum */
	const __REPO__: string;
	const __BUILT__: string;
}

export {};
