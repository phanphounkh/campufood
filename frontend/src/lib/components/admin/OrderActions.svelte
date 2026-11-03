<script lang="ts">
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import { updateOrderStatus } from '#lib/services/orders.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import type { Order } from '#lib/types/api.ts';
	import { reportError } from './errors.ts';
	import { CANCELLABLE, NEXT_STEP } from './orderFlow.ts';

	let {
		order,
		size = 'sm',
		onchanged,
		oncancel
	}: {
		order: Order;
		size?: 'sm' | 'md';
		onchanged: (order: Order) => void;
		oncancel: (order: Order) => void;
	} = $props();

	let busy = $state(false);
	const next = $derived(NEXT_STEP[order.status]);
	const canCancel = $derived(CANCELLABLE.includes(order.status));

	async function advance() {
		if (!next) return;
		busy = true;
		try {
			const updated = await updateOrderStatus(order.id, next.to);
			toast.success(
				t('admin.orders.updated', {
					number: updated.order_number,
					status: t(`status.${updated.status}`)
				})
			);
			onchanged(updated);
		} catch (err) {
			reportError(err);
		} finally {
			busy = false;
		}
	}
</script>

<div class="flex items-center justify-end gap-1.5">
	{#if next}
		<button
			type="button"
			class="btn btn-primary {size === 'sm' ? 'btn-sm' : ''}"
			disabled={busy}
			onclick={advance}
		>
			{#if busy}<LoaderCircle class="size-3.5 animate-spin" />{:else}<Check class="size-3.5" />{/if}
			{t(next.labelKey)}
		</button>
	{:else if order.status === 'pending_payment'}
		<span class="text-xs font-medium whitespace-nowrap text-amber-700"
			>{t('admin.orders.awaitingPayment')}</span
		>
	{:else}
		<span class="text-xs whitespace-nowrap text-ink-muted">{t('admin.orders.final')}</span>
	{/if}
	{#if canCancel}
		{#if size === 'sm'}
			<button
				type="button"
				class="grid size-8 place-items-center rounded-lg text-ink-muted transition hover:bg-red-50 hover:text-danger-ink"
				aria-label={t('admin.orders.cancelNamed', { number: order.order_number })}
				title={t('admin.orders.cancel')}
				disabled={busy}
				onclick={() => oncancel(order)}
			>
				<X class="size-4" />
			</button>
		{:else}
			<button
				type="button"
				class="btn btn-secondary text-danger-ink"
				disabled={busy}
				onclick={() => oncancel(order)}
			>
				<X class="size-4" />{t('admin.orders.cancel')}
			</button>
		{/if}
	{/if}
</div>
