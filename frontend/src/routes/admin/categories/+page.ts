import { attempt } from '#lib/components/admin/errors.ts';
import { listCategories } from '#lib/services/catalog.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, depends }) => {
	depends('admin:categories');
	const result = await attempt(() => listCategories(fetch));
	return {
		categories: result.ok ? result.value : null,
		error: result.ok ? null : result.error
	};
};
