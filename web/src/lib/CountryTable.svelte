<script lang="ts">
	import { delta, pct } from '$lib/format';
	import type { RankedCountry } from '$lib/weights';

	let {
		rows,
		prev = new Map<string, number>()
	}: { rows: RankedCountry[]; prev?: Map<string, number> } = $props();

	const max = $derived(Math.max(...rows.map((r) => r.target), 0.01));
	const sum = $derived({
		mcap: rows.reduce((a, r) => a + r.mcap, 0),
		gdp: rows.reduce((a, r) => a + r.gdp, 0),
		target: rows.reduce((a, r) => a + r.target, 0)
	});
</script>

<div class="card scroll">
	<table>
		<thead>
			<tr>
				<th>Country</th>
				<th>MCap&thinsp;%</th>
				<th>GDP&thinsp;%</th>
				<th>Target&thinsp;%</th>
				<th>Cumulative&thinsp;%</th>
				<th>Δ previous date&thinsp;pp</th>
				<th></th>
			</tr>
		</thead>
		<tbody>
			{#each rows as r (r.country)}
				<tr>
					<td>{r.country}</td>
					<td>{pct(r.mcap)}</td>
					<td>{pct(r.gdp)}</td>
					<td><strong>{pct(r.target)}</strong></td>
					<td>{pct(r.cum)}</td>
					<!-- Deliberately coloured neutrally: a rising country weight is neither
					     good nor bad, only a need to rebalance. -->
					<td class:muted={!prev.has(r.country)}>
						{prev.has(r.country) ? delta(r.target - (prev.get(r.country) ?? 0)) : 'new'}
					</td>
					<td class="barcell">
						<span class="minibar" style:width="{(100 * r.target) / max}%"></span>
					</td>
				</tr>
			{/each}
		</tbody>
		<tfoot>
			<tr>
				<td>Total</td>
				<td>{pct(sum.mcap)}</td>
				<td>{pct(sum.gdp)}</td>
				<td>{pct(sum.target)}</td>
				<td></td><td></td><td></td>
			</tr>
		</tfoot>
	</table>
</div>

<style>
	tfoot td {
		font-weight: 600;
		border-top: 2px solid var(--baseline);
		border-bottom: none;
	}
	.barcell {
		width: 120px;
	}
	.minibar {
		display: inline-block;
		height: 8px;
		border-radius: 0 3px 3px 0;
		background: var(--s1);
		vertical-align: middle;
	}
</style>
