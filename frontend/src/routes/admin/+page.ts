import { attempt } from '#lib/components/admin/errors.ts';
import { getDashboard, type DashboardRange } from '#lib/services/admin.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url, depends }) => {
	depends('admin:dashboard');
	const raw = url.searchParams.get('range');
	const range: DashboardRange = raw === '7d' || raw === '30d' ? raw : 'today';
	const result = await attempt(() => getDashboard(range, fetch));
	return {
		range,
		dashboard: result.ok ? result.value : null,
		error: result.ok ? null : result.error
	};
};
