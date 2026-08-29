<script lang="ts">
	import History from '$lib/History.svelte';
	import SplitSlider from '$lib/SplitSlider.svelte';
	import { mix } from '$lib/split.svelte';

	let { data } = $props();

	const split = $derived(mix.split);
</script>

<svelte:head>
	<title>History of the target weights</title>
</svelte:head>

<h2>Mix</h2>
<SplitSlider />

<h2>Target weight across the as-of dates</h2>
{#if data.reports.length > 1}
	<History reports={data.reports} {split} />
{:else}
	<div class="card"><p class="muted">This needs at least two as-of dates.</p></div>
{/if}
