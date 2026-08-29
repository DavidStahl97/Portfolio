import { base } from '$app/paths';
import type { Report } from './types';

/** Laedt einen Stichtag. `stamp` ist YYYYMMDD, so heissen die Dateien. */
export async function loadReport(
	fetcher: typeof fetch,
	stamp: string
): Promise<Report | null> {
	const res = await fetcher(`${base}/data/${stamp}.json`);
	return res.ok ? ((await res.json()) as Report) : null;
}

/** "2026-07-31" -> "20260731" */
export const stampOf = (asOf: string) => asOf.replaceAll('-', '');
