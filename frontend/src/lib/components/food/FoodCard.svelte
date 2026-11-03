<script lang="ts">
	import Plus from '@lucide/svelte/icons/plus';
	import GripVertical from '@lucide/svelte/icons/grip-vertical';
	import Flame from '@lucide/svelte/icons/flame';
	import type { Food } from '#lib/types/api.ts';
	import FoodImage from '#lib/components/ui/FoodImage.svelte';
	import { addToCart } from '#lib/components/cart/addToCart.ts';
	import { cart } from '#lib/stores/cart.svelte.ts';
	import { drag, draggableFood } from '#lib/stores/dnd.svelte.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { formatMoney } from '#lib/utils/money.ts';

	let {
		food,
		onopen,
		eager = false
	}: { food: Food; onopen?: (food: Food) => void; eager?: boolean } = $props();

	const name = $derived(i18n.pick(food, 'name'));
	const otherName = $derived(i18n.pickOther(food, 'name'));
	const description = $derived(i18n.pick(food, 'description'));
	const inCart = $derived(cart.quantityOf(food.id));
	const lowStock = $derived(!food.is_sold_out && food.stock_quantity <= 5);
	const beingDragged = $derived(drag.food?.id === food.id);
</script>

<article
	class="group relative flex flex-col overflow-hidden rounded-[var(--radius-card)] border bg-white transition duration-300
		{beingDragged
		? 'scale-[0.97] border-brand-400 opacity-60 ring-4 ring-brand-100'
		: 'border-line shadow-soft hover:-translate-y-1 hover:border-brand-200 hover:shadow-lift'}
		{food.is_sold_out ? '' : 'cursor-grab active:cursor-grabbing'}"
	use:draggableFood={{ food, disabled: food.is_sold_out, onDrop: (f) => addToCart(f) }}
	data-testid="food-card"
	data-food-id={food.id}
>
	<div class="relative aspect-[4/3] overflow-hidden bg-brand-50">
		<button
			type="button"
			class="block size-full"
			data-drag-ok
			onclick={() => onopen?.(food)}
			aria-label={t('food.details') + ': ' + name}
			tabindex={onopen ? 0 : -1}
		>
			<FoodImage
				src={food.image_url}
				alt={name}
				loading={eager ? 'eager' : 'lazy'}
				class="size-full transition duration-500 group-hover:scale-105 {food.is_sold_out
					? 'grayscale-[60%]'
					: ''}"
			/>
		</button>

		<div class="pointer-events-none absolute top-3 left-3 flex flex-wrap gap-1.5">
			{#if food.is_sold_out}
				<span class="chip bg-ink/85 text-white backdrop-blur">{t('food.soldOut')}</span>
			{:else if food.is_featured}
				<span class="chip bg-danger-ink text-white shadow-sm"
					><Flame class="size-3" />{t('food.popular')}</span
				>
			{/if}
			{#if lowStock}
				<span class="chip bg-amber-100 text-amber-900"
					>{t('food.onlyLeft', { count: food.stock_quantity })}</span
				>
			{/if}
		</div>

		{#if !food.is_sold_out}
			<button
				type="button"
				data-drag-handle
				class="absolute top-2.5 right-2.5 grid size-9 touch-none place-items-center rounded-xl bg-white/90 text-ink-soft shadow-sm backdrop-blur transition hover:bg-white hover:text-brand-700 focus-visible:opacity-100 sm:opacity-0 sm:group-hover:opacity-100"
				aria-label={t('food.drag', { name })}
				title={t('food.drag', { name })}
				onclick={() => addToCart(food)}
			>
				<GripVertical class="size-4" />
			</button>
		{/if}

		{#if inCart > 0}
			<span
				class="chip absolute bottom-2.5 left-2.5 bg-brand-600 text-white shadow"
				aria-label={t('food.inCart', { count: inCart })}
			>
				{t('food.inCart', { count: inCart })}
			</span>
		{/if}
	</div>

	<div class="flex flex-1 flex-col p-4">
		<div class="flex items-start justify-between gap-2">
			<div class="min-w-0">
				<h3 class="font-bold text-ink" lang={i18n.locale}>
					<button
						type="button"
						class="text-left hover:text-brand-700"
						onclick={() => onopen?.(food)}
						tabindex="-1"
					>
						{name}
					</button>
				</h3>
				{#if otherName}
					<p class="truncate text-xs text-ink-muted" lang={i18n.locale === 'en' ? 'km' : 'en'}>
						{otherName}
					</p>
				{/if}
			</div>
			<span class="chip shrink-0 bg-brand-50 text-brand-700" lang={i18n.locale}>
				{i18n.pick(food.category, 'name')}
			</span>
		</div>
		{#if description}
			<p class="mt-2 line-clamp-2 text-sm text-ink-muted" lang={i18n.locale}>{description}</p>
		{/if}
		<div class="mt-auto flex items-center justify-between pt-4">
			<div>
				<p class="text-lg font-extrabold text-brand-600">{formatMoney(food.price)}</p>
				<p class="text-xs font-medium {food.is_sold_out ? 'text-danger-ink' : 'text-success-ink'}">
					{food.is_sold_out ? t('food.soldOut') : t('food.available')}
				</p>
			</div>
			<button
				type="button"
				class="grid size-11 place-items-center rounded-2xl transition
					{food.is_sold_out
					? 'cursor-not-allowed bg-slate-100 text-slate-400'
					: 'bg-brand-600 text-white shadow-[0_8px_18px_-8px_rgb(100_37_216/0.8)] hover:scale-105 hover:bg-brand-700 active:scale-95'}"
				disabled={food.is_sold_out}
				aria-label={t('food.addNamed', { name })}
				data-testid="add-to-cart"
				onclick={() => addToCart(food)}
			>
				<Plus class="size-5" strokeWidth={2.5} />
			</button>
		</div>
	</div>
</article>
