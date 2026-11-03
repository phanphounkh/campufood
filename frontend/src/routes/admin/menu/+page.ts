import { attempt } from '#lib/components/admin/errors.ts';
import { listCategories, listFoods } from '#lib/services/catalog.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url, depends }) => {
	depends('admin:menu');
	const archived = url.searchParams.get('archived') === '1';
	const [foods, categories] = await Promise.all([
		attempt(() => listFoods({ include_archived: archived, page_size: 100, sort: 'name' }, fetch)),
		attempt(() => listCategories(fetch))
	]);
	return {
		archived,
		foods: foods.ok ? foods.value.items : null,
		categories: categories.ok ? categories.value : [],
		error: foods.ok ? null : foods.error
	};
};
