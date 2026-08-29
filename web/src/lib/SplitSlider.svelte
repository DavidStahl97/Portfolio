<script lang="ts">
	import { DEFAULT_SPLIT, mix, remember } from '$lib/split.svelte';

	const fmt = (v: number) => `${Math.round(v * 100)} %`;

	function set(v: number) {
		mix.split = v;
		remember(v);
	}
</script>

<div class="card split">
	<label for="split">
		<strong>{fmt(mix.split)}</strong> Marktkapitalisierung /
		<strong>{fmt(1 - mix.split)}</strong> BIP
	</label>
	<input
		id="split"
		type="range"
		min="0"
		max="1"
		step="0.05"
		value={mix.split}
		oninput={(e) => set(Number(e.currentTarget.value))}
	/>
	{#if Math.abs(mix.split - DEFAULT_SPLIT) > 0.001}
		<button onclick={() => set(DEFAULT_SPLIT)}>zurück auf {fmt(DEFAULT_SPLIT)}</button>
	{:else}
		<span class="muted">die Standardmischung</span>
	{/if}
</div>

<style>
	.split {
		display: flex;
		align-items: center;
		gap: 16px;
		flex-wrap: wrap;
		padding: 12px 20px;
	}
	label {
		color: var(--ink-2);
	}
	strong {
		color: var(--ink);
		font-variant-numeric: tabular-nums;
	}
	input {
		flex: 1 1 220px;
		accent-color: var(--s1);
	}
	button {
		font: inherit;
		color: var(--s1);
		background: none;
		border: 1px solid var(--ring);
		border-radius: 7px;
		padding: 3px 10px;
		cursor: pointer;
	}
	button:hover {
		background: color-mix(in srgb, var(--ink) 5%, transparent);
	}
	.muted {
		font-size: 12px;
	}
</style>
