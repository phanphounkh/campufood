import { attempt } from '#lib/components/admin/errors.ts';
import { getPayments, getPaymentSummary } from '#lib/services/admin.ts';
import type { PaymentStatus } from '#lib/types/api.ts';
import type { PageLoad } from './$types';

const STATUSES: PaymentStatus[] = ['pending', 'paid', 'failed', 'expired', 'cancelled', 'refunded'];

export const load: PageLoad = async ({ fetch, url }) => {
	const raw = url.searchParams.get('status');
	const status = STATUSES.includes(raw as PaymentStatus) ? (raw as PaymentStatus) : null;
	const q = url.searchParams.get('q')?.trim() ?? '';
	const pageNumber = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const [payments, summary] = await Promise.all([
		attempt(() =>
			getPayments({ status: status ?? undefined, search: q || undefined, page: pageNumber }, fetch)
		),
		attempt(() => getPaymentSummary(fetch))
	]);
	return {
		statuses: STATUSES,
		status,
		q,
		page: pageNumber,
		payments: payments.ok ? payments.value : null,
		summary: summary.ok ? summary.value : null,
		error: payments.ok ? null : payments.error
	};
};
