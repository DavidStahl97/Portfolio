<script lang="ts">
	import { pct } from '$lib/format';
	import { targets } from '$lib/weights';
	import type { Country } from '$lib/types';

	let {
		countries,
		split,
		top = 8
	}: { countries: Country[]; split: number; top?: number } = $props();

	// The same eight series colours as everywhere else, assigned in this order: the
	// colour belongs to the country and is the same in all three charts, which is the
	// whole point of showing them next to each other.
	const COLORS = ['--s1', '--s2', '--s3', '--s4', '--s5', '--s6', '--s7', '--s8'];
	const REST = 'Other countries';

	const R = 52;
	const HOLE = 30;
	const BOX = 124; // -62 .. 62

	const target = $derived(targets(countries, split));

	/** Which countries get their own slice is decided by the mixed weighting - so all
	 *  three charts are cut the same way and are comparable slice by slice. */
	const names = $derived(
		[...countries]
			.sort((a, b) => (target.get(b.country) ?? 0) - (target.get(a.country) ?? 0))
			.slice(0, top)
			.map((c) => c.country)
	);
	const color = $derived(
		new Map(names.map((n, i) => [n, `var(${COLORS[i % COLORS.length]})`]))
	);

	/** One chart: the named countries in the order of the legend, the remainder
	 *  collected into one slice. Normalised to 100 % - the weight columns of the
	 *  factsheet are rounded, so their sum is only nearly 100. */
	function slices(value: (c: Country) => number) {
		const sum = countries.reduce((a, c) => a + value(c), 0) || 1;
		const named = names.map((n) => {
			const c = countries.find((x) => x.country === n);
			return { name: n, share: (100 * (c ? value(c) : 0)) / sum };
		});
		const rest = 100 - named.reduce((a, s) => a + s.share, 0);
		return [...named, { name: REST, share: Math.max(rest, 0) }];
	}

	const charts = $derived([
		{ key: 'mcap', label: 'Market capitalisation', slices: slices((c) => c.mcap) },
		{ key: 'gdp', label: 'GDP', slices: slices((c) => c.gdp) },
		{
			key: 'target',
			label: 'Mix',
			slices: slices((c) => split * c.mcap + (1 - split) * c.gdp)
		}
	]);

	/** Ring segment from `from` to `to`, both in percent of the full circle, starting
	 *  at twelve o'clock and running clockwise. */
	function arc(from: number, to: number) {
		const p = (v: number, r: number) => {
			const a = (v / 100) * 2 * Math.PI - Math.PI / 2;
			return [r * Math.cos(a), r * Math.sin(a)];
		};
		const big = to - from > 50 ? 1 : 0;
		const [x1, y1] = p(from, R);
		const [x2, y2] = p(to, R);
		const [x3, y3] = p(to, HOLE);
		const [x4, y4] = p(from, HOLE);
		return `M${x1} ${y1}A${R} ${R} 0 ${big} 1 ${x2} ${y2}L${x3} ${y3}A${HOLE} ${HOLE} 0 ${big} 0 ${x4} ${y4}Z`;
	}

	/** The slices with their running start, so every chart is drawn in one pass. */
	const drawn = $derived(
		charts.map((chart) => {
			let at = 0;
			return {
				...chart,
				parts: chart.slices.map((s) => {
					const from = at;
					at += s.share;
					// a full circle has no arc that svg could draw - leave a hair open
					return { ...s, d: arc(from, Math.min(at, from + 99.999)) };
				})
			};
		})
	);

	let hovered = $state<string | null>(null);
	const legend = $derived([...names, REST]);
	const fill = (name: string) => color.get(name) ?? 'var(--baseline)';
</script>

<div class="card">
	<p class="legend">
		{#each legend as name (name)}
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<span
				class:dim={hovered !== null && hovered !== name}
				onmouseenter={() => (hovered = name)}
				onmouseleave={() => (hovered = null)}
			>
				<i class="key" style:background={fill(name)}></i>{name}
			</span>
		{/each}
	</p>

	<div class="charts">
		{#each drawn as chart (chart.key)}
			<figure>
				<svg viewBox="{-BOX / 2} {-BOX / 2} {BOX} {BOX}" role="img" aria-label={chart.label}>
					{#each chart.parts as part (part.name)}
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<path
							d={part.d}
							fill={fill(part.name)}
							class:dim={hovered !== null && hovered !== part.name}
							onmouseenter={() => (hovered = part.name)}
							onmouseleave={() => (hovered = null)}
						>
							<title>{part.name}: {pct(part.share)} %</title>
						</path>
					{/each}
					{#if hovered}
						{@const share = chart.parts.find((p) => p.name === hovered)?.share ?? 0}
						<text class="mid" x="0" y="4">{pct(share)} %</text>
					{/if}
				</svg>
				<figcaption>
					{chart.label}
					{#if chart.key === 'target'}
						<span class="muted"
							>{Math.round(split * 100)} / {Math.round((1 - split) * 100)}</span
						>
					{/if}
				</figcaption>
			</figure>
		{/each}
	</div>
</div>

<style>
	.legend {
		display: flex;
		gap: 8px 18px;
		flex-wrap: wrap;
		margin: 0 0 8px;
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
	.charts {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 8px;
		justify-items: center;
	}
	figure {
		margin: 0;
		width: 100%;
		max-width: 260px;
		text-align: center;
	}
	svg {
		width: 100%;
		height: auto;
	}
	path {
		stroke: var(--surface);
		stroke-width: 1;
	}
	.dim {
		opacity: 0.32;
	}
	.mid {
		text-anchor: middle;
		font-size: 13px;
		fill: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	figcaption {
		color: var(--ink-2);
		font-size: 13px;
		margin-top: 2px;
	}
	figcaption .muted {
		font-variant-numeric: tabular-nums;
	}
</style>
