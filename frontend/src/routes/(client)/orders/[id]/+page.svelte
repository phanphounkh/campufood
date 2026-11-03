<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Check from '@lucide/svelte/icons/check';
	import Clock from '@lucide/svelte/icons/clock';
	import Copy from '@lucide/svelte/icons/copy';
	import BellRing from '@lucide/svelte/icons/bell-ring';
	import CircleX from '@lucide/svelte/icons/circle-x';
	import SearchX from '@lucide/svelte/icons/search-x';
	import QrCode from '@lucide/svelte/icons/qr-code';
	import Radio from '@lucide/svelte/icons/radio';
	import StatusBadge from '#lib/components/ui/StatusBadge.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import { getOrder } from '#lib/services/orders.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import type { Order, OrderStatus } from '#lib/types/api.ts';
	import { formatDateTime, formatTime } from '#lib/utils/format.ts';
	import { formatMoney } from '#lib/utils/money.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	// svelte-ignore state_referenced_locally
	let order = $state<Order | null>(data.order);
	// svelte-ignore state_referenced_locally
	const token = data.token;

	const steps: OrderStatus[] = ['pending_payment', 'confirmed', 'preparing', 'ready', 'completed'];
	const current = $derived(order ? steps.indexOf(order.status) : -1);
	const final = $derived(order?.status === 'completed' || order?.status === 'cancelled');

	let timer: ReturnType<typeof setInterval> | undefined;
	onMount(() => {
		// Polling keeps the page live; WebSockets can replace this later.
		timer = setInterval(async () => {
			if (!order || final || document.hidden) return;
			try {
				const next = await getOrder(order.id, token);
				if (next.status !== order.status && next.status === 'ready')
					toast.success(t('orders.readyBanner'));
				order = next;
			} catch {
				/* retry next tick */
			}
		}, 5000);
	});
	onDestroy(() => clearInterval(timer));

	async function copyLink() {
		if (!order || !token) return;
		const url = `${location.origin}/orders/${order.id}#t=${token}`;
		await navigator.clipboard.writeText(url);
		toast.success(t('orders.linkCopied'));
	}

	const itemName = (item: Order['items'][number]) =>
		i18n.locale === 'km'
			? item.food_name_km_snapshot || item.food_name_snapshot
			: item.food_name_snapshot;
</script>

<svelte:head
	><title
		>{order ? t('orders.number', { number: order.order_number }) : t('orders.notFound')} · CampusEats</title
	></svelte:head
>

<div class="container-page max-w-3xl py-8">
	<a href="/orders" class="btn btn-ghost -ml-3"><ArrowLeft class="size-4" />{t('nav.orders')}</a>

	{#if !order}
		<div class="card mt-4">
			<EmptyState icon={SearchX} title={t('orders.notFound')} text={t('orders.notFoundText')}>
				<a href="/menu" class="btn btn-primary">{t('cart.browse')}</a>
			</EmptyState>
		</div>
	{:else}
		<header class="mt-3 flex flex-wrap items-start justify-between gap-4">
			<div>
				<h1 class="text-3xl font-extrabold tracking-tight" data-testid="order-number">
					{t('orders.number', { number: order.order_number })}
				</h1>
				<p class="mt-1 text-sm text-ink-muted">
					{t('orders.placedAt', { time: formatDateTime(order.created_at, i18n.locale) })}
				</p>
			</div>
			<div class="flex items-center gap-2">
				{#if !final}
					<span class="chip bg-green-50 text-success-ink"
						><Radio class="size-3 animate-pulse" />{t('orders.liveUpdates')}</span
					>
				{/if}
				<StatusBadge status={order.status} size="md" />
			</div>
		</header>

		{#if order.status === 'ready'}
			<p
				class="mt-5 flex items-center gap-3 rounded-2xl bg-emerald-50 p-4 font-semibold text-emerald-900"
				role="status"
			>
				<BellRing class="size-5 animate-bounce" />{t('orders.readyBanner')}
			</p>
		{/if}

		<section class="card mt-6 p-5 sm:p-6" aria-label={t('orders.status')}>
			{#if order.status === 'cancelled'}
				<div class="flex items-start gap-4">
					<span
						class="grid size-12 shrink-0 place-items-center rounded-2xl bg-slate-100 text-slate-500"
						><CircleX class="size-6" /></span
					>
					<div>
						<p class="text-lg font-bold">{t('status.cancelled')}</p>
						{#if order.cancel_reason}
							<p class="text-sm text-ink-muted">
								{t('orders.cancelReason', { reason: order.cancel_reason })}
							</p>
						{/if}
						{#if order.payment?.status === 'refunded'}
							<p class="mt-2"><StatusBadge status="refunded" kind="payment" /></p>
						{/if}
					</div>
				</div>
			{:else}
				<ol class="grid grid-cols-5 gap-1" data-testid="order-timeline">
					{#each steps as step, i (step)}
						{@const done = i < current || order.status === 'completed'}
						{@const active = i === current && order.status !== 'completed'}
						<li class="relative flex flex-col items-center text-center">
							{#if i > 0}
								<span
									class="absolute top-4 right-1/2 -z-0 h-1 w-full -translate-y-1/2 rounded-full {i <=
									current
										? 'bg-brand-500'
										: 'bg-line'}"
									aria-hidden="true"
								></span>
							{/if}
							<span
								class="relative z-10 grid size-8 place-items-center rounded-full text-sm font-bold ring-4 ring-white transition
									{done
									? 'bg-brand-600 text-white'
									: active
										? 'bg-brand-600 text-white shadow-[0_0_0_6px_rgb(100_37_216/0.15)]'
										: 'bg-line text-ink-muted'}"
								aria-current={active ? 'step' : undefined}
							>
								{#if done}<Check class="size-4" />{:else}{i + 1}{/if}
							</span>
							<span
								class="mt-2 text-[11px] leading-tight font-semibold sm:text-xs {active
									? 'text-brand-700'
									: done
										? 'text-ink'
										: 'text-ink-muted'}"
							>
								{t(`status.${step}`)}
							</span>
						</li>
					{/each}
				</ol>
			{/if}

			<dl class="mt-6 grid gap-4 border-t border-line pt-5 sm:grid-cols-3">
				<div>
					<dt class="text-xs font-semibold text-ink-muted uppercase">{t('orders.pickupAt')}</dt>
					<dd class="mt-1 flex items-center gap-1.5 text-lg font-bold">
						<Clock class="size-4 text-brand-600" />{formatTime(order.pickup_time, i18n.locale)}
					</dd>
				</div>
				<div>
					<dt class="text-xs font-semibold text-ink-muted uppercase">{t('orders.payment')}</dt>
					<dd class="mt-1.5">
						{#if order.payment}<StatusBadge status={order.payment.status} kind="payment" />{/if}
					</dd>
				</div>
				<div>
					<dt class="text-xs font-semibold text-ink-muted uppercase">{t('orders.customer')}</dt>
					<dd class="mt-1 font-semibold">{order.customer_name}</dd>
				</div>
			</dl>

			{#if order.status === 'pending_payment'}
				<a href="/orders/{order.id}/pay" class="btn btn-primary btn-lg mt-6 w-full"
					><QrCode class="size-4" />{t('orders.pay')}</a
				>
			{/if}
		</section>

		<section class="card mt-5 p-5 sm:p-6">
			<h2 class="font-bold">{t('orders.items')}</h2>
			<ul class="mt-3 divide-y divide-line">
				{#each order.items as item (item.id)}
					<li class="flex items-center justify-between gap-4 py-3">
						<div>
							<p class="font-semibold" lang={i18n.locale}>{itemName(item)}</p>
							<p class="text-sm text-ink-muted">{formatMoney(item.unit_price)} × {item.quantity}</p>
						</div>
						<p class="font-bold tabular-nums">{formatMoney(item.line_total)}</p>
					</li>
				{/each}
			</ul>
			<div class="mt-2 flex items-baseline justify-between border-t border-line pt-4">
				<span class="text-lg font-extrabold">{t('cart.total')}</span>
				<span class="text-2xl font-extrabold text-brand-600">{formatMoney(order.total)}</span>
			</div>
			{#if order.notes}
				<p class="mt-4 rounded-xl bg-brand-50/70 p-3 text-sm">
					<span class="font-semibold">{t('orders.notes')}:</span>
					{order.notes}
				</p>
			{/if}
		</section>

		{#if token}
			<div class="mt-4 text-center">
				<button type="button" class="btn btn-ghost" onclick={copyLink}
					><Copy class="size-4" />{t('orders.shareLink')}</button
				>
			</div>
		{/if}
	{/if}
</div>
