<script lang="ts">
	import { adminHref } from '#lib/components/admin/links.ts';
	import { goto } from '$app/navigation';
	import Download from '@lucide/svelte/icons/download';
	import Banknote from '@lucide/svelte/icons/banknote';
	import Undo2 from '@lucide/svelte/icons/undo-2';
	import Wallet from '@lucide/svelte/icons/wallet';
	import ClipboardList from '@lucide/svelte/icons/clipboard-list';
	import Utensils from '@lucide/svelte/icons/utensils';
	import Ban from '@lucide/svelte/icons/ban';
	import Receipt from '@lucide/svelte/icons/receipt';
	import Info from '@lucide/svelte/icons/info';
	import PageHeader from '#lib/components/admin/PageHeader.svelte';
	import KpiCard from '#lib/components/admin/KpiCard.svelte';
	import ErrorState from '#lib/components/admin/ErrorState.svelte';
	import ColumnChart from '#lib/components/admin/charts/ColumnChart.svelte';
	import { axisMoney, type ChartPoint } from '#lib/components/admin/charts/scale.ts';
	import { dayLabels } from '#lib/components/admin/chartData.ts';
	import FoodImage from '#lib/components/ui/FoodImage.svelte';
	import { reportCsvUrl, type Granularity } from '#lib/services/admin.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { toCents } from '#lib/utils/money.ts';
	import { usd, usdCents } from '#lib/components/admin/format.ts';
	import { shiftDays, todayISO } from '#lib/utils/format.ts';
	import type { ReportPeriod } from '#lib/types/api.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	// svelte-ignore state_referenced_locally
	let from = $state(data.from);
	// svelte-ignore state_referenced_locally
	let to = $state(data.to);
	$effect(() => {
		from = data.from;
		to = data.to;
	});

	function apply(f: string, tt: string, g: Granularity = data.granularity) {
		goto(adminHref('/admin/reports', { from: f, to: tt, g: g === 'day' ? null : g }), {
			reset: false
		});
	}

	function preset(kind: '7' | '30' | '90' | 'month') {
		const today = todayISO();
		if (kind === 'month') apply(`${today.slice(0, 8)}01`, today);
		else apply(shiftDays(today, -(Number(kind) - 1)), today);
	}

	const granularities: Granularity[] = ['day', 'week', 'month'];
	const intl = $derived(i18n.locale === 'km' ? 'km-KH' : 'en-US');

	function periodLabels(p: ReportPeriod): { short: string; full: string } {
		if (data.granularity === 'day') return dayLabels(p.start, i18n.locale);
		if (data.granularity === 'week') {
			const start = dayLabels(p.start, i18n.locale);
			return { short: start.short, full: `${p.period} · ${start.full}` };
		}
		const date = new Date(`${p.start}T00:00:00Z`);
		return {
			short: new Intl.DateTimeFormat(intl, { month: 'short', timeZone: 'UTC' }).format(date),
			full: new Intl.DateTimeFormat(intl, {
				month: 'long',
				year: 'numeric',
				timeZone: 'UTC'
			}).format(date)
		};
	}

	const points = $derived<ChartPoint[]>(
		data.report
			? data.report.periods.map((p) => {
					const labels = periodLabels(p);
					return {
						label: labels.short,
						fullLabel: labels.full,
						value: Math.max(0, toCents(p.net_revenue)),
						detail: t('admin.chart.ordersCount', { count: p.orders })
					};
				})
			: []
	);
	const csvHref = $derived(
		reportCsvUrl({ date_from: data.from, date_to: data.to, granularity: data.granularity })
	);
</script>

<svelte:head><title>{t('admin.reports.title')} · {t('admin.title')}</title></svelte:head>

<PageHeader title={t('admin.reports.title')} subtitle={t('admin.reports.subtitle')}>
	{#snippet actions()}
		{#if data.report}
			<a href={csvHref} download rel="external" class="btn btn-secondary"
				><Download class="size-4" />{t('admin.reports.export')}</a
			>
		{/if}
	{/snippet}
</PageHeader>

<!-- Filters: one row above everything they scope -->
<form
	class="card mb-6 flex flex-wrap items-end gap-3 p-4"
	onsubmit={(e) => {
		e.preventDefault();
		apply(from, to);
	}}
>
	<div>
		<label class="label text-xs" for="r-from">{t('admin.reports.from')}</label>
		<input id="r-from" type="date" class="py-2 text-sm" bind:value={from} max={to} />
	</div>
	<div>
		<label class="label text-xs" for="r-to">{t('admin.reports.to')}</label>
		<input id="r-to" type="date" class="py-2 text-sm" bind:value={to} min={from} max={todayISO()} />
	</div>
	<button type="submit" class="btn btn-primary">{t('admin.reports.apply')}</button>
	<div class="flex flex-wrap gap-1.5">
		<button type="button" class="btn btn-soft btn-sm" onclick={() => preset('7')}
			>{t('admin.reports.preset7')}</button
		>
		<button type="button" class="btn btn-soft btn-sm" onclick={() => preset('30')}
			>{t('admin.reports.preset30')}</button
		>
		<button type="button" class="btn btn-soft btn-sm" onclick={() => preset('90')}
			>{t('admin.reports.preset90')}</button
		>
		<button type="button" class="btn btn-soft btn-sm" onclick={() => preset('month')}
			>{t('admin.reports.presetMonth')}</button
		>
	</div>
	<div class="ml-auto" role="group" aria-label={t('admin.reports.granularity')}>
		<span class="label text-xs">{t('admin.reports.granularity')}</span>
		<div class="inline-flex rounded-xl border border-line bg-white p-1">
			{#each granularities as g (g)}
				<button
					type="button"
					aria-pressed={data.granularity === g}
					class="rounded-lg px-3 py-1 text-sm font-semibold transition {data.granularity === g
						? 'bg-brand-600 text-white'
						: 'text-ink-muted hover:text-brand-700'}"
					onclick={() => apply(data.from, data.to, g)}
				>
					{t(`admin.reports.${g}`)}
				</button>
			{/each}
		</div>
	</div>
</form>

{#if data.invalidRange}
	<p class="rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700" role="alert">
		{t('admin.reports.invalidRange')}
	</p>
{:else if data.error || !data.report}
	<ErrorState message={data.error ?? ''} />
{:else}
	{@const totals = data.report.totals}
	<div class="grid gap-4 md:grid-cols-3">
		<KpiCard
			label={t('admin.reports.gross')}
			value={usd(totals.gross_sales)}
			icon={Banknote}
			tone="green"
			hint={t('admin.reports.grossHint')}
		/>
		<KpiCard
			label={t('admin.reports.refunds')}
			value={usdCents(-toCents(totals.refunds))}
			icon={Undo2}
			tone="rose"
			hint={t('admin.reports.refundsHint', { count: totals.refunded_orders })}
		/>
		<div class="rounded-[var(--radius-card)] ring-2 ring-brand-200">
			<KpiCard
				label={t('admin.reports.net')}
				value={usd(totals.net_revenue)}
				icon={Wallet}
				hint={t('admin.reports.netHint')}
			/>
		</div>
	</div>
	<div class="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
		<KpiCard
			label={t('admin.reports.orders')}
			value={String(totals.orders)}
			icon={ClipboardList}
			tone="sky"
		/>
		<KpiCard
			label={t('admin.reports.itemsSold')}
			value={String(totals.items_sold)}
			icon={Utensils}
			tone="brand"
		/>
		<KpiCard
			label={t('admin.reports.cancelled')}
			value={String(totals.cancelled_orders)}
			icon={Ban}
			tone="rose"
		/>
		<KpiCard
			label={t('admin.reports.aov')}
			value={usd(totals.average_order_value)}
			icon={Receipt}
			tone="amber"
		/>
	</div>
	<p class="mt-3 flex items-start gap-2 text-xs text-ink-muted">
		<Info class="mt-px size-3.5 shrink-0" />{t('admin.reports.revenueNote')}
	</p>

	<section class="card mt-6 p-5">
		<ColumnChart
			title={t('admin.reports.chartTitle')}
			subtitle={`${data.from} → ${data.to}`}
			{points}
			formatValue={(v) => usdCents(v)}
			formatAxis={axisMoney}
			minStep={100}
			emptyText={t('admin.reports.noSales')}
			height={260}
		/>
	</section>

	<div class="mt-6 grid gap-6 xl:grid-cols-5">
		<section class="card overflow-hidden xl:col-span-3">
			<h2 class="px-5 py-4 text-base font-bold text-ink">{t('admin.reports.breakdown')}</h2>
			<div class="max-h-[520px] overflow-auto">
				<table class="w-full min-w-[640px] text-left text-sm">
					<thead
						class="sticky top-0 border-y border-line bg-canvas text-xs font-semibold whitespace-nowrap text-ink-muted"
					>
						<tr>
							<th class="px-5 py-3">{t('admin.col.period')}</th>
							<th class="px-3 py-3 text-right">{t('admin.col.orders')}</th>
							<th class="px-3 py-3 text-right">{t('admin.col.itemsSold')}</th>
							<th class="px-3 py-3 text-right">{t('admin.col.gross')}</th>
							<th class="px-3 py-3 text-right">{t('admin.col.refunds')}</th>
							<th class="px-3 py-3 text-right">{t('admin.col.net')}</th>
							<th class="px-5 py-3 text-right">{t('admin.col.cancelled')}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-line tabular-nums">
						{#each data.report.periods as p (p.period)}
							<tr class="hover:bg-canvas/60">
								<td class="px-5 py-2.5 whitespace-nowrap text-ink-soft">{periodLabels(p).full}</td>
								<td class="px-3 py-2.5 text-right">{p.orders}</td>
								<td class="px-3 py-2.5 text-right">{p.items_sold}</td>
								<td class="px-3 py-2.5 text-right">{usd(p.gross_sales)}</td>
								<td
									class="px-3 py-2.5 text-right {toCents(p.refunds) > 0
										? 'text-red-700'
										: 'text-ink-muted'}"
								>
									{toCents(p.refunds) > 0 ? usdCents(-toCents(p.refunds)) : '—'}
								</td>
								<td class="px-3 py-2.5 text-right font-semibold">{usd(p.net_revenue)}</td>
								<td class="px-5 py-2.5 text-right text-ink-muted">{p.cancelled_orders}</td>
							</tr>
						{/each}
					</tbody>
					<tfoot class="sticky bottom-0 border-t-2 border-line bg-white font-bold tabular-nums">
						<tr>
							<td class="px-5 py-3">{t('admin.reports.total')}</td>
							<td class="px-3 py-3 text-right">{totals.orders}</td>
							<td class="px-3 py-3 text-right">{totals.items_sold}</td>
							<td class="px-3 py-3 text-right">{usd(totals.gross_sales)}</td>
							<td class="px-3 py-3 text-right text-red-700">{usdCents(-toCents(totals.refunds))}</td
							>
							<td class="px-3 py-3 text-right text-brand-700">{usd(totals.net_revenue)}</td>
							<td class="px-5 py-3 text-right">{totals.cancelled_orders}</td>
						</tr>
					</tfoot>
				</table>
			</div>
		</section>

		<section class="card overflow-hidden xl:col-span-2">
			<h2 class="px-5 py-4 text-base font-bold text-ink">{t('admin.reports.bestSellers')}</h2>
			{#if data.report.best_sellers.length === 0}
				<p class="border-t border-line px-5 py-10 text-center text-sm text-ink-muted">
					{t('admin.reports.noSales')}
				</p>
			{:else}
				<table class="w-full text-left text-sm">
					<thead class="border-y border-line bg-canvas text-xs font-semibold text-ink-muted">
						<tr>
							<th class="px-5 py-3">{t('admin.col.rank')}</th>
							<th class="px-3 py-3">{t('admin.col.food')}</th>
							<th class="px-3 py-3 text-right">{t('admin.col.qty')}</th>
							<th class="px-5 py-3 text-right">{t('admin.col.revenue')}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-line">
						{#each data.report.best_sellers as item, i (item.food_id ?? item.name_en)}
							<tr>
								<td class="px-5 py-2.5 font-bold text-ink-muted tabular-nums">{i + 1}</td>
								<td class="px-3 py-2.5">
									<div class="flex items-center gap-2.5">
										<FoodImage src={item.image_url} alt="" class="size-8 shrink-0 rounded-lg" />
										<span class="font-semibold text-ink" lang={i18n.locale}
											>{i18n.pick(item, 'name')}</span
										>
									</div>
								</td>
								<td class="px-3 py-2.5 text-right tabular-nums">{item.quantity}</td>
								<td class="px-5 py-2.5 text-right font-semibold tabular-nums"
									>{usd(item.revenue)}</td
								>
							</tr>
						{/each}
					</tbody>
				</table>
			{/if}
		</section>
	</div>
{/if}
