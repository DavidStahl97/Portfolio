<script lang="ts">
	import { untrack } from 'svelte';
	import History from '$lib/History.svelte';
	import SplitSlider from '$lib/SplitSlider.svelte';

	let { data } = $props();

	const configured = $derived(data.reports.at(-1)?.split ?? 0.5);
	let split = $state(untrack(() => data.reports.at(-1)?.split ?? 0.5));
	$effect(() => {
		split = configured;
	});
</script>

<svelte:head>
	<title>Verlauf der Zielgewichte</title>
</svelte:head>

<h2>Mischung</h2>
<SplitSlider bind:split {configured} />

<h2>Zielgewicht über die Stichtage</h2>
{#if data.reports.length > 1}
	<History reports={data.reports} {split} />
{:else}
	<div class="card"><p class="muted">Dafür braucht es mindestens zwei Stichtage.</p></div>
{/if}
