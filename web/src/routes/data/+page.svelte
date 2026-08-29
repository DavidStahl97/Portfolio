<script lang="ts">
	import { base } from '$app/paths';
	import { day } from '$lib/format';
	import { stampOf } from '$lib/data';
	import Empty from '$lib/Empty.svelte';

	let { data } = $props();
</script>

<svelte:head>
	<title>Data</title>
</svelte:head>

{#if data.index.dates.length === 0}
	<Empty />
{:else}
	<h2>Data to download</h2>
<p class="lead">
	The checked raw data of the factsheet this site computes from: per country the
	weights by market capitalisation and by GDP. They are versioned in the
	repository.
</p>

<div class="card scroll">
	<table>
		<thead>
			<tr>
				<th>As of</th>
				<th>Countries</th>
				<th>Check</th>
				<th>Raw factsheet data</th>
			</tr>
		</thead>
		<tbody>
			{#each data.index.dates as s (s.asOf)}
				{@const stamp = stampOf(s.asOf)}
				<tr>
					<td><a href="{base}/dates/{stamp}/">{day(s.asOf)}</a></td>
					<td>{s.countries}</td>
					<td>
						<span class="status" class:ok={s.ok} class:fail={!s.ok}>
							<span class="dot"></span>{s.ok ? 'OK' : 'FAILED'}
						</span>
					</td>
					<td><a href="{base}/csv/ftse_country_weights_{stamp}.csv" download>CSV</a></td>
				</tr>
			{/each}
		</tbody>
	</table>
	</div>
{/if}

<style>
	.lead {
		color: var(--ink-2);
		margin: 0 0 16px;
		max-width: 62ch;
	}
</style>
