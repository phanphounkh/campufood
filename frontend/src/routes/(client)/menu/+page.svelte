<script lang="ts">
	import { reveal } from '#lib/actions/reveal.ts';
	import { onMount, untrack } from 'svelte';
	import { page } from '$app/state';
	import { replaceState } from '$app/navigation';
	import Search from '@lucide/svelte/icons/search';
	import SearchX from '@lucide/svelte/icons/search-x';
	import X from '@lucide/svelte/icons/x';
	import MousePointerClick from '@lucide/svelte/icons/mouse-pointer-click';
	import FoodCard from '#lib/components/food/FoodCard.svelte';
	import CategoryTabs from '#lib/components/food/CategoryTabs.svelte';
	import FoodDetailModal from '#lib/components/food/FoodDetailModal.svelte';
	import CartPanel from '#lib/components/cart/CartPanel.svelte';
	import FloatingCartButton from '#lib/components/cart/FloatingCartButton.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import { cart } from '#lib/stores/cart.svelte.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import type { Food } from '#lib/types/api.ts';
	import { filterFoods, type MenuSort } from '#lib/utils/menu.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const sorts: MenuSort[] = ['featured', 'price_asc', 'price_desc', 'name'];
	const initial = page.url.searchParams;
	let category = $state(initial.get('category') ?? 'all');
	let search = $state(initial.get('q') ?? '');
	let sort = $state<MenuSort>(
		sorts.includes(initial.get('sort') as MenuSort) ? (initial.get('sort') as MenuSort) : 'featured'
	);
	let selected = $state<Food | null>(null);

	const visible = $derived(filterFoods(data.foods, { category, search, sort }));

	// Keep the URL shareable (?category=&q=&sort=) without reloading or re-running load().
	$effect(() => {
		const entries: [string, string][] = [];
		if (category !== 'all') entries.push(['category', category]);
		if (search.trim()) entries.push(['q', search.trim()]);
		if (sort !== 'featured') entries.push(['sort', sort]);
		const query = entries.length ? `?${new URLSearchParams(entries)}` : '';
		untrack(() => {
			if (location.search === query) return;
			try {
				replaceState(`${location.pathname}${query}`, page.state);
			} catch {
				/* router not ready yet */
			}
		});
	});

	onMount(() => {
		cart.load();
		const hadItems = cart.lines.length > 0;
		if (cart.sync(data.foods) && hadItems) toast.info(t('cart.updatedPrices'));
	});

	function resetFilters() {
		category = 'all';
		search = '';
		sort = 'featured';
	}
</script>

<svelte:head>
	<title>{t('menu.title')} · CampusEats</title>
</svelte:head>

<div class="border-b border-line bg-gradient-to-b from-brand-50/70 to-white">
	<div class="container-page pt-8 pb-6" use:reveal>
		<h1 class="text-3xl font-extrabold tracking-tight sm:text-4xl">{t('menu.title')}</h1>
		<p class="mt-2 flex items-center gap-2 text-ink-muted">
			<MousePointerClick class="size-4 text-brand-500" />
			{t('menu.subtitle')}
		</p>

		<div class="mt-6 flex flex-col gap-3 sm:flex-row">
			<label class="relative flex-1">
				<span class="sr-only">{t('menu.searchLabel')}</span>
				<Search
					class="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-ink-muted"
				/>
				<input
					type="search"
					bind:value={search}
					placeholder={t('menu.searchPlaceholder')}
					class="h-12 w-full pr-10 pl-10"
					data-testid="menu-search"
				/>
				{#if search}
					<button
						type="button"
						class="absolute top-1/2 right-2 grid size-8 -translate-y-1/2 place-items-center rounded-lg text-ink-muted hover:bg-brand-50"
						aria-label={t('menu.clearFilters')}
						onclick={() => (search = '')}
					>
						<X class="size-4" />
					</button>
				{/if}
			</label>
			<label class="flex items-center gap-2 sm:w-64">
				<span class="shrink-0 text-sm font-semibold text-ink-muted">{t('menu.sortLabel')}</span>
				<select
					bind:value={sort}
					class="h-12 w-full rounded-xl border-line text-sm"
					data-testid="menu-sort"
				>
					{#each sorts as option (option)}
						<option value={option}>{t(`menu.sort.${option}`)}</option>
					{/each}
				</select>
			</label>
		</div>
		<div class="mt-4">
			<CategoryTabs categories={data.categories} bind:selected={category} />
		</div>
	</div>
</div>

<div class="container-page grid gap-8 py-8 lg:grid-cols-[minmax(0,1fr)_380px]">
	<section aria-labelledby="results-heading">
		<h2 id="results-heading" class="sr-only">{t('menu.title')}</h2>
		<p class="mb-4 text-sm font-medium text-ink-muted" aria-live="polite" data-testid="menu-count">
			{t('menu.results', { count: visible.length })}
		</p>
		{#if visible.length}
			<div class="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
				{#each visible as food, i (food.id)}
					<FoodCard {food} eager={i < 3} onopen={(f) => (selected = f)} />
				{/each}
			</div>
		{:else}
			<div class="card" use:reveal={{ from: 'zoom' }}>
				<EmptyState icon={SearchX} title={t('menu.empty')} text={t('menu.emptyHint')}>
					<button type="button" class="btn btn-soft" onclick={resetFilters}
						>{t('menu.clearFilters')}</button
					>
				</EmptyState>
			</div>
		{/if}
	</section>

	<aside class="hidden lg:block" lang={i18n.locale} use:reveal={{ from: 'right' }}>
		<div class="sticky top-24">
			<CartPanel droppable class="max-h-[calc(100dvh-7.5rem)] min-h-80" />
		</div>
	</aside>
</div>

<FoodDetailModal bind:food={selected} />
<FloatingCartButton />
