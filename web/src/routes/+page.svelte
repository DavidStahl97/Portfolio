<script lang="ts">
	import Report from '$lib/Report.svelte';
	import Empty from '$lib/Empty.svelte';
	let { data } = $props();
</script>

{#if data.report}
	<Report report={data.report} previous={data.previous} regions={data.regions.regions} />
{:else}
	<Empty />
{/if}
