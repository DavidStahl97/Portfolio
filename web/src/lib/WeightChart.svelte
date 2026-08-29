<script lang="ts">
	import { pct } from '$lib/format';
	import type { RankedCountry } from '$lib/weights';

	let {
		rows,
		top = 15,
		prev = new Map<string, number>()
	}: { rows: RankedCountry[]; top?: number; prev?: Map<string, number> } = $props();

	const shown = $derived(rows.slice(0, top));
	// All three series share one scale - two axes would lose exactly the comparability
	// this chart is about.
	const scale = $derived(
		Math.max(...shown.flatMap((r) => [r.mcap, r.gdp, r.target]), 0.01)
	);
	let hovered = $state<string | null>(null);

	const series = [
		{ key: 'mcap', label: 'Market capitalisation', color: 'var(--s1)' },
		{ key: 'gdp', label: 'GDP', color: 'var(--s2)' },
		{ key: 'target', label: 'Target weight', color: 'var(--s3)' }
	] as const;
</script>

<div class="card">
	<p class="legend">
		{#each series as s (s.key)}
			<span><i class="key" style:background={s.color}></i>{s.label}&thinsp;%</span>
		{/each}
	</p>

	<div class="chart">
		{#each shown as r (r.country)}
			{@const d = prev.has(r.country) ? r.target - (prev.get(r.country) ?? 0) : null}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				class="name"
				class:hot={hovered === r.country}
				onmouseenter={() => (hovered = r.country)}
				onmouseleave={() => (hovered = null)}
			>
				{r.country}
			</div>
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				class="group"
				class:hot={hovered === r.country}
				onmouseenter={() => (hovered = r.country)}
				onmouseleave={() => (hovered = null)}
			>
				{#each series as s (s.key)}
					<div class="row">
						<div
							class="bar"
							style:width="calc((100% - 46px) * {r[s.key] / scale})"
							style:background={s.color}
						></div>
						<div class="val">{pct(r[s.key])}</div>
					</div>
				{/each}
				{#if hovered === r.country}
					<div class="tip">
						{r.country}: target {pct(r.target)} %, cumulative {pct(r.cum)} %{d !== null
							? `, ${d >= 0 ? '+' : ''}${pct(d)} pp vs. the previous date`
							: ''}
					</div>
				{/if}
			</div>
		{/each}
	</div>
</div>

<style>
	.legend {
		display: flex;
		gap: 18px;
		flex-wrap: wrap;
		margin: 0 0 16px;
		color: var(--ink-2);
		font-size: 13px;
	}
	.legend span {
		display: inline-flex;
		align-items: center;
		gap: 7px;
	}
	.key {
		width: 11px;
		height: 11px;
		border-radius: 3px;
		flex: none;
	}
	.chart {
		display: grid;
		grid-template-columns: 112px 1fr;
		gap: 6px 12px;
		align-items: center;
	}
	.name {
		color: var(--ink-2);
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.name.hot {
		color: var(--ink);
	}
	.group {
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding: 5px 0;
		position: relative;
	}
	.row {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.bar {
		height: 9px;
		border-radius: 0 4px 4px 0;
		min-width: 2px;
		flex: none;
	}
	.val {
		font-size: 11.5px;
		color: var(--ink-2);
		font-variant-numeric: tabular-nums;
	}
	.tip {
		position: absolute;
		right: 0;
		top: -6px;
		background: var(--surface);
		border: 1px solid var(--ring);
		border-radius: 7px;
		padding: 4px 9px;
		font-size: 12px;
		color: var(--ink-2);
		white-space: nowrap;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
		pointer-events: none;
		z-index: 2;
	}
</style>
