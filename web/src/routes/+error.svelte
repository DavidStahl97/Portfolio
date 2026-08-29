<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';
</script>

<h2>{page.status} — {page.error?.message ?? 'There is nothing here'}</h2>
<p><a href="{base}/">Back to the newest as-of date</a></p>
