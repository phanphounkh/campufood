<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import Receipt from '@lucide/svelte/icons/receipt';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import Smartphone from '@lucide/svelte/icons/smartphone';
	import StatusBadge from '#lib/components/ui/StatusBadge.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import Skeleton from '#lib/components/ui/Skeleton.svelte';
	import { getOrder, myOrders } from '#lib/services/orders.ts';
	import { ApiError } from '#lib/services/api.ts';
	import { forgetOrder, rememberedOrders } from '#lib/stores/guestOrders.ts';
	import type { Order } from '#lib/types/api.ts';
	import { formatDateTime } from '#lib/utils/format.ts';
	import { formatMoney } from '#lib/utils/money.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';

	let orders = $state<Order[]>([]);
	let loading = $state(true);
	const user = $derived(page.data.user);

	onMount(async () => {
		const byId: Record<string, Order> = {};
		const remembered = rememberedOrders();
		const results = await Promise.allSettled(remembered.map((o) => getOrder(o.id, o.token)));
		results.forEach((result, i) => {
			if (result.status === 'fulfilled') byId[result.value.id] = result.value;
			else if (result.reason instanceof ApiError && result.reason.status === 404)
				forgetOrder(remembered[i].id);
		});
		if (user) {
			try {
				for (const order of (await myOrders()).items) byId[order.id] = order;
			} catch {
				/* show device orders only */
			}
		}
		orders = Object.values(byId).sort((a, b) => b.created_at.localeCompare(a.created_at));
		loading = false;
	});

	const summary = (order: Order) =>
		order.items
			.map(
				(i) =>
					`${i18n.locale === 'km' ? i.food_name_km_snapshot || i.food_name_snapshot : i.food_name_snapshot} ×${i.quantity}`
			)
			.join(', ');
</script>

<svelte:head><title>{t('orders.title')} · CampusEats</title></svelte:head>

<div class="container-page max-w-3xl py-8">
	<h1 class="text-3xl font-extrabold tracking-tight">{t('orders.title')}</h1>
	<p class="mt-1 text-ink-muted">{t('orders.subtitle')}</p>

	<div class="mt-6 space-y-3" data-testid="orders-list">
		{#if loading}
			{#each [1, 2, 3] as i (i)}<Skeleton class="h-24 w-full" />{/each}
		{:else if orders.length === 0}
			<div class="card">
				<EmptyState icon={Receipt} title={t('orders.empty')} text={t('orders.emptyHint')}>
					<a href="/menu" class="btn btn-primary">{t('cart.browse')}</a>
				</EmptyState>
			</div>
		{:else}
			{#each orders as order (order.id)}
				<a
					href={order.status === 'pending_payment'
						? `/orders/${order.id}/pay`
						: `/orders/${order.id}`}
					class="card flex items-center gap-4 p-4 transition hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-lift sm:p-5"
				>
					<span
						class="hidden size-12 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600 sm:grid"
					>
						<Receipt class="size-5" />
					</span>
					<div class="min-w-0 flex-1">
						<div class="flex flex-wrap items-center gap-2">
							<span class="font-extrabold">{order.order_number}</span>
							<StatusBadge status={order.status} />
						</div>
						<p class="mt-1 truncate text-sm text-ink-soft" lang={i18n.locale}>{summary(order)}</p>
						<p class="text-xs text-ink-muted">{formatDateTime(order.created_at, i18n.locale)}</p>
					</div>
					<div class="text-right">
						<p class="font-extrabold text-brand-600">{formatMoney(order.total)}</p>
						{#if order.status === 'pending_payment'}
							<span class="text-xs font-semibold text-amber-700">{t('orders.pay')}</span>
						{/if}
					</div>
					<ChevronRight class="size-5 text-ink-muted" />
				</a>
			{/each}
		{/if}
	</div>

	{#if !user}
		<p class="mt-6 flex items-center justify-center gap-2 text-center text-sm text-ink-muted">
			<Smartphone class="size-4" />{t('orders.guestNote')}
			<a href="/login?next=/orders" class="font-semibold text-brand-700 hover:underline"
				>{t('nav.login')}</a
			>
		</p>
	{/if}
</div>
