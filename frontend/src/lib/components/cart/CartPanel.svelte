<script lang="ts">
	import ShoppingCart from '@lucide/svelte/icons/shopping-cart';
	import Trash from '@lucide/svelte/icons/trash';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import CartLineItem from './CartLineItem.svelte';
	import ConfirmDialog from '#lib/components/ui/ConfirmDialog.svelte';
	import { cart } from '#lib/stores/cart.svelte.ts';
	import { drag, dropZone } from '#lib/stores/dnd.svelte.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import { formatCents } from '#lib/utils/money.ts';

	let {
		droppable = false,
		bordered = true,
		onnavigate,
		heading = true,
		class: className = 'h-full'
	}: {
		droppable?: boolean;
		bordered?: boolean;
		onnavigate?: () => void;
		heading?: boolean;
		class?: string;
	} = $props();

	let panel: HTMLElement | undefined = $state();
	let confirmClear = $state(false);
	const hovering = $derived(drag.dragging && drag.activeZone === panel);

	function clear() {
		cart.clear();
		confirmClear = false;
		toast.info(t('cart.cleared'));
	}
</script>

<section
	bind:this={panel}
	{@attach (node) => {
		if (!droppable) return;
		const z = dropZone(node);
		return () => z.destroy();
	}}
	class="relative flex flex-col transition duration-200 {className}
		{bordered ? 'card' : ''}
		{drag.dragging && droppable ? 'ring-2 ring-brand-300 ring-offset-2' : ''}
		{hovering ? 'scale-[1.01] !border-brand-500 bg-brand-50/60' : ''}"
	aria-label={t('cart.title')}
	data-testid="cart-panel"
>
	<header class="flex items-center justify-between gap-3 px-5 pt-5 pb-3">
		<h2 class="text-xl font-extrabold text-ink {heading ? '' : 'sr-only'}">{t('cart.title')}</h2>
		<span class="font-medium text-ink-muted {heading ? 'mr-auto -ml-1' : ''}">
			({cart.count === 1 ? t('cart.item') : t('cart.items', { count: cart.count })})
		</span>
		{#if cart.lines.length}
			<button type="button" class="btn btn-ghost btn-sm" onclick={() => (confirmClear = true)}>
				<Trash class="size-3.5" />
				{t('cart.clear')}
			</button>
		{/if}
	</header>

	{#if cart.lines.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center px-6 pt-6 pb-10 text-center">
			<div
				class="grid size-20 place-items-center rounded-3xl border-2 border-dashed transition
					{hovering
					? 'border-brand-500 bg-brand-100 text-brand-700'
					: 'border-brand-200 bg-brand-50 text-brand-400'}"
			>
				<ShoppingCart class="size-8" />
			</div>
			<p class="mt-4 font-bold text-ink">{t('cart.empty')}</p>
			<p class="mt-1 max-w-[16rem] text-sm text-ink-muted">{t('cart.emptyHint')}</p>
		</div>
	{:else}
		<ul class="flex-1 divide-y divide-line overflow-y-auto px-5">
			{#each cart.lines as line (line.foodId)}
				<CartLineItem {line} />
			{/each}
		</ul>
		<div class="border-t border-line px-5 pt-4 pb-5">
			<dl class="space-y-1.5 text-sm">
				<div class="flex justify-between text-ink-soft">
					<dt>{t('cart.subtotal')}</dt>
					<dd class="font-semibold tabular-nums">{formatCents(cart.subtotalCents)}</dd>
				</div>
				<div class="flex justify-between text-ink-soft">
					<dt>{t('cart.serviceFee')}</dt>
					<dd class="font-semibold tabular-nums">{formatCents(0)}</dd>
				</div>
				<div class="flex items-baseline justify-between pt-2">
					<dt class="text-lg font-extrabold text-ink">{t('cart.total')}</dt>
					<dd class="text-2xl font-extrabold text-brand-600 tabular-nums" data-testid="cart-total">
						{formatCents(cart.totalCents)}
					</dd>
				</div>
			</dl>
			<a href="/checkout" class="btn btn-primary btn-lg mt-4 w-full" onclick={() => onnavigate?.()}>
				{t('cart.checkout')}
				<ArrowRight class="size-4" />
			</a>
		</div>
	{/if}

	{#if drag.dragging && droppable}
		<div
			class="pointer-events-none absolute inset-2 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed text-center backdrop-blur-[2px] transition
				{hovering ? 'border-brand-600 bg-brand-100/80' : 'border-brand-300 bg-white/70'}"
		>
			<ShoppingCart class="size-9 text-brand-600 {hovering ? 'animate-bounce' : ''}" />
			<p class="mt-2 font-bold text-brand-700">{t('cart.dropHere')}</p>
			<p class="text-sm text-brand-700/80">{t('cart.dropHint')}</p>
		</div>
	{/if}
</section>

<ConfirmDialog
	bind:open={confirmClear}
	title={t('cart.clear')}
	message={t('cart.clearConfirm')}
	confirmLabel={t('cart.clear')}
	onconfirm={clear}
/>
