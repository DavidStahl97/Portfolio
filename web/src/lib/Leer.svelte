<!-- Der Zustand vor dem ersten Lauf: die Seite steht, es gibt nur noch keine Daten. -->
<div class="card leer">
	<h2>Noch keine Stichtage</h2>
	<p>
		Es liegen noch keine geprüften Factsheet-Daten vor. Den ersten Stichtag erzeugt ein Lauf
		der Action <strong>Portfolio-Report</strong> – oder lokal:
	</p>
	<pre>python scripts/update.py</pre>
	<p class="muted">
		Danach steht hier der Report: Kennzahlen, Prüfungen, die größten Positionen und die
		vollständige Ländertabelle.
	</p>
</div>

<style>
	.leer {
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
