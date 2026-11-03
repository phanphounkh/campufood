<script lang="ts">
	import ShoppingCart from '@lucide/svelte/icons/shopping-cart';
	import Modal from '#lib/components/ui/Modal.svelte';
	import FoodImage from '#lib/components/ui/FoodImage.svelte';
	import QuantityStepper from '#lib/components/ui/QuantityStepper.svelte';
	import { addToCart } from '#lib/components/cart/addToCart.ts';
	import { MAX_PER_ITEM } from '#lib/stores/cart.svelte.ts';
	import type { Food } from '#lib/types/api.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { formatCents, formatMoney, toCents } from '#lib/utils/money.ts';

	let { food = $bindable(null) }: { food: Food | null } = $props();

	let open = $state(false);
	let quantity = $state(1);
	$effect(() => {
		if (food) {
			open = true;
			quantity = 1;
		}
	});

	const max = $derived(food ? Math.min(MAX_PER_ITEM, food.stock_quantity) : 1);

	function add() {
		if (food && addToCart(food, quantity)) open = false;
	}
</script>

{#if food}
	<Modal bind:open title={i18n.pick(food, 'name')} onclose={() => (food = null)} size="md">
		<div class="-mx-5 -mt-5 sm:-mx-6">
			<FoodImage
				src={food.image_url}
				alt={i18n.pick(food, 'name')}
				class="aspect-[16/10] w-full"
				loading="eager"
			/>
		</div>
		<div class="mt-5 flex items-start justify-between gap-4">
			<div>
				<p class="text-sm text-ink-muted" lang={i18n.locale === 'en' ? 'km' : 'en'}>
					{i18n.pickOther(food, 'name')}
				</p>
				<span class="chip mt-2 bg-brand-50 text-brand-700" lang={i18n.locale}>
					{i18n.pick(food.category, 'name')}
				</span>
			</div>
			<p class="text-2xl font-extrabold text-brand-600">{formatMoney(food.price)}</p>
		</div>
		<p class="mt-4 text-ink-soft" lang={i18n.locale}>{i18n.pick(food, 'description')}</p>
		<p class="mt-2 text-sm text-ink-muted" lang={i18n.locale === 'en' ? 'km' : 'en'}>
			{i18n.pickOther(food, 'description')}
		</p>
		{#if food.is_sold_out}
			<p class="mt-4 rounded-xl bg-red-50 px-4 py-3 text-sm font-semibold text-danger-ink">
				{t('food.soldOut')}
			</p>
		{:else if food.stock_quantity <= 5}
			<p class="mt-4 rounded-xl bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
				{t('food.onlyLeft', { count: food.stock_quantity })}
			</p>
		{/if}

		{#snippet footer()}
			{#if food && !food.is_sold_out}
				<div class="flex w-full items-center justify-between gap-3">
					<div class="flex items-center gap-3">
						<span class="text-sm font-semibold text-ink-muted">{t('food.quantity')}</span>
						<QuantityStepper
							value={quantity}
							{max}
							name={i18n.pick(food, 'name')}
							ondecrement={() => (quantity = Math.max(1, quantity - 1))}
							onincrement={() => (quantity = Math.min(max, quantity + 1))}
						/>
					</div>
					<button type="button" class="btn btn-primary" onclick={add}>
						<ShoppingCart class="size-4" />
						{t('food.add')} · {formatCents(toCents(food.price) * quantity)}
					</button>
				</div>
			{/if}
		{/snippet}
	</Modal>
{/if}
