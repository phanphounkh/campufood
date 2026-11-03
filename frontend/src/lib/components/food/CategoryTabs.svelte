<script lang="ts">
	import type { Component } from 'svelte';
	import LayoutGrid from '@lucide/svelte/icons/layout-grid';
	import CookingPot from '@lucide/svelte/icons/cooking-pot';
	import Soup from '@lucide/svelte/icons/soup';
	import Sandwich from '@lucide/svelte/icons/sandwich';
	import CupSoda from '@lucide/svelte/icons/cup-soda';
	import IceCreamCone from '@lucide/svelte/icons/ice-cream-cone';
	import UtensilsCrossed from '@lucide/svelte/icons/utensils-crossed';
	import type { Category } from '#lib/types/api.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';

	let {
		categories,
		selected = $bindable('all'),
		onchange
	}: {
		categories: Category[];
		selected?: string;
		onchange?: (slug: string) => void;
	} = $props();

	const icons: Record<string, Component<{ class?: string }>> = {
		all: LayoutGrid,
		rice: CookingPot,
		noodles: Soup,
		snacks: Sandwich,
		drinks: CupSoda,
		desserts: IceCreamCone
	};

	const tabs = $derived([
		{ slug: 'all', label: t('menu.all') },
		...categories
			.filter((c) => c.food_count > 0)
			.map((c) => ({ slug: c.slug, label: i18n.pick(c, 'name') }))
	]);

	function select(slug: string) {
		selected = slug;
		onchange?.(slug);
	}
</script>

<div
	class="-mx-4 flex [scrollbar-width:none] gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:flex-wrap sm:px-0"
	role="toolbar"
	aria-label={t('menu.categories')}
>
	{#each tabs as tab (tab.slug)}
		{@const Icon = icons[tab.slug] ?? UtensilsCrossed}
		{@const active = selected === tab.slug}
		<button
			type="button"
			class="inline-flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition
				{active
				? 'border-brand-600 bg-brand-600 text-white shadow-[0_6px_16px_-8px_rgb(100_37_216/0.9)]'
				: 'border-line bg-white text-ink-soft hover:border-brand-200 hover:bg-brand-50 hover:text-brand-700'}"
			aria-pressed={active}
			lang={i18n.locale}
			onclick={() => select(tab.slug)}
		>
			<Icon class="size-4" />
			{tab.label}
		</button>
	{/each}
</div>
