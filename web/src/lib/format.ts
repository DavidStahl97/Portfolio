const num = new Intl.NumberFormat('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const int = new Intl.NumberFormat('de-DE');
const sign = new Intl.NumberFormat('de-DE', {
	minimumFractionDigits: 2,
	maximumFractionDigits: 2,
	signDisplay: 'always'
});

export const pct = (v: number) => num.format(v);
export const count = (v: number) => int.format(v);
export const delta = (v: number) => (Math.abs(v) < 0.005 ? '–' : sign.format(v));

/** "2026-07-31" -> "31.07.2026" */
export const day = (iso: string) =>
	new Date(iso + 'T00:00:00Z').toLocaleDateString('de-DE', {
		timeZone: 'UTC',
		day: '2-digit',
		month: '2-digit',
		year: 'numeric'
	});

/** "2026-07-31" -> "07/2026", die Beschriftung in der Stichtagsleiste */
export const month = (iso: string) => `${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
