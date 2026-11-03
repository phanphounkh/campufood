<script lang="ts">
	import { slide } from 'svelte/transition';
	import Trash from '@lucide/svelte/icons/trash';
	import FoodImage from '#lib/components/ui/FoodImage.svelte';
	import QuantityStepper from '#lib/components/ui/QuantityStepper.svelte';
	import { cart, type CartLine } from '#lib/stores/cart.svelte.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { formatCents, formatMoney, toCents } from '#lib/utils/money.ts';

	let { line, compact = false }: { line: CartLine; compact?: boolean } = $props();
	const name = $derived(i18n.pick(line, 'name'));
</script>

<li
	class="flex items-center gap-3 py-3"
	transition:slide={{ duration: 200 }}
	data-testid="cart-line"
>
	<FoodImage
		src={line.image_url}
		alt={name}
		class="{compact ? 'size-14' : 'size-16'} shrink-0 rounded-2xl"
	/>
	<div class="min-w-0 flex-1">
		<p class="truncate font-semibold text-ink" lang={i18n.locale}>{name}</p>
		<p class="text-sm font-bold text-brand-600">
			{formatMoney(line.price)}
			{#if line.quantity > 1}
				<span class="font-medium text-ink-muted"
					>× {line.quantity} = {formatCents(toCents(line.price) * line.quantity)}</span
				>
			{/if}
		</p>
	</div>
	<div class="flex flex-col items-end gap-1.5">
		<QuantityStepper
			size="sm"
			value={line.quantity}
			max={line.maxQuantity}
			{name}
			ondecrement={() => cart.decrement(line.foodId)}
			onincrement={() => cart.increment(line.foodId)}
		/>
		<button
			type="button"
			class="inline-flex items-center gap-1 rounded-md px-1 text-xs font-medium text-ink-muted hover:text-danger-ink"
			aria-label={t('cart.remove', { name })}
			onclick={() => cart.remove(line.foodId)}
		>
			<Trash class="size-3.5" />
		</button>
	</div>
</li>
