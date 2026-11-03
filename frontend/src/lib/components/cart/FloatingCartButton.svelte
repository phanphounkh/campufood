<script lang="ts">
	import { fly } from 'svelte/transition';
	import ShoppingCart from '@lucide/svelte/icons/shopping-cart';
	import { cart } from '#lib/stores/cart.svelte.ts';
	import { drag, dropZone } from '#lib/stores/dnd.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import { formatCents } from '#lib/utils/money.ts';

	/** Mobile/tablet cart: always reachable, and a drop target while dragging food. */
	let button: HTMLButtonElement | undefined = $state();
	const hovering = $derived(drag.dragging && drag.activeZone === button);
	const visible = $derived(cart.count > 0 || drag.dragging);
</script>

{#if visible}
	<div
		class="fixed inset-x-0 bottom-4 z-40 flex justify-center px-4 lg:hidden"
		transition:fly={{ y: 40, duration: 250 }}
	>
		<button
			bind:this={button}
			use:dropZone
			type="button"
			class="flex w-full max-w-md items-center gap-3 rounded-2xl px-4 py-3 text-white shadow-[0_16px_32px_-12px_rgb(100_37_216/0.7)] transition
				{hovering ? 'scale-105 bg-brand-800 ring-4 ring-brand-200' : 'bg-brand-600'}"
			aria-label={t('nav.cartWithCount', { count: cart.count })}
			data-testid="floating-cart"
			onclick={() => (cart.drawerOpen = true)}
		>
			<span class="relative grid size-10 place-items-center rounded-xl bg-white/15">
				{#key cart.pulse}
					<ShoppingCart class="size-5 animate-pop" />
				{/key}
				<span
					class="absolute -top-1.5 -right-1.5 grid min-w-5 place-items-center rounded-full bg-white px-1 text-xs font-bold text-brand-700"
				>
					{cart.count}
				</span>
			</span>
			<span class="flex-1 text-left font-semibold">
				{drag.dragging ? t('cart.dropHere') : t('cart.view')}
			</span>
			<span class="text-lg font-extrabold tabular-nums">{formatCents(cart.totalCents)}</span>
		</button>
	</div>
{/if}
