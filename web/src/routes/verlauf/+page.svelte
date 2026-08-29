<script lang="ts">
	import History from '$lib/History.svelte';
	import SplitSlider from '$lib/SplitSlider.svelte';
	import { mix } from '$lib/split.svelte';

	let { data } = $props();

	const split = $derived(mix.split);
</script>

<svelte:head>
	<title>Verlauf der Zielgewichte</title>
</svelte:head>

<h2>Mischung</h2>
<SplitSlider />

<h2>Zielgewicht über die Stichtage</h2>
{#if data.reports.length > 1}
	<History reports={data.reports} {split} />
{:else}
	<div class="card"><p class="muted">Dafür braucht es mindestens zwei Stichtage.</p></div>
{/if}
