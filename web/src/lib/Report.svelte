<script lang="ts">
	import Checks from '$lib/Checks.svelte';
	import CountryTable from '$lib/CountryTable.svelte';
	import PieCharts from '$lib/PieCharts.svelte';
	import SplitSlider from '$lib/SplitSlider.svelte';
	import Tiles from '$lib/Tiles.svelte';
	import WeightChart from '$lib/WeightChart.svelte';
	import { day } from '$lib/format';
	import { mix } from '$lib/split.svelte';
	import { activeShare, ranked, targets, viaRegions } from '$lib/weights';
	import type { Region, Report } from '$lib/types';

	let {
		report,
		previous,
		regions = []
	}: { report: Report; previous: Report | null; regions?: Region[] } = $props();

	// The mix applies to every page and stays put when the as-of date changes.
	const split = $derived(mix.split);
	const rows = $derived(ranked(report.countries, split));
	// The previous as-of date is computed with the same mix - otherwise the delta
	// column would show the movement of the slider instead of the movement of the market.
	const prev = $derived(previous ? targets(previous.countries, split) : new Map<string, number>());

	// What the five regional ETFs would actually deliver. They hit a region exactly and
	// then weight the countries inside it by market capitalisation, which is how an
	// index fund holds them - so the GDP half of the mix survives between the regions
	// and is undone within them. Without regions.json there is nothing to compare to.
	const viaEtf = $derived(
		regions.length ? viaRegions(report.countries, split, regions) : new Map<string, number>()
	);
	const active = $derived(regions.length ? activeShare(report.countries, split, regions) : null);
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

<Tiles {report} {rows} {active} />

<h2>Checks</h2>
<Checks checks={report.checks} />

<h2>Mix</h2>
<SplitSlider />

<h2>Market capitalisation, GDP and the mix</h2>
<PieCharts countries={report.countries} {split} {regions} />

<h2>Largest 15 positions</h2>
<WeightChart {rows} {prev} />

<h2>All countries</h2>
<CountryTable {rows} {prev} {viaEtf} />

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
