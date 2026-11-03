<script lang="ts">
	import { adminHref } from '#lib/components/admin/links.ts';
	import { onMount } from 'svelte';
	import { invalidate } from '$app/navigation';
	import ClipboardList from '@lucide/svelte/icons/clipboard-list';
	import CircleDollarSign from '@lucide/svelte/icons/circle-dollar-sign';
	import Hourglass from '@lucide/svelte/icons/hourglass';
	import PackageCheck from '@lucide/svelte/icons/package-check';
	import Receipt from '@lucide/svelte/icons/receipt';
	import ChefHat from '@lucide/svelte/icons/chef-hat';
	import Wallet from '@lucide/svelte/icons/wallet';
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import PageHeader from '#lib/components/admin/PageHeader.svelte';
	import KpiCard from '#lib/components/admin/KpiCard.svelte';
	import ErrorState from '#lib/components/admin/ErrorState.svelte';
	import AreaChart from '#lib/components/admin/charts/AreaChart.svelte';
	import ColumnChart from '#lib/components/admin/charts/ColumnChart.svelte';
	import HBarList from '#lib/components/admin/charts/HBarList.svelte';
	import { axisMoney } from '#lib/components/admin/charts/scale.ts';
	import { orderPoints, revenuePoints } from '#lib/components/admin/chartData.ts';
	import FoodImage from '#lib/components/ui/FoodImage.svelte';
	import StatusBadge from '#lib/components/ui/StatusBadge.svelte';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { usd, usdCents } from '#lib/components/admin/format.ts';
	import { formatDateTime, formatTime, isToday } from '#lib/utils/format.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const ranges = ['today', '7d', '30d'] as const;
	const d = $derived(data.dashboard);
	const comparison = $derived(t(`admin.vs.${data.range}`));

	const salesPoints = $derived(
		d ? orderPoints(d.sales_over_time, i18n.locale, (revenue) => usd(revenue)) : []
	);
	const dailyPoints = $derived(
		d
			? revenuePoints(d.daily_revenue, i18n.locale, (orders) =>
					t('admin.chart.ordersCount', { count: orders })
				)
			: []
	);
	const statusRows = $derived(
		d ? d.orders_by_status.map((s) => ({ label: t(`status.${s.status}`), value: s.count })) : []
	);
	const maxPopular = $derived(Math.max(1, ...(d?.popular_items.map((p) => p.quantity) ?? [1])));

	onMount(() => {
		const timer = setInterval(() => {
			if (document.visibilityState === 'visible') invalidate('admin:dashboard');
		}, 60_000);
		return () => clearInterval(timer);
	});
</script>

<svelte:head><title>{t('admin.dashboard.title')} · {t('admin.title')}</title></svelte:head>

<PageHeader title={t('admin.dashboard.title')} subtitle={t('admin.dashboard.subtitle')}>
	{#snippet actions()}
		{#if d}
			<span class="text-xs text-ink-muted">
				{t('admin.updatedAt', { time: formatTime(d.generated_at, i18n.locale) })}
			</span>
		{/if}
	{/snippet}
</PageHeader>

<!-- Filters: one row above everything they scope -->
<div
	class="mb-6 inline-flex rounded-xl border border-line bg-white p-1 shadow-soft"
	role="group"
	aria-label={t('admin.range.label')}
>
	{#each ranges as range (range)}
		<a
			href={adminHref('/admin', { range: range === 'today' ? null : range })}
			class="rounded-lg px-3.5 py-1.5 text-sm font-semibold transition {data.range === range
				? 'bg-brand-600 text-white shadow-sm'
				: 'text-ink-muted hover:bg-brand-50 hover:text-brand-700'}"
			aria-current={data.range === range ? 'true' : undefined}
		>
			{t(`admin.range.${range}`)}
		</a>
	{/each}
</div>

{#if data.error || !d}
	<ErrorState message={data.error ?? ''} />
{:else}
	<section
		class="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-5"
		aria-label={t('admin.dashboard.title')}
	>
		<KpiCard
			label={t('admin.kpi.orders')}
			value={String(d.total_orders.value)}
			icon={ClipboardList}
			changePct={d.total_orders.change_pct}
			{comparison}
		/>
		<KpiCard
			label={t('admin.kpi.revenue')}
			value={usd(d.revenue.value)}
			icon={CircleDollarSign}
			tone="green"
			changePct={d.revenue.change_pct}
			{comparison}
		/>
		<KpiCard
			label={t('admin.kpi.pending')}
			value={String(d.pending_orders)}
			icon={Hourglass}
			tone="amber"
			hint={t('admin.kpi.pendingHint')}
		>
			{#if d.pending_orders > 0}
				<a
					href={adminHref('/admin/orders', { status: 'confirmed' })}
					class="mt-2 inline-flex items-center gap-1 text-xs font-bold text-brand-700 hover:underline"
				>
					{t('admin.orders.accept')}<ArrowRight class="size-3.5" />
				</a>
			{/if}
		</KpiCard>
		<KpiCard
			label={t('admin.kpi.completed')}
			value={String(d.completed_orders.value)}
			icon={PackageCheck}
			tone="sky"
			changePct={d.completed_orders.change_pct}
			{comparison}
		/>
		<KpiCard
			label={t('admin.kpi.aov')}
			value={usd(d.average_order_value.value)}
			icon={Receipt}
			tone="rose"
			changePct={d.average_order_value.change_pct}
			{comparison}
		/>
	</section>

	<div class="mt-4 flex flex-wrap gap-2">
		<a
			href={adminHref('/admin/orders', { status: 'preparing' })}
			class="chip gap-1.5 border border-line bg-white px-3 py-1.5 text-ink-soft hover:border-brand-200"
		>
			<ChefHat class="size-3.5 text-sky-600" />{t('admin.chip.inProgress', {
				count: d.in_progress_orders
			})}
		</a>
		<a
			href={adminHref('/admin/orders', { status: 'pending_payment' })}
			class="chip gap-1.5 border border-line bg-white px-3 py-1.5 text-ink-soft hover:border-brand-200"
		>
			<Wallet class="size-3.5 text-amber-600" />{t('admin.chip.awaitingPayment', {
				count: d.awaiting_payment
			})}
		</a>
		{#if d.low_stock_count > 0}
			<a
				href={adminHref('/admin/inventory', { low: 1 })}
				class="chip gap-1.5 border border-amber-200 bg-amber-50 px-3 py-1.5 text-amber-800 hover:bg-amber-100"
			>
				<TriangleAlert class="size-3.5" />{t('admin.chip.lowStock', { count: d.low_stock_count })}
			</a>
		{/if}
	</div>

	<div class="mt-6 grid gap-4 lg:grid-cols-3">
		<section class="card p-5 lg:col-span-2">
			<AreaChart
				title={t('admin.chart.salesOverTime')}
				subtitle={data.range === 'today'
					? t('admin.chart.salesHourly')
					: t('admin.chart.salesDaily')}
				points={salesPoints}
				formatValue={(v) => t('admin.chart.ordersCount', { count: v })}
				formatAxis={(v) => String(v)}
				emptyText={t('admin.chart.noData')}
			/>
		</section>
		<section class="card p-5">
			<HBarList
				title={t('admin.chart.ordersByStatus')}
				subtitle={t('admin.chart.ordersByStatusSub')}
				rows={statusRows}
			/>
		</section>

		<section class="card p-5 lg:col-span-2">
			<ColumnChart
				title={t('admin.chart.dailyRevenue')}
				subtitle={t('admin.chart.dailyRevenueSub', { days: d.daily_revenue.length })}
				points={dailyPoints}
				formatValue={(v) => usdCents(v)}
				formatAxis={axisMoney}
				minStep={100}
				emptyText={t('admin.chart.noData')}
			/>
		</section>
		<section class="card p-5">
			<h3 class="text-base font-bold text-ink">{t('admin.chart.popular')}</h3>
			<p class="text-xs text-ink-muted">{t('admin.chart.popularSub')}</p>
			{#if d.popular_items.length === 0}
				<p class="mt-8 text-center text-sm text-ink-muted">{t('admin.chart.noData')}</p>
			{:else}
				<ol class="mt-4 space-y-3.5">
					{#each d.popular_items as item, i (item.food_id ?? item.name_en)}
						<li class="flex items-center gap-3">
							<FoodImage src={item.image_url} alt="" class="size-11 shrink-0 rounded-xl" />
							<div class="min-w-0 flex-1">
								<div class="flex items-baseline justify-between gap-2">
									<p class="truncate text-sm font-semibold text-ink" lang={i18n.locale}>
										<span class="text-ink-muted">{i + 1}.</span>
										{i18n.pick(item, 'name')}
									</p>
									<p class="shrink-0 text-sm font-bold text-ink tabular-nums">
										{usd(item.revenue)}
									</p>
								</div>
								<div class="mt-1.5 flex items-center gap-2">
									<span class="h-1.5 flex-1 rounded-full bg-brand-50">
										<span
											class="block h-full rounded-full bg-brand-600"
											style="width: {(item.quantity / maxPopular) * 100}%"
										></span>
									</span>
									<span class="text-xs text-ink-muted tabular-nums">
										{t('admin.chart.sold', { count: item.quantity })}
									</span>
								</div>
							</div>
						</li>
					{/each}
				</ol>
			{/if}
		</section>
	</div>

	<section class="card mt-6 overflow-hidden">
		<div class="flex items-center justify-between gap-3 px-5 py-4">
			<h2 class="text-base font-bold text-ink">{t('admin.recent.title')}</h2>
			<a href={adminHref('/admin/orders')} class="btn btn-ghost btn-sm">
				{t('admin.recent.viewAll')}<ArrowRight class="size-4" />
			</a>
		</div>
		<div class="overflow-x-auto">
			<table class="w-full min-w-[820px] text-left text-sm">
				<thead class="border-y border-line bg-canvas text-xs font-semibold text-ink-muted">
					<tr>
						<th class="px-5 py-3">{t('admin.col.order')}</th>
						<th class="px-3 py-3">{t('admin.col.customer')}</th>
						<th class="px-3 py-3">{t('admin.col.items')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.total')}</th>
						<th class="px-3 py-3">{t('admin.col.payment')}</th>
						<th class="px-3 py-3">{t('admin.col.status')}</th>
						<th class="px-3 py-3">{t('admin.col.time')}</th>
						<th class="px-5 py-3 text-right">{t('admin.col.actions')}</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-line">
					{#each d.recent_orders as order (order.id)}
						<tr class="hover:bg-canvas/70">
							<td class="px-5 py-3 font-bold whitespace-nowrap text-ink">{order.order_number}</td>
							<td class="px-3 py-3 text-ink-soft">{order.customer_name}</td>
							<td
								class="max-w-[260px] truncate px-3 py-3 text-ink-muted"
								title={order.items_summary}
							>
								{order.items_summary}
							</td>
							<td class="px-3 py-3 text-right font-semibold tabular-nums">{usd(order.total)}</td>
							<td class="px-3 py-3">
								{#if order.payment_status}<StatusBadge
										status={order.payment_status}
										kind="payment"
									/>{/if}
							</td>
							<td class="px-3 py-3"><StatusBadge status={order.status} /></td>
							<td class="px-3 py-3 whitespace-nowrap text-ink-muted">
								{isToday(order.created_at)
									? formatTime(order.created_at, i18n.locale)
									: formatDateTime(order.created_at, i18n.locale)}
							</td>
							<td class="px-5 py-3 text-right">
								<a href={adminHref('/admin/orders', { open: order.id })} class="btn btn-soft btn-sm"
									>{t('admin.view')}</a
								>
							</td>
						</tr>
					{:else}
						<tr>
							<td colspan="8" class="px-5 py-10 text-center text-ink-muted"
								>{t('admin.orders.empty')}</td
							>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>
{/if}
