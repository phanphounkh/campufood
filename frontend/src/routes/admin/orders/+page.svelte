<script lang="ts">
	import { adminHref } from '#lib/components/admin/links.ts';
	import { onMount } from 'svelte';
	import { goto, invalidate } from '$app/navigation';
	import { page } from '$app/state';
	import ClipboardList from '@lucide/svelte/icons/clipboard-list';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import PageHeader from '#lib/components/admin/PageHeader.svelte';
	import ErrorState from '#lib/components/admin/ErrorState.svelte';
	import SearchInput from '#lib/components/admin/SearchInput.svelte';
	import Pagination from '#lib/components/admin/Pagination.svelte';
	import OrderActions from '#lib/components/admin/OrderActions.svelte';
	import OrderDrawer from '#lib/components/admin/OrderDrawer.svelte';
	import CancelOrderDialog from '#lib/components/admin/CancelOrderDialog.svelte';
	import { adminState } from '#lib/components/admin/state.svelte.ts';
	import { errorMessage } from '#lib/components/admin/errors.ts';
	import { itemCount, itemName, ORDER_STATUSES } from '#lib/components/admin/orderFlow.ts';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import StatusBadge from '#lib/components/ui/StatusBadge.svelte';
	import { getAdminOrder } from '#lib/services/orders.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { usd } from '#lib/components/admin/format.ts';
	import { formatDateTime, formatTime, isToday } from '#lib/utils/format.ts';
	import type { Order, OrderStatus } from '#lib/types/api.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	// Keep the sidebar badge in sync with what this page just loaded.
	$effect(() => {
		if (data.summary) adminState.summary = data.summary;
	});

	function href(changes: {
		status?: OrderStatus | null;
		q?: string;
		page?: number;
		open?: string | null;
	}) {
		const current = {
			status: data.status,
			q: data.q,
			page: data.page,
			open: page.url.searchParams.get('open')
		};
		const next = { ...current, ...changes };
		if ('status' in changes || 'q' in changes) next.page = 1;
		return adminHref('/admin/orders', {
			status: next.status,
			q: next.q,
			page: next.page && next.page > 1 ? next.page : null,
			open: next.open
		});
	}

	// ── Detail drawer (?open=<id>) ────────────────────────────────
	const openId = $derived(page.url.searchParams.get('open'));
	let drawerOpen = $state(false);
	let fetched = $state<Order | null>(null);
	let drawerLoading = $state(false);
	let drawerError = $state('');
	const drawerOrder = $derived(
		(openId && data.orders?.items.find((o) => o.id === openId)) ||
			(fetched?.id === openId ? fetched : null)
	);

	$effect(() => {
		drawerOpen = !!openId;
		if (!openId || data.orders?.items.some((o) => o.id === openId) || fetched?.id === openId)
			return;
		const id = openId;
		drawerLoading = true;
		drawerError = '';
		getAdminOrder(id)
			.then((order) => {
				if (openId === id) fetched = order;
			})
			.catch((err) => (drawerError = errorMessage(err)))
			.finally(() => (drawerLoading = false));
	});

	function closeDrawer() {
		if (openId) goto(href({ open: null }), { replace: true, reset: false });
	}

	// ── Mutations ─────────────────────────────────────────────────
	let cancelTarget = $state<Order | null>(null);
	let cancelOpen = $state(false);

	function askCancel(order: Order) {
		cancelTarget = order;
		cancelOpen = true;
	}

	async function refresh() {
		await Promise.all([invalidate('admin:orders'), adminState.refreshSummary()]);
	}

	function onchanged(order: Order) {
		if (fetched?.id === order.id) fetched = order;
		refresh();
	}

	let refreshing = $state(false);
	async function manualRefresh() {
		refreshing = true;
		await refresh();
		refreshing = false;
	}

	onMount(() => {
		const timer = setInterval(() => {
			if (document.visibilityState === 'visible' && !cancelOpen) refresh();
		}, 15_000);
		return () => clearInterval(timer);
	});

	const tabs: (OrderStatus | null)[] = [null, ...ORDER_STATUSES];
	const counts = $derived(data.summary ?? adminState.summary);
	const time = (iso: string) =>
		isToday(iso) ? formatTime(iso, i18n.locale) : formatDateTime(iso, i18n.locale);
</script>

<svelte:head><title>{t('admin.orders.title')} · {t('admin.title')}</title></svelte:head>

<PageHeader title={t('admin.orders.title')} subtitle={t('admin.orders.subtitle')}>
	{#snippet actions()}
		<span class="hidden text-xs text-ink-muted sm:inline">{t('admin.orders.autoRefresh')}</span>
		<button
			type="button"
			class="btn btn-secondary btn-sm"
			onclick={manualRefresh}
			disabled={refreshing}
		>
			<RefreshCw class="size-4 {refreshing ? 'animate-spin' : ''}" />{t('admin.refresh')}
		</button>
	{/snippet}
</PageHeader>

<div class="card overflow-hidden">
	<div class="flex flex-col gap-3 border-b border-line p-4">
		<nav
			class="-mx-1 flex gap-1 overflow-x-auto px-1 pb-1"
			aria-label={t('admin.orders.statusTabs')}
		>
			{#each tabs as tab (tab ?? 'all')}
				{@const active = data.status === tab}
				{@const count = counts ? counts[tab ?? 'all'] : null}
				<a
					href={href({ status: tab })}
					aria-current={active ? 'page' : undefined}
					class="flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-semibold whitespace-nowrap transition
						{active
						? 'bg-brand-50 text-brand-700 ring-1 ring-brand-200'
						: 'text-ink-muted hover:bg-canvas hover:text-ink'}"
				>
					{tab ? t(`status.${tab}`) : t('admin.all')}
					{#if count !== null && count !== undefined}
						<span
							class="rounded-full px-1.5 text-xs tabular-nums {active
								? 'bg-brand-600 text-white'
								: tab === 'confirmed' && count > 0
									? 'bg-danger-ink text-white'
									: 'bg-canvas text-ink-muted'}">{count}</span
						>
					{/if}
				</a>
			{/each}
		</nav>
		<SearchInput
			class="w-full sm:w-96"
			value={data.q}
			placeholder={t('admin.orders.search')}
			onsearch={(q) => goto(href({ q }), { replace: true, reset: false })}
		/>
	</div>

	{#if data.error || !data.orders}
		<div class="p-4"><ErrorState message={data.error ?? ''} /></div>
	{:else if data.orders.items.length === 0}
		<EmptyState
			icon={ClipboardList}
			title={t('admin.orders.empty')}
			text={t('admin.orders.emptyHint')}
		/>
	{:else}
		<!-- Phones & small tablets: one card per order with the next action within thumb reach -->
		<ul class="divide-y divide-line md:hidden">
			{#each data.orders.items as order (order.id)}
				<li class="space-y-3 p-4 {order.status === 'confirmed' ? 'bg-brand-50/40' : ''}">
					<div class="flex items-start justify-between gap-3">
						<a href={href({ open: order.id })} class="min-w-0">
							<p class="font-bold text-ink">{order.order_number}</p>
							<p class="truncate text-sm text-ink-soft">
								{order.customer_name} · <span class="tabular-nums">{order.customer_phone}</span>
							</p>
						</a>
						<p class="shrink-0 text-right">
							<span class="block font-bold tabular-nums">{usd(order.total)}</span>
							<span class="text-xs text-ink-muted">{time(order.created_at)}</span>
						</p>
					</div>
					<p class="text-sm text-ink-soft" lang={i18n.locale}>
						{order.items.map((i) => `${itemName(i, i18n.locale)} ×${i.quantity}`).join(', ')}
					</p>
					<div class="flex flex-wrap items-center justify-between gap-2">
						<div class="flex flex-wrap gap-1.5">
							<StatusBadge status={order.status} />
							{#if order.payment}<StatusBadge status={order.payment.status} kind="payment" />{/if}
						</div>
						<OrderActions {order} {onchanged} oncancel={askCancel} />
					</div>
				</li>
			{/each}
		</ul>

		<div class="hidden overflow-x-auto md:block">
			<table class="w-full min-w-[1120px] text-left text-sm">
				<thead class="bg-canvas text-xs font-semibold whitespace-nowrap text-ink-muted">
					<tr>
						<th class="px-4 py-3">{t('admin.col.order')}</th>
						<th class="px-3 py-3">{t('admin.col.customer')}</th>
						<th class="px-3 py-3">{t('admin.col.items')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.qty')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.total')}</th>
						<th class="px-3 py-3">{t('admin.col.payment')}</th>
						<th class="px-3 py-3">{t('admin.col.status')}</th>
						<th class="px-3 py-3">{t('admin.col.created')}</th>
						<th class="px-4 py-3 text-right">{t('admin.col.actions')}</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-line">
					{#each data.orders.items as order (order.id)}
						<tr
							class="align-middle transition hover:bg-canvas/60 {order.status === 'confirmed'
								? 'bg-brand-50/40'
								: ''}"
						>
							<td class="px-4 py-3">
								<a
									href={href({ open: order.id })}
									class="font-bold whitespace-nowrap text-ink hover:text-brand-700 hover:underline"
								>
									{order.order_number}
								</a>
							</td>
							<td class="px-3 py-3">
								<p class="font-semibold whitespace-nowrap text-ink">{order.customer_name}</p>
								<p class="text-xs text-ink-muted tabular-nums">{order.customer_phone}</p>
							</td>
							<td class="max-w-[280px] px-3 py-3 text-ink-soft">
								<p class="line-clamp-2" lang={i18n.locale}>
									{order.items.map((i) => `${itemName(i, i18n.locale)} ×${i.quantity}`).join(', ')}
								</p>
							</td>
							<td class="px-3 py-3 text-right tabular-nums">{itemCount(order)}</td>
							<td class="px-3 py-3 text-right font-semibold tabular-nums">{usd(order.total)}</td>
							<td class="px-3 py-3">
								{#if order.payment}<StatusBadge status={order.payment.status} kind="payment" />{/if}
							</td>
							<td class="px-3 py-3"><StatusBadge status={order.status} /></td>
							<td class="px-3 py-3 whitespace-nowrap text-ink-muted">{time(order.created_at)}</td>
							<td class="px-4 py-3">
								<div class="flex items-center justify-end gap-1.5">
									<OrderActions {order} {onchanged} oncancel={askCancel} />
									<a href={href({ open: order.id })} class="btn btn-ghost btn-sm"
										>{t('admin.view')}</a
									>
								</div>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<Pagination
			page={data.page}
			pageSize={data.pageSize}
			total={data.orders.total}
			href={(p) => href({ page: p })}
		/>
	{/if}
</div>

<OrderDrawer
	bind:open={drawerOpen}
	order={drawerOrder}
	loading={drawerLoading && !drawerOrder}
	error={drawerError}
	onclose={closeDrawer}
	{onchanged}
	oncancel={askCancel}
/>

<CancelOrderDialog bind:open={cancelOpen} order={cancelTarget} oncancelled={onchanged} />
