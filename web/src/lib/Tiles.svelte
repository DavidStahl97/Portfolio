<script lang="ts">
	import { count, day, pct } from '$lib/format';
	import type { RankedCountry } from '$lib/weights';
	import type { Report } from '$lib/types';

	let { report, rows }: { report: Report; rows: RankedCountry[] } = $props();

	const top10 = $derived(rows.slice(0, 10).reduce((a, r) => a + r.target, 0));
	const usa = $derived(rows.find((r) => r.country === 'USA'));
</script>

<div class="tiles">
	<div class="tile">
		<div class="label">Stichtag</div>
		<div class="value">{day(report.asOf)}</div>
		<div class="note">{count(report.totals.consGdp)} Konstituenten</div>
	</div>
	<div class="tile">
		<div class="label">Länder</div>
		<div class="value">{report.countries.length}</div>
		<div class="note">Top 10 = {pct(top10)} %</div>
	</div>
	{#if usa}
		<div class="tile">
			<div class="label">USA-Zielgewicht</div>
			<div class="value">{pct(usa.target)} %</div>
			<div class="note">MCap {pct(usa.mcap)} % / BIP {pct(usa.gdp)} %</div>
		</div>
	{/if}
	<div class="tile">
		<div class="label">Datenprüfung</div>
		<div class="value small status" class:ok={report.ok} class:fail={!report.ok}>
			<span class="dot"></span>{report.ok ? 'bestanden' : 'fehlgeschlagen'}
		</div>
		<div class="note">{report.checks.length} Prüfungen</div>
	</div>
</div>

<style>
	.tiles {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
		gap: 12px;
	}
	.tile {
		background: var(--surface);
		border: 1px solid var(--ring);
		border-radius: 10px;
		padding: 14px 16px;
	}
	.label {
		color: var(--ink-muted);
		font-size: 12px;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.value {
		font-size: 26px;
		margin-top: 4px;
		letter-spacing: -0.02em;
	}
	.value.small {
		font-size: 17px;
	}
	.note {
		color: var(--ink-2);
		font-size: 12px;
		margin-top: 2px;
	}
</style>
