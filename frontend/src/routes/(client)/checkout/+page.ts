import { listFoods } from '#lib/services/catalog.ts';
import type { PageLoad } from './$types';

// The cart lives in localStorage, so render this page in the browser only.
export const ssr = false;

export const load: PageLoad = async ({ fetch }) => {
	const foods = await listFoods({ page_size: 100 }, fetch);
	return { foods: foods.items };
};
