<script lang="ts">
	import type { Snippet } from 'svelte';
	let { title, subtitle, children }: { title: string; subtitle: string; children: Snippet } =
		$props();
</script>

<div class="container-page grid min-h-[70dvh] place-items-center py-12">
	<div class="card w-full max-w-md p-7 sm:p-8">
		<h1 class="text-2xl font-extrabold tracking-tight">{title}</h1>
		<p class="mt-1 text-sm text-ink-muted">{subtitle}</p>
		<div class="mt-7">{@render children()}</div>
	</div>
</div>
