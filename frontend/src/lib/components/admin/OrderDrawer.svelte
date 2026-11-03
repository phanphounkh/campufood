<script lang="ts">
	import Phone from '@lucide/svelte/icons/phone';
	import Clock from '@lucide/svelte/icons/clock';
	import IdCard from '@lucide/svelte/icons/id-card';
	import StickyNote from '@lucide/svelte/icons/sticky-note';
	import Modal from '#lib/components/ui/Modal.svelte';
	import Skeleton from '#lib/components/ui/Skeleton.svelte';
	import StatusBadge from '#lib/components/ui/StatusBadge.svelte';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { usd } from '#lib/components/admin/format.ts';
	import { formatDateTime } from '#lib/utils/format.ts';
	import type { Order } from '#lib/types/api.ts';
	import OrderActions from './OrderActions.svelte';
	import { itemName } from './orderFlow.ts';

	let {
		open = $bindable(false),
		order,
		loading = false,
		error = '',
		onclose,
		onchanged,
		oncancel
	}: {
		open?: boolean;
		order: Order | null;
		loading?: boolean;
		error?: string;
		onclose: () => void;
		onchanged: (order: Order) => void;
		oncancel: (order: Order) => void;
	} = $props();
</script>

<Modal
	bind:open
	variant="drawer"
	title={order ? t('admin.orders.detail', { number: order.order_number }) : t('common.loading')}
	description={order
		? t('admin.orders.detailSub', { time: formatDateTime(order.created_at, i18n.locale) })
		: undefined}
	{onclose}
>
	{#if loading}
		<div class="space-y-3">
			<Skeleton class="h-6 w-1/2" />
			<Skeleton class="h-24 w-full" />
			<Skeleton class="h-40 w-full" />
		</div>
	{:else if error || !order}
		<p class="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
			{error || t('admin.orders.notFound')}
		</p>
	{:else}
		<div class="flex flex-wrap items-center gap-2">
			<StatusBadge status={order.status} size="md" />
			{#if order.payment}<StatusBadge status={order.payment.status} kind="payment" size="md" />{/if}
		</div>

		{#if order.cancel_reason}
			<div class="mt-4 rounded-xl border border-line bg-canvas px-4 py-3 text-sm">
				<p class="font-semibold text-ink">{t('admin.orders.cancelReason')}</p>
				<p class="text-ink-soft">{order.cancel_reason}</p>
			</div>
		{/if}

		<dl class="mt-5 grid gap-3 text-sm">
			<div class="flex items-start gap-3">
				<dt class="sr-only">{t('admin.col.customer')}</dt>
				<span class="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600"
					><Phone class="size-4" /></span
				>
				<dd>
					<p class="font-semibold text-ink">{order.customer_name}</p>
					<a class="text-brand-700 hover:underline" href="tel:{order.customer_phone}"
						>{order.customer_phone}</a
					>
					<p class="text-xs text-ink-muted">
						{order.user_id ? t('admin.orders.registered') : t('admin.orders.guest')}
					</p>
				</dd>
			</div>
			<div class="flex items-start gap-3">
				<dt class="sr-only">{t('admin.orders.pickup')}</dt>
				<span class="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600"
					><Clock class="size-4" /></span
				>
				<dd>
					<p class="text-xs text-ink-muted">{t('admin.orders.pickup')}</p>
					<p class="font-semibold text-ink">{formatDateTime(order.pickup_time, i18n.locale)}</p>
				</dd>
			</div>
			{#if order.student_id}
				<div class="flex items-start gap-3">
					<dt class="sr-only">{t('admin.orders.studentId')}</dt>
					<span
						class="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600"
						><IdCard class="size-4" /></span
					>
					<dd>
						<p class="text-xs text-ink-muted">{t('admin.orders.studentId')}</p>
						<p class="font-semibold text-ink">{order.student_id}</p>
					</dd>
				</div>
			{/if}
			<div class="flex items-start gap-3">
				<dt class="sr-only">{t('admin.orders.notes')}</dt>
				<span class="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-600"
					><StickyNote class="size-4" /></span
				>
				<dd>
					<p class="text-xs text-ink-muted">{t('admin.orders.notes')}</p>
					<p class="text-ink {order.notes ? 'font-semibold' : 'text-ink-muted'}">
						{order.notes ?? t('admin.orders.noNotes')}
					</p>
				</dd>
			</div>
		</dl>

		<h3 class="mt-6 text-sm font-bold text-ink">{t('admin.col.items')}</h3>
		<ul class="mt-2 divide-y divide-line rounded-xl border border-line">
			{#each order.items as item (item.id)}
				<li class="flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
					<span class="min-w-0">
						<span class="font-semibold text-ink" lang={i18n.locale}
							>{itemName(item, i18n.locale)}</span
						>
						<span class="block text-xs text-ink-muted tabular-nums">
							{item.quantity} × {usd(item.unit_price)}
						</span>
					</span>
					<span class="font-semibold tabular-nums">{usd(item.line_total)}</span>
				</li>
			{/each}
			<li class="flex items-center justify-between px-4 py-3 text-sm font-extrabold">
				<span>{t('admin.orders.total')}</span>
				<span class="text-brand-700 tabular-nums">{usd(order.total)}</span>
			</li>
		</ul>

		{#if order.payment}
			<h3 class="mt-6 text-sm font-bold text-ink">{t('admin.orders.paymentInfo')}</h3>
			<dl
				class="mt-2 grid grid-cols-2 gap-x-4 gap-y-2 rounded-xl border border-line px-4 py-3 text-sm"
			>
				<dt class="text-ink-muted">{t('admin.col.provider')}</dt>
				<dd class="text-right font-semibold">{t('admin.payments.providerDemo')}</dd>
				<dt class="text-ink-muted">{t('admin.col.amount')}</dt>
				<dd class="text-right font-semibold tabular-nums">{usd(order.payment.amount)}</dd>
				<dt class="text-ink-muted">{t('admin.orders.reference')}</dt>
				<dd class="truncate text-right font-mono text-xs leading-5">
					{order.payment.transaction_reference ?? '—'}
				</dd>
				<dt class="text-ink-muted">{t('admin.orders.paidAt')}</dt>
				<dd class="text-right">
					{order.payment.paid_at ? formatDateTime(order.payment.paid_at, i18n.locale) : '—'}
				</dd>
			</dl>
		{/if}
	{/if}

	{#snippet footer()}
		{#if order && !loading}
			<OrderActions {order} size="md" {onchanged} {oncancel} />
		{/if}
	{/snippet}
</Modal>
