<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';
</script>

<h2>{page.status} — {page.error?.message ?? 'Da ist nichts'}</h2>
<p><a href="{base}/">Zurück zum neuesten Stichtag</a></p>
