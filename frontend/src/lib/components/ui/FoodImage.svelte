<script lang="ts">
	import UtensilsCrossed from '@lucide/svelte/icons/utensils-crossed';

	let {
		src,
		alt,
		class: className = '',
		loading = 'lazy'
	}: { src: string | null; alt: string; class?: string; loading?: 'lazy' | 'eager' } = $props();

	let failed = $state(false);
	$effect(() => {
		void src;
		failed = false;
	});
</script>

{#if src && !failed}
	<img
		{src}
		{alt}
		{loading}
		decoding="async"
		draggable="false"
		class="object-cover {className}"
		onerror={() => (failed = true)}
	/>
{:else}
	<div
		class="grid place-items-center bg-gradient-to-br from-brand-50 to-brand-100 text-brand-300 {className}"
		role="img"
		aria-label={alt}
	>
		<UtensilsCrossed class="size-1/3 max-h-12 max-w-12" />
	</div>
{/if}
