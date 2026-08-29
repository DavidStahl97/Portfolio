<script lang="ts">
	let {
		split = $bindable(),
		configured
	}: { split: number; configured: number } = $props();

	const fmt = (v: number) => `${Math.round(v * 100)} %`;
</script>

<div class="card split">
	<label for="split">
		Mischung <strong>{fmt(split)}</strong> Marktkapitalisierung /
		<strong>{fmt(1 - split)}</strong> BIP
	</label>
	<input id="split" type="range" min="0" max="1" step="0.05" bind:value={split} />
	{#if Math.abs(split - configured) > 0.001}
		<button onclick={() => (split = configured)}>zurück auf {fmt(configured)}</button>
	{:else}
		<span class="muted">so gerechnet und in der CSV abgelegt</span>
	{/if}
</div>

<style>
	.split {
		display: flex;
		align-items: center;
		gap: 16px;
		flex-wrap: wrap;
		padding: 12px 20px;
		margin-bottom: 12px;
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
