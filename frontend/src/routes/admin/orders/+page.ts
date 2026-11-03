import { attempt } from '#lib/components/admin/errors.ts';
import { ORDER_STATUSES } from '#lib/components/admin/orderFlow.ts';
import { listAdminOrders, ordersSummary } from '#lib/services/orders.ts';
import type { OrderStatus } from '#lib/types/api.ts';
import type { PageLoad } from './$types';

const PAGE_SIZE = 15;

export const load: PageLoad = async ({ fetch, url, depends }) => {
	depends('admin:orders');
	const rawStatus = url.searchParams.get('status');
	const status = ORDER_STATUSES.includes(rawStatus as OrderStatus)
		? (rawStatus as OrderStatus)
		: null;
	const q = url.searchParams.get('q')?.trim() ?? '';
	const pageNumber = Math.max(1, Number(url.searchParams.get('page')) || 1);

	const [orders, summary] = await Promise.all([
		attempt(() =>
			listAdminOrders(
				{
					status: status ? [status] : undefined,
					search: q || undefined,
					page: pageNumber,
					page_size: PAGE_SIZE
				},
				fetch
			)
		),
		attempt(() => ordersSummary(fetch))
	]);

	return {
		status,
		q,
		page: pageNumber,
		pageSize: PAGE_SIZE,
		orders: orders.ok ? orders.value : null,
		summary: summary.ok ? summary.value : null,
		error: orders.ok ? null : orders.error
	};
};
