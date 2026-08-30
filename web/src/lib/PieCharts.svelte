<script lang="ts">
	import { pct } from '$lib/format';
	import { countryGroups, regionGroups, shares, UNCOVERED, type Group } from '$lib/weights';
	import type { Country, Region } from '$lib/types';

	let {
		countries,
		split,
		regions = [],
		top = 8
	}: { countries: Country[]; split: number; regions?: Region[]; top?: number } = $props();

	// The same eight series colours as everywhere else, assigned in this order: the
	// colour belongs to the country or the region and is the same in all three charts,
	// which is the whole point of showing them next to each other.
	const COLORS = ['--s1', '--s2', '--s3', '--s4', '--s5', '--s6', '--s7', '--s8'];

	const R = 52;
	const HOLE = 30;
	const BOX = 124; // -62 .. 62

	// Countries or the five regional indices. Without regions.json there is nothing to
	// switch to, and the control is not shown at all.
	let by = $state<'country' | 'region'>('country');
	const canGroup = $derived(regions.length > 0);
	const mode = $derived(canGroup ? by : 'country');

	/** How the pie is cut. All three charts use the same groups, so they are comparable
	 *  slice by slice; only the way a country is valued differs between them. */
	const groups: Group[] = $derived(
		mode === 'region' ? regionGroups(countries, regions) : countryGroups(countries, split, top)
	);

	// The remainder and the countries in none of the five are not a series of their
	// own - they get the neutral colour, so a real slice is never mistaken for them.
	const color = $derived(
		new Map(
			groups
				.filter((g) => g.name !== 'rest' && g.name !== UNCOVERED)
				.map((g, i) => [g.name, `var(${COLORS[i % COLORS.length]})`])
		)
	);
	const fill = (name: string) => color.get(name) ?? 'var(--baseline)';
	const label = $derived(new Map(groups.map((g) => [g.name, g.label])));
	const title = $derived(new Map(groups.map((g) => [g.name, g.title])));

	const charts = $derived([
		{ key: 'mcap', label: 'Market capitalisation', value: (c: Country) => c.mcap },
		{ key: 'gdp', label: 'GDP', value: (c: Country) => c.gdp },
		{
			key: 'target',
			label: 'Mix',
			value: (c: Country) => split * c.mcap + (1 - split) * c.gdp
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
				parts: shares(countries, groups, chart.value).map((s) => {
					const from = at;
					at += s.share;
					// a full circle has no arc that svg could draw - leave a hair open
					return { ...s, d: arc(from, Math.min(at, from + 99.999)) };
				})
			};
		})
	);

	let hovered = $state<string | null>(null);
</script>

<div class="card">
	<div class="head">
		<p class="legend">
			{#each groups as group (group.name)}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<span
					class:dim={hovered !== null && hovered !== group.name}
					title={group.title}
					onmouseenter={() => (hovered = group.name)}
					onmouseleave={() => (hovered = null)}
				>
					<i class="key" style:background={fill(group.name)}></i>{group.label}
				</span>
			{/each}
		</p>

		{#if canGroup}
			<div class="switch" role="group" aria-label="Group by">
				<button type="button" aria-pressed={mode === 'country'} onclick={() => (by = 'country')}>
					Countries
				</button>
				<button type="button" aria-pressed={mode === 'region'} onclick={() => (by = 'region')}>
					5 regions
				</button>
			</div>
		{/if}
	</div>

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
							<title>{title.get(part.name)}: {pct(part.share)} %</title>
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

	{#if mode === 'region'}
		<p class="note">
			{#if hovered && hovered !== UNCOVERED}
				{title.get(hovered)}: {groups.find((g) => g.name === hovered)?.countries.join(', ')}
			{:else}
				The five indices of the Vanguard regional ETFs. Together they cover the All-World
				except for the neutral slice - the mix decides how much goes into each.
			{/if}
		</p>
	{/if}
</div>

<style>
	.head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 16px;
		flex-wrap: wrap;
		margin-bottom: 8px;
	}
	.legend {
		display: flex;
		gap: 8px 18px;
		flex-wrap: wrap;
		margin: 0;
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
	.switch {
		display: inline-flex;
		border: 1px solid var(--ring);
		border-radius: 8px;
		overflow: hidden;
		flex: none;
	}
	.switch button {
		font: inherit;
		font-size: 13px;
		padding: 4px 10px;
		border: 0;
		background: transparent;
		color: var(--ink-2);
		cursor: pointer;
	}
	.switch button + button {
		border-left: 1px solid var(--ring);
	}
	.switch button[aria-pressed='true'] {
		background: var(--ring);
		color: var(--ink);
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
	.note {
		margin: 8px 0 0;
		color: var(--ink-2);
		font-size: 13px;
	}
</style>
