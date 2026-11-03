import { listCategories, listFoods } from '#lib/services/catalog.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const [foods, categories] = await Promise.all([
		listFoods({ page_size: 100 }, fetch),
		listCategories(fetch)
	]);
	return { foods: foods.items, categories };
};
