import type { Food } from '#lib/types/api.ts';
import { toCents } from './money.ts';

export type MenuSort = 'featured' | 'price_asc' | 'price_desc' | 'name';

export interface MenuFilter {
	category: string;
	search: string;
	sort: MenuSort;
}

function normalize(text: string): string {
	return text.toLocaleLowerCase().normalize('NFC').trim();
}

/** Client-side menu filtering (the whole menu is small enough to filter instantly). */
export function filterFoods(foods: Food[], { category, search, sort }: MenuFilter): Food[] {
	const term = normalize(search);
	const filtered = foods.filter((food) => {
		if (category !== 'all' && food.category.slug !== category) return false;
		if (!term) return true;
		return [food.name_en, food.name_km, food.description_en, food.description_km].some((text) =>
			normalize(text).includes(term)
		);
	});

	const byName = (a: Food, b: Food) => a.name_en.localeCompare(b.name_en);
	const sorters: Record<MenuSort, (a: Food, b: Food) => number> = {
		featured: (a, b) =>
			Number(a.is_sold_out) - Number(b.is_sold_out) ||
			Number(b.is_featured) - Number(a.is_featured) ||
			byName(a, b),
		price_asc: (a, b) => toCents(a.price) - toCents(b.price) || byName(a, b),
		price_desc: (a, b) => toCents(b.price) - toCents(a.price) || byName(a, b),
		name: byName
	};
	return [...filtered].sort(sorters[sort]);
}
