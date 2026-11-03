<script lang="ts">
	import { adminHref } from '#lib/components/admin/links.ts';
	import { goto } from '$app/navigation';
	import Users from '@lucide/svelte/icons/users';
	import PageHeader from '#lib/components/admin/PageHeader.svelte';
	import ErrorState from '#lib/components/admin/ErrorState.svelte';
	import SearchInput from '#lib/components/admin/SearchInput.svelte';
	import Pagination from '#lib/components/admin/Pagination.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { usd } from '#lib/components/admin/format.ts';
	import { formatDate, formatDateTime } from '#lib/utils/format.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const href = (changes: { q?: string; page?: number }) => {
		const q = changes.q ?? data.q;
		const p = changes.page ?? ('q' in changes ? 1 : data.page);
		return adminHref('/admin/customers', { q, page: p > 1 ? p : null });
	};
	const initials = (name: string) =>
		name
			.split(/\s+/)
			.map((p) => p[0])
			.slice(0, 2)
			.join('')
			.toUpperCase();
</script>

<svelte:head><title>{t('admin.customers.title')} · {t('admin.title')}</title></svelte:head>

<PageHeader title={t('admin.customers.title')} subtitle={t('admin.customers.subtitle')} />

<div class="card overflow-hidden">
	<div class="border-b border-line p-4">
		<SearchInput
			class="w-full sm:w-80"
			value={data.q}
			placeholder={t('admin.customers.search')}
			onsearch={(q) => goto(href({ q }), { replace: true, reset: false })}
		/>
	</div>
	{#if data.error || !data.customers}
		<div class="p-4"><ErrorState message={data.error ?? ''} /></div>
	{:else if data.customers.items.length === 0}
		<EmptyState
			icon={Users}
			title={t('admin.customers.empty')}
			text={t('admin.customers.emptyHint')}
		/>
	{:else}
		<div class="overflow-x-auto">
			<table class="w-full min-w-[900px] text-left text-sm">
				<thead class="bg-canvas text-xs font-semibold whitespace-nowrap text-ink-muted">
					<tr>
						<th class="px-4 py-3">{t('admin.col.customer')}</th>
						<th class="px-3 py-3">{t('admin.col.phone')}</th>
						<th class="px-3 py-3">{t('admin.col.email')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.orders')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.paidOrders')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.spent')}</th>
						<th class="px-4 py-3">{t('admin.col.lastOrder')}</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-line">
					{#each data.customers.items as c (c.customer_phone)}
						<tr class="hover:bg-canvas/60">
							<td class="px-4 py-3">
								<div class="flex items-center gap-3">
									<span
										class="grid size-9 shrink-0 place-items-center rounded-full bg-brand-50 text-xs font-bold text-brand-700"
										aria-hidden="true"
									>
										{initials(c.customer_name)}
									</span>
									<div>
										<p class="font-semibold whitespace-nowrap text-ink">{c.customer_name}</p>
										<span
											class="chip mt-0.5 {c.is_registered
												? 'bg-brand-50 text-brand-700'
												: 'bg-slate-100 text-slate-600'}"
										>
											{c.is_registered
												? t('admin.customers.registered')
												: t('admin.customers.guest')}
										</span>
									</div>
								</div>
							</td>
							<td class="px-3 py-3 whitespace-nowrap text-ink-soft tabular-nums">
								<a href="tel:{c.customer_phone}" class="hover:text-brand-700 hover:underline"
									>{c.customer_phone}</a
								>
							</td>
							<td class="px-3 py-3 text-ink-muted">{c.email ?? '—'}</td>
							<td class="px-3 py-3 text-right tabular-nums">{c.orders_count}</td>
							<td class="px-3 py-3 text-right tabular-nums">{c.paid_orders}</td>
							<td class="px-3 py-3 text-right font-semibold tabular-nums">{usd(c.total_spent)}</td>
							<td
								class="px-4 py-3 whitespace-nowrap text-ink-muted"
								title={formatDateTime(c.last_order_at, i18n.locale)}
							>
								{formatDate(c.last_order_at, i18n.locale)}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<Pagination
			page={data.page}
			pageSize={data.customers.page_size}
			total={data.customers.total}
			href={(p) => href({ page: p })}
		/>
	{/if}
</div>
