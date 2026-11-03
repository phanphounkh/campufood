<script lang="ts">
	import { adminHref } from '#lib/components/admin/links.ts';
	import { goto } from '$app/navigation';
	import CreditCard from '@lucide/svelte/icons/credit-card';
	import Banknote from '@lucide/svelte/icons/banknote';
	import Undo2 from '@lucide/svelte/icons/undo-2';
	import Wallet from '@lucide/svelte/icons/wallet';
	import Hourglass from '@lucide/svelte/icons/hourglass';
	import Info from '@lucide/svelte/icons/info';
	import PageHeader from '#lib/components/admin/PageHeader.svelte';
	import KpiCard from '#lib/components/admin/KpiCard.svelte';
	import ErrorState from '#lib/components/admin/ErrorState.svelte';
	import SearchInput from '#lib/components/admin/SearchInput.svelte';
	import Pagination from '#lib/components/admin/Pagination.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import StatusBadge from '#lib/components/ui/StatusBadge.svelte';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { toCents } from '#lib/utils/money.ts';
	import { usd, usdCents } from '#lib/components/admin/format.ts';
	import { formatDateTime } from '#lib/utils/format.ts';
	import type { PaymentStatus } from '#lib/types/api.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	function href(changes: { status?: PaymentStatus | null; q?: string; page?: number }) {
		const status = 'status' in changes ? changes.status : data.status;
		const q = changes.q ?? data.q;
		const p = changes.page ?? ('status' in changes || 'q' in changes ? 1 : data.page);
		return adminHref('/admin/payments', { status, q, page: p > 1 ? p : null });
	}

	const net = $derived(
		data.summary ? usdCents(toCents(data.summary.collected) - toCents(data.summary.refunded)) : '—'
	);
</script>

<svelte:head><title>{t('admin.payments.title')} · {t('admin.title')}</title></svelte:head>

<PageHeader title={t('admin.payments.title')} subtitle={t('admin.payments.subtitle')} />

<p
	class="mb-5 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-900"
>
	<Info class="mt-0.5 size-4 shrink-0" />{t('admin.payments.demoNotice')}
</p>

{#if data.summary}
	<div class="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
		<KpiCard
			label={t('admin.payments.collected')}
			value={usd(data.summary.collected)}
			icon={Banknote}
			tone="green"
			hint={t('admin.payments.collectedHint')}
		/>
		<KpiCard
			label={t('admin.payments.refunded')}
			value={usd(data.summary.refunded)}
			icon={Undo2}
			tone="rose"
			hint={t('admin.payments.refundedHint')}
		/>
		<KpiCard
			label={t('admin.payments.net')}
			value={net}
			icon={Wallet}
			hint={t('admin.payments.netHint')}
		/>
		<KpiCard
			label={t('admin.payments.pending')}
			value={usd(data.summary.pending)}
			icon={Hourglass}
			tone="amber"
			hint={t('admin.payments.pendingHint')}
		/>
	</div>
{/if}

<div class="card overflow-hidden">
	<div class="flex flex-col gap-3 border-b border-line p-4 sm:flex-row sm:items-center">
		<select
			class="w-full rounded-xl py-2 text-sm sm:w-52"
			aria-label={t('admin.payments.statusFilter')}
			value={data.status ?? ''}
			onchange={(e) =>
				goto(href({ status: (e.currentTarget.value || null) as PaymentStatus | null }), {
					reset: false
				})}
		>
			<option value="">{t('admin.payments.allStatuses')}</option>
			{#each data.statuses as s (s)}
				<option value={s}
					>{t(`payment.${s}`)}{data.summary
						? ` (${data.summary.count_by_status[s] ?? 0})`
						: ''}</option
				>
			{/each}
		</select>
		<SearchInput
			class="w-full sm:w-80"
			value={data.q}
			placeholder={t('admin.payments.search')}
			onsearch={(q) => goto(href({ q }), { replace: true, reset: false })}
		/>
	</div>
	{#if data.error || !data.payments}
		<div class="p-4"><ErrorState message={data.error ?? ''} /></div>
	{:else if data.payments.items.length === 0}
		<EmptyState icon={CreditCard} title={t('admin.payments.empty')} />
	{:else}
		<div class="overflow-x-auto">
			<table class="w-full min-w-[960px] text-left text-sm">
				<thead class="bg-canvas text-xs font-semibold whitespace-nowrap text-ink-muted">
					<tr>
						<th class="px-4 py-3">{t('admin.col.reference')}</th>
						<th class="px-3 py-3">{t('admin.col.order')}</th>
						<th class="px-3 py-3">{t('admin.col.customer')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.amount')}</th>
						<th class="px-3 py-3">{t('admin.col.status')}</th>
						<th class="px-3 py-3">{t('admin.col.provider')}</th>
						<th class="px-3 py-3">{t('admin.col.paidAt')}</th>
						<th class="px-4 py-3">{t('admin.col.created')}</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-line">
					{#each data.payments.items as p (p.id)}
						<tr class="hover:bg-canvas/60">
							<td class="px-4 py-3">
								<p class="font-mono text-xs font-semibold text-ink">
									{p.transaction_reference ?? '—'}
								</p>
								<p class="font-mono text-[11px] text-ink-muted" title={p.id}>{p.id.slice(0, 8)}</p>
							</td>
							<td class="px-3 py-3">
								<a
									href={adminHref('/admin/orders', { open: p.order_id })}
									class="font-semibold whitespace-nowrap text-brand-700 hover:underline"
									>{p.order_number}</a
								>
							</td>
							<td class="px-3 py-3 whitespace-nowrap text-ink-soft">{p.customer_name}</td>
							<td class="px-3 py-3 text-right font-semibold tabular-nums">{usd(p.amount)}</td>
							<td class="px-3 py-3"><StatusBadge status={p.status} kind="payment" /></td>
							<td class="px-3 py-3"
								><span class="chip bg-brand-50 text-brand-700"
									>{t('admin.payments.providerDemo')}</span
								></td
							>
							<td class="px-3 py-3 whitespace-nowrap text-ink-muted"
								>{p.paid_at ? formatDateTime(p.paid_at, i18n.locale) : '—'}</td
							>
							<td class="px-4 py-3 whitespace-nowrap text-ink-muted"
								>{formatDateTime(p.created_at, i18n.locale)}</td
							>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<Pagination
			page={data.page}
			pageSize={data.payments.page_size}
			total={data.payments.total}
			href={(p) => href({ page: p })}
		/>
	{/if}
</div>
