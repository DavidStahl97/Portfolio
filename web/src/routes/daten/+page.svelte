<script lang="ts">
	import { base } from '$app/paths';
	import { day } from '$lib/format';
	import { stampOf } from '$lib/data';
	import Leer from '$lib/Leer.svelte';

	let { data } = $props();
</script>

<svelte:head>
	<title>Daten</title>
</svelte:head>

{#if data.index.stichtage.length === 0}
	<Leer />
{:else}
	<h2>Daten zum Herunterladen</h2>
<p class="lead">
	Die geprüften Rohdaten des Factsheets, aus denen diese Seite rechnet: je Land die
	Gewichte nach Marktkapitalisierung und nach BIP. Sie liegen versioniert im
	Repository.
</p>

<div class="card scroll">
	<table>
		<thead>
			<tr>
				<th>Stichtag</th>
				<th>Länder</th>
				<th>Prüfung</th>
				<th>Rohdaten des Factsheets</th>
			</tr>
		</thead>
		<tbody>
			{#each data.index.stichtage as s (s.asOf)}
				{@const stamp = stampOf(s.asOf)}
				<tr>
					<td><a href="{base}/stichtage/{stamp}/">{day(s.asOf)}</a></td>
					<td>{s.countries}</td>
					<td>
						<span class="status" class:ok={s.ok} class:fail={!s.ok}>
							<span class="dot"></span>{s.ok ? 'OK' : 'FEHLER'}
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
