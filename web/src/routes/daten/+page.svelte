<script lang="ts">
	import { base } from '$app/paths';
	import { day } from '$lib/format';
	import { stampOf } from '$lib/data';

	let { data } = $props();
</script>

<svelte:head>
	<title>Daten</title>
</svelte:head>

<h2>Daten zum Herunterladen</h2>
<p class="lead">
	Dieselben Dateien, aus denen diese Seite gebaut ist. Sie liegen versioniert im
	Repository, jede Zeile ist ein Land.
</p>

<div class="card scroll">
	<table>
		<thead>
			<tr>
				<th>Stichtag</th>
				<th>Mischung</th>
				<th>Länder</th>
				<th>Prüfung</th>
				<th>Zielgewichte</th>
				<th>Rohdaten</th>
			</tr>
		</thead>
		<tbody>
			{#each data.index.stichtage as s (s.asOf)}
				{@const stamp = stampOf(s.asOf)}
				<tr>
					<td><a href="{base}/stichtage/{stamp}/">{day(s.asOf)}</a></td>
					<td>{Math.round(s.split * 100)} / {Math.round((1 - s.split) * 100)}</td>
					<td>{s.countries}</td>
					<td>
						<span class="status" class:ok={s.ok} class:fail={!s.ok}>
							<span class="dot"></span>{s.ok ? 'OK' : 'FEHLER'}
						</span>
					</td>
					<td><a href="{base}/csv/target_weights_{stamp}.csv" download>CSV</a></td>
					<td><a href="{base}/csv/ftse_country_weights_{stamp}.csv" download>CSV</a></td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	.lead {
		color: var(--ink-2);
		margin: 0 0 16px;
		max-width: 62ch;
	}
</style>
