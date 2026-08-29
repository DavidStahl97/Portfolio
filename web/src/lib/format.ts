const num = new Intl.NumberFormat('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const int = new Intl.NumberFormat('en-GB');
const sign = new Intl.NumberFormat('en-GB', {
	minimumFractionDigits: 2,
	maximumFractionDigits: 2,
	signDisplay: 'always'
});

export const pct = (v: number) => num.format(v);
export const count = (v: number) => int.format(v);
export const delta = (v: number) => (Math.abs(v) < 0.005 ? '–' : sign.format(v));

/** "2026-07-31" -> "31 Jul 2026" */
export const day = (iso: string) =>
	new Date(iso + 'T00:00:00Z').toLocaleDateString('en-GB', {
		timeZone: 'UTC',
		day: '2-digit',
		month: 'short',
		year: 'numeric'
	});

/** "2026-07-31" -> "07/2026", the label in the as-of date bar */
export const month = (iso: string) => `${iso.slice(5, 7)}/${iso.slice(0, 4)}`;
