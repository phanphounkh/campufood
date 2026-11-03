import { listCategories, listFoods } from '#lib/services/catalog.ts';
import { toCents } from '#lib/utils/money.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch }) => {
	const [featured, all, categories] = await Promise.all([
		listFoods({ featured: true, page_size: 8 }, fetch),
		listFoods({ page_size: 100 }, fetch),
		listCategories(fetch)
	]);
	const prices = all.items.filter((f) => !f.is_sold_out).map((f) => f.price);
	return {
		featured: featured.items,
		mealCount: all.total,
		cheapest: prices.sort((a, b) => toCents(a) - toCents(b))[0] ?? null,
		categories
	};
};
