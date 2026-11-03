<script lang="ts">
	import type { Component, Snippet } from 'svelte';

	let {
		icon: Icon,
		title,
		text,
		children,
		compact = false
	}: {
		icon: Component<{ class?: string }>;
		title: string;
		text?: string;
		children?: Snippet;
		compact?: boolean;
	} = $props();
</script>

<div class="flex flex-col items-center text-center {compact ? 'py-6' : 'py-14'}">
	<div class="grid size-16 place-items-center rounded-2xl bg-brand-50 text-brand-500">
		<Icon class="size-7" />
	</div>
	<h3 class="mt-4 text-base font-bold text-ink">{title}</h3>
	{#if text}<p class="mt-1 max-w-xs text-sm text-ink-muted">{text}</p>{/if}
	{#if children}<div class="mt-5">{@render children()}</div>{/if}
</div>
