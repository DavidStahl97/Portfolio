<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { day, month } from '$lib/format';
	import { stampOf } from '$lib/data';
	import { onMount } from 'svelte';
	import '../app.css';

	let { data, children } = $props();

	// The manifest is linked from app.html, the only markup that exists before JavaScript
	// runs - nothing renders on a server, so a <svelte:head> entry would arrive too late.
	// The service worker registers itself here instead: SvelteKit does not run app.html
	// through Vite's html plugin, so vite-plugin-pwa injects nothing for us.
	onMount(async () => {
		const { registerSW } = await import('virtual:pwa-register');
		registerSW({ immediate: true });
	});

	const current = $derived(page.params.date ?? stampOf(data.index.dates[0]?.asOf ?? ''));
	const history = $derived(page.url.pathname.endsWith('/history/'));
	const dataPage = $derived(page.url.pathname.endsWith('/data/'));
	const several = $derived(data.index.dates.length > 1);
</script>

<div class="wrap">
	<header>
		<h1>Portfolio target weights</h1>
		<p class="lead">
			Country weights, half by market capitalisation and half by gross domestic product,
			from the factsheet of the FTSE All-World GDP Weighted Index.
		</p>
	</header>

	<nav class="dates">
		<span class="navlabel">As of</span>
		{#each data.index.dates as s (s.asOf)}
			{@const stamp = stampOf(s.asOf)}
			<a
				href="{base}/dates/{stamp}/"
				class:current={!history && !dataPage && stamp === current}
				title={day(s.asOf)}>{month(s.asOf)}</a
			>
		{/each}
		<span class="sep"></span>
		{#if several}
			<a href="{base}/history/" class:current={history}>History</a>
		{/if}
		<a href="{base}/data/" class:current={dataPage}>Data</a>
	</nav>

	{@render children()}

	<footer>
		Source: FTSE Russell, FTSE All-World GDP Weighted Index factsheet.
		<a href="{base}/data/">Data as CSV</a>. Built from
		<a href="https://github.com/{__REPO__}">{__REPO__}</a>{__BUILT__ ? `, as of ${__BUILT__}` : ''}.
		Not investment advice.
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
	.dates {
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
	.dates a {
		padding: 3px 9px;
		border-radius: 6px;
		text-decoration: none;
		font-variant-numeric: tabular-nums;
	}
	.dates a:hover {
		background: color-mix(in srgb, var(--ink) 6%, transparent);
	}
	.dates a.current {
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
