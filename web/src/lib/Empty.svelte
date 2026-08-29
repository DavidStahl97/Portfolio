<!-- The state before the first run: the site stands, there is just no data yet. -->
<div class="card empty">
	<h2>No as-of dates yet</h2>
	<p>
		There are no checked factsheet data yet. The first as-of date is produced by a run of
		the <strong>Fetch data</strong> action – or locally:
	</p>
	<pre>python scripts/update.py</pre>
	<p class="muted">
		After that the report stands here: key figures, checks, the largest positions and the
		full country table.
	</p>
</div>

<style>
	.empty {
		max-width: 62ch;
	}
	h2 {
		margin: 0 0 8px;
		font-size: 17px;
	}
	p {
		color: var(--ink-2);
		margin: 0 0 12px;
	}
	pre {
		background: var(--plane);
		border: 1px solid var(--ring);
		border-radius: 7px;
		padding: 10px 14px;
		margin: 0 0 12px;
		overflow-x: auto;
	}
</style>
