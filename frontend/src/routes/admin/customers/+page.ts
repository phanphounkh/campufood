import { attempt } from '#lib/components/admin/errors.ts';
import { getCustomers } from '#lib/services/admin.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
	const q = url.searchParams.get('q')?.trim() ?? '';
	const pageNumber = Math.max(1, Number(url.searchParams.get('page')) || 1);
	const result = await attempt(() =>
		getCustomers({ search: q || undefined, page: pageNumber }, fetch)
	);
	return {
		q,
		page: pageNumber,
		customers: result.ok ? result.value : null,
		error: result.ok ? null : result.error
	};
};
