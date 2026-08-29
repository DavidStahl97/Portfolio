<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { day, month } from '$lib/format';
	import { stampOf } from '$lib/data';
	import '../app.css';

	let { data, children } = $props();

	const current = $derived(page.params.date ?? stampOf(data.index.stichtage[0]?.asOf ?? ''));
	const verlauf = $derived(page.url.pathname.endsWith('/verlauf/'));
	const daten = $derived(page.url.pathname.endsWith('/daten/'));
	const mehrfach = $derived(data.index.stichtage.length > 1);
</script>

<div class="wrap">
	<header>
		<h1>Portfolio-Zielgewichte</h1>
		<p class="lead">
			Länder-Gewichte je zur Hälfte nach Marktkapitalisierung und nach Bruttoinlandsprodukt,
			aus dem Factsheet des FTSE All-World GDP Weighted Index.
		</p>
	</header>

	<nav class="stichtage">
		<span class="navlabel">Stichtag</span>
		{#each data.index.stichtage as s (s.asOf)}
			{@const stamp = stampOf(s.asOf)}
			<a
				href="{base}/stichtage/{stamp}/"
				class:current={!verlauf && !daten && stamp === current}
				title={day(s.asOf)}>{month(s.asOf)}</a
			>
		{/each}
		<span class="sep"></span>
		{#if mehrfach}
			<a href="{base}/verlauf/" class:current={verlauf}>Verlauf</a>
		{/if}
		<a href="{base}/daten/" class:current={daten}>Daten</a>
	</nav>

	{@render children()}

	<footer>
		Quelle: FTSE Russell, FTSE All-World GDP Weighted Index Factsheet.
		<a href="{base}/daten/">Daten als CSV</a>. Erzeugt aus
		<a href="https://github.com/{__REPO__}">{__REPO__}</a>{__BUILT__ ? `, Stand ${__BUILT__}` : ''}.
		Keine Anlageberatung.
	</footer>
</div>

<style>
	.wrap {
		max-width: 1080px;
		margin: 0 auto;
		padding: 32px 20px 64px;
	}
	.lead {
		color: var(--ink-2);
		margin: 0 0 24px;
		max-width: 62ch;
	}
	.stichtage {
		display: flex;
		align-items: center;
		gap: 6px;
		flex-wrap: wrap;
		margin: 0 0 28px;
		padding: 10px 14px;
		background: var(--surface);
		border: 1px solid var(--ring);
		border-radius: 10px;
	}
	.navlabel {
		color: var(--ink-muted);
		font-size: 12px;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		margin-right: 4px;
	}
	.sep {
		width: 1px;
		align-self: stretch;
		background: var(--grid);
		margin: 0 4px;
	}
	.stichtage a {
		padding: 3px 9px;
		border-radius: 6px;
		text-decoration: none;
		font-variant-numeric: tabular-nums;
	}
	.stichtage a:hover {
		background: color-mix(in srgb, var(--ink) 6%, transparent);
	}
	.stichtage a.current {
		color: var(--ink);
		font-weight: 600;
		background: color-mix(in srgb, var(--ink) 8%, transparent);
	}
	footer {
		color: var(--ink-muted);
		font-size: 12px;
		margin-top: 48px;
		border-top: 1px solid var(--grid);
		padding-top: 16px;
	}
</style>
