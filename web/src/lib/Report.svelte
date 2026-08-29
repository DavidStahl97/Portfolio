<script lang="ts">
	import { untrack } from 'svelte';
	import Checks from '$lib/Checks.svelte';
	import CountryTable from '$lib/CountryTable.svelte';
	import SplitSlider from '$lib/SplitSlider.svelte';
	import Tiles from '$lib/Tiles.svelte';
	import WeightChart from '$lib/WeightChart.svelte';
	import { day } from '$lib/format';
	import { ranked, targets } from '$lib/weights';
	import type { Report } from '$lib/types';

	let { report, previous }: { report: Report; previous: Report | null } = $props();

	// Der Split ist verstellbar: die Seite rechnet neu, ohne dass ein Lauf noetig waere.
	// Startwert ohne Abhaengigkeit lesen, das Nachziehen macht der Effekt darunter.
	let split = $state(untrack(() => report.split));
	$effect(() => {
		split = report.split; // beim Wechsel des Stichtags zurueck auf dessen Mischung
	});

	const rows = $derived(ranked(report.countries, split));
	// Der Vorstichtag wird mit derselben Mischung gerechnet - sonst zeigte die
	// Delta-Spalte die Verstellung des Reglers statt der Bewegung im Markt.
	const prev = $derived(previous ? targets(previous.countries, split) : new Map<string, number>());
</script>

<svelte:head>
	<title>Zielgewichte {day(report.asOf)}</title>
</svelte:head>

{#if !report.ok}
	<p class="warn">
		<span class="status fail"><span class="dot"></span>Prüfung fehlgeschlagen</span> — die Zahlen
		dieses Stichtags sind nicht belastbar. Was gerissen ist, steht unten.
	</p>
{/if}

<Tiles {report} {rows} />

<h2>Prüfungen</h2>
<Checks checks={report.checks} />

<h2>Mischung</h2>
<SplitSlider bind:split configured={report.split} />

<h2>Größte 15 Positionen</h2>
<WeightChart {rows} {prev} />

<h2>Alle Länder</h2>
<CountryTable {rows} {prev} />

<style>
	.warn {
		background: var(--surface);
		border: 1px solid var(--ring);
		border-left: 3px solid var(--critical);
		border-radius: 10px;
		padding: 12px 16px;
		color: var(--ink-2);
	}
</style>
