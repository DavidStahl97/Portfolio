<script lang="ts">
	import Report from '$lib/Report.svelte';
	import Leer from '$lib/Leer.svelte';
	let { data } = $props();
</script>

{#if data.report}
	<Report report={data.report} previous={data.previous} />
{:else}
	<Leer />
{/if}
