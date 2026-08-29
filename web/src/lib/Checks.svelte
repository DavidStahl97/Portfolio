<script lang="ts">
	import type { Check } from '$lib/types';

	let { checks }: { checks: Check[] } = $props();
</script>

<div class="card scroll">
	<table>
		<thead>
			<tr><th>Check</th><th>Result</th><th>Status</th></tr>
		</thead>
		<tbody>
			{#each checks as c (c.name)}
				<tr>
					<td class="wrap">{c.name}</td>
					<td>{c.detail}</td>
					<td>
						<span class="status" class:ok={c.passed} class:fail={!c.passed}>
							<span class="dot"></span>{c.passed ? 'OK' : 'FAILED'}
						</span>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>

<style>
	td.wrap {
		white-space: normal;
	}
</style>
