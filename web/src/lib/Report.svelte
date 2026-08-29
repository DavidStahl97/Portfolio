<script lang="ts">
	import Checks from '$lib/Checks.svelte';
	import CountryTable from '$lib/CountryTable.svelte';
	import SplitSlider from '$lib/SplitSlider.svelte';
	import Tiles from '$lib/Tiles.svelte';
	import WeightChart from '$lib/WeightChart.svelte';
	import { day } from '$lib/format';
	import { mix } from '$lib/split.svelte';
	import { ranked, targets } from '$lib/weights';
	import type { Report } from '$lib/types';

	let { report, previous }: { report: Report; previous: Report | null } = $props();

	// The mix applies to every page and stays put when the as-of date changes.
	const split = $derived(mix.split);
	const rows = $derived(ranked(report.countries, split));
	// The previous as-of date is computed with the same mix - otherwise the delta
	// column would show the movement of the slider instead of the movement of the market.
	const prev = $derived(previous ? targets(previous.countries, split) : new Map<string, number>());
</script>

<svelte:head>
	<title>Target weights {day(report.asOf)}</title>
</svelte:head>

{#if !report.ok}
	<p class="warn">
		<span class="status fail"><span class="dot"></span>Check failed</span> — the figures of
		this as-of date are not dependable. What broke is listed below.
	</p>
{/if}

<Tiles {report} {rows} />

<h2>Checks</h2>
<Checks checks={report.checks} />

<h2>Mix</h2>
<SplitSlider />

<h2>Largest 15 positions</h2>
<WeightChart {rows} {prev} />

<h2>All countries</h2>
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
