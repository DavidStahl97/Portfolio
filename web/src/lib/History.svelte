<script lang="ts">
	import { day, month, pct } from '$lib/format';
	import { targets } from '$lib/weights';
	import type { Report } from '$lib/types';

	let {
		reports,
		split,
		top = 8
	}: { reports: Report[]; split: number; top?: number } = $props();

	// Eight fixed series colours, assigned in this order and never handed on:
	// the colour belongs to the country, not to its rank.
	const COLORS = ['--s1', '--s2', '--s3', '--s4', '--s5', '--s6', '--s7', '--s8'];

	const W = 860;
	const H = 340;
	const PAD = { t: 16, r: 108, b: 28, l: 40 };

	const perDate = $derived(reports.map((r) => targets(r.countries, split)));
	// Which countries are shown is decided by the newest as-of date - after that every
	// country keeps its colour, no matter how it moved before.
	const names = $derived(
		[...(perDate.at(-1) ?? new Map())]
			.sort((a, b) => b[1] - a[1])
			.slice(0, top)
			.map(([name]) => name)
	);
	const max = $derived(
		Math.max(...names.flatMap((n) => perDate.map((m) => m.get(n) ?? 0)), 1) * 1.08
	);

	const x = (i: number) =>
		PAD.l + (reports.length < 2 ? 0 : (i * (W - PAD.l - PAD.r)) / (reports.length - 1));
	const y = (v: number) => H - PAD.b - (v / max) * (H - PAD.t - PAD.b);

	const lines = $derived(
		names.map((name, s) => ({
			name,
			color: `var(${COLORS[s % COLORS.length]})`,
			values: perDate.map((m) => m.get(name) ?? 0),
			d: perDate.map((m, i) => `${i ? 'L' : 'M'}${x(i)} ${y(m.get(name) ?? 0)}`).join(' ')
		}))
	);

	/** Push the end labels apart so that countries lying close together do not
	 *  overwrite each other. The dot stays on its value, only the text moves - which
	 *  is why every shifted line gets a leader line. */
	const labels = $derived.by(() => {
		const GAP = 13;
		const items = lines
			.map((l, i) => ({ i, name: l.name, color: l.color, v: l.values.at(-1) ?? 0 }))
			.map((o) => ({ ...o, at: y(o.v), ly: y(o.v) }))
			.sort((a, b) => a.at - b.at);
		for (let k = 1; k < items.length; k++)
			items[k].ly = Math.max(items[k].ly, items[k - 1].ly + GAP);
		// push back into the frame if it ran out at the bottom
		const over = (items.at(-1)?.ly ?? 0) - (H - PAD.b);
		if (over > 0) for (const o of items) o.ly -= over;
		return items;
	});

	/** Round values on the axis - 0 / 10 / 20 instead of 11.4 / 22.8. */
	const ticks = $derived.by(() => {
		const raw = max / 4;
		const mag = 10 ** Math.floor(Math.log10(raw));
		const step = [1, 2, 2.5, 5, 10].find((f) => f * mag >= raw)! * mag;
		const out: number[] = [];
		for (let v = 0; v <= max; v += step) out.push(Math.round(v * 100) / 100);
		return out;
	});

	let at = $state<number | null>(null);
</script>

<div class="card">
	<p class="legend">
		{#each lines as l (l.name)}
			<span><i class="key" style:background={l.color}></i>{l.name}</span>
		{/each}
	</p>

	<div class="plot">
		<svg viewBox="0 0 {W} {H}" role="img" aria-label="Target weights across the as-of dates">
			{#each ticks as t (t)}
				<line class="grid" x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} />
				<text class="tick" x={PAD.l - 8} y={y(t)} text-anchor="end" dominant-baseline="middle"
					>{t}</text
				>
			{/each}

			{#each reports as r, i (r.asOf)}
				<text class="tick" x={x(i)} y={H - 8} text-anchor="middle">{month(r.asOf)}</text>
			{/each}

			{#if at !== null}
				<line class="cursor" x1={x(at)} x2={x(at)} y1={PAD.t} y2={H - PAD.b} />
			{/if}

			{#each lines as l (l.name)}
				<path class="line" d={l.d} stroke={l.color} />
				<circle
					class="end"
					cx={x(reports.length - 1)}
					cy={y(l.values.at(-1) ?? 0)}
					r="4"
					fill={l.color}
				/>
				{#if at !== null}
					<circle class="end" cx={x(at)} cy={y(l.values[at])} r="4" fill={l.color} />
				{/if}
			{/each}

			{#each labels as o (o.name)}
				{#if Math.abs(o.ly - o.at) > 1}
					<path
						class="leader"
						d="M{x(reports.length - 1) + 5} {o.at} L{W - PAD.r + 4} {o.ly}"
						stroke={o.color}
					/>
				{/if}
				<text class="label" x={W - PAD.r + 10} y={o.ly} dominant-baseline="middle"
					>{o.name} {pct(o.v)}</text
				>
			{/each}

			{#each reports as r, i (r.asOf)}
				<!-- wide, invisible hit area per as-of date -->
				<rect
					class="hit"
					x={x(i) - (W - PAD.l - PAD.r) / (2 * Math.max(1, reports.length - 1))}
					y={PAD.t}
					width={(W - PAD.l - PAD.r) / Math.max(1, reports.length - 1)}
					height={H - PAD.t - PAD.b}
					role="presentation"
					onmouseenter={() => (at = i)}
					onmouseleave={() => (at = null)}
				/>
			{/each}
		</svg>
	</div>

	{#if at !== null}
		<table class="readout">
			<caption>{day(reports[at].asOf)}</caption>
			<tbody>
				{#each lines as l (l.name)}
					<tr>
						<td><i class="key" style:background={l.color}></i>{l.name}</td>
						<td>{pct(l.values[at])} %</td>
						<td class="muted">
							{at > 0
								? `${l.values[at] - l.values[at - 1] >= 0 ? '+' : ''}${pct(l.values[at] - l.values[at - 1])} pp`
								: ''}
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
</div>

<style>
	.legend {
		display: flex;
		gap: 16px;
		flex-wrap: wrap;
		margin: 0 0 12px;
		color: var(--ink-2);
		font-size: 13px;
	}
	.legend span,
	.readout td:first-child {
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
	.plot {
		overflow-x: auto;
	}
	svg {
		width: 100%;
		min-width: 560px;
		height: auto;
		display: block;
	}
	.grid {
		stroke: var(--grid);
		stroke-width: 1;
	}
	.cursor {
		stroke: var(--baseline);
		stroke-width: 1;
	}
	.line {
		fill: none;
		stroke-width: 2;
		stroke-linejoin: round;
		stroke-linecap: round;
	}
	.end {
		stroke: var(--surface);
		stroke-width: 2;
	}
	.tick,
	.label {
		font-size: 11px;
		fill: var(--ink-muted);
		font-variant-numeric: tabular-nums;
	}
	.label {
		fill: var(--ink-2);
	}
	.leader {
		fill: none;
		stroke-width: 1;
		opacity: 0.5;
	}
	.hit {
		fill: transparent;
	}
	.readout {
		margin-top: 12px;
		width: auto;
	}
	.readout caption {
		text-align: left;
		color: var(--ink-muted);
		font-size: 12px;
		padding-bottom: 4px;
	}
	.readout td {
		border-bottom: none;
		padding: 3px 14px 3px 0;
	}
	.readout td:first-child {
		text-align: left;
	}
</style>
