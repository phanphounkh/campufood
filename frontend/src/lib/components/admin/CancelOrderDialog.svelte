<script lang="ts">
	import ConfirmDialog from '#lib/components/ui/ConfirmDialog.svelte';
	import { updateOrderStatus } from '#lib/services/orders.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import type { Order } from '#lib/types/api.ts';
	import { reportError } from './errors.ts';
	import { isPaid } from './orderFlow.ts';

	let {
		order,
		open = $bindable(false),
		oncancelled
	}: {
		order: Order | null;
		open?: boolean;
		oncancelled: (order: Order) => void;
	} = $props();

	let reason = $state('');
	let error = $state('');
	let busy = $state(false);

	const presets = [
		'admin.orders.reasonStock',
		'admin.orders.reasonCustomer',
		'admin.orders.reasonClosing'
	];

	$effect(() => {
		if (open) {
			reason = '';
			error = '';
		}
	});

	async function confirm() {
		if (!order) return;
		if (reason.trim().length < 3) {
			error = t('admin.orders.reasonRequired');
			return;
		}
		busy = true;
		try {
			const updated = await updateOrderStatus(order.id, 'cancelled', reason.trim());
			toast.success(t('admin.orders.cancelled', { number: updated.order_number }));
			open = false;
			oncancelled(updated);
		} catch (err) {
			reportError(err);
		} finally {
			busy = false;
		}
	}
</script>

<ConfirmDialog
	bind:open
	title={t('admin.orders.cancelTitle', { number: order?.order_number ?? '' })}
	message={order && isPaid(order)
		? t('admin.orders.cancelTextPaid')
		: t('admin.orders.cancelTextUnpaid')}
	confirmLabel={t('admin.orders.confirmCancel')}
	{busy}
	onconfirm={confirm}
>
	<div class="mt-4">
		<label class="label" for="cancel-reason">{t('admin.orders.reason')}</label>
		<textarea
			id="cancel-reason"
			rows="2"
			maxlength="300"
			class="w-full text-sm"
			placeholder={t('admin.orders.reasonPlaceholder')}
			bind:value={reason}
			aria-invalid={!!error}
			aria-describedby={error ? 'cancel-reason-error' : undefined}></textarea>
		{#if error}<p id="cancel-reason-error" class="field-error">{error}</p>{/if}
		<div class="mt-2 flex flex-wrap gap-1.5">
			{#each presets as key (key)}
				<button
					type="button"
					class="chip border border-line bg-white px-2.5 py-1 text-ink-soft hover:border-brand-200 hover:bg-brand-50"
					onclick={() => {
						reason = t(key);
						error = '';
					}}
				>
					{t(key)}
				</button>
			{/each}
		</div>
	</div>
</ConfirmDialog>
