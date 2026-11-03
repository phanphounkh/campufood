import { describe, expect, it } from 'vitest';
import { filterFoods } from '#lib/utils/menu.ts';
import { chickenRice, makeFood, milkTea } from './fixtures.ts';

const foods = [
	chickenRice(),
	milkTea(),
	makeFood({
		id: 103,
		name_en: 'Fried Rice',
		name_km: 'បាយឆា',
		price: '1.75',
		description_en: 'Wok fried'
	}),
	makeFood({ id: 104, name_en: 'Pork Rice', price: '1.75', is_sold_out: true, stock_quantity: 0 })
];

describe('menu filtering', () => {
	it('filters by category', () => {
		const drinks = filterFoods(foods, { category: 'drinks', search: '', sort: 'featured' });
		expect(drinks.map((f) => f.name_en)).toEqual(['Iced Milk Tea']);
		expect(filterFoods(foods, { category: 'all', search: '', sort: 'featured' })).toHaveLength(4);
	});

	it('searches English and Khmer names and descriptions', () => {
		expect(
			filterFoods(foods, { category: 'all', search: 'FRIED', sort: 'name' }).map((f) => f.id)
		).toEqual([103]);
		expect(
			filterFoods(foods, { category: 'all', search: 'បាយមាន់', sort: 'name' }).map((f) => f.id)
		).toEqual([101]);
		expect(
			filterFoods(foods, { category: 'all', search: 'wok', sort: 'name' }).map((f) => f.id)
		).toEqual([103]);
		expect(filterFoods(foods, { category: 'drinks', search: 'rice', sort: 'name' })).toEqual([]);
	});

	it('sorts by price and puts featured first, sold out last', () => {
		const asc = filterFoods(foods, { category: 'all', search: '', sort: 'price_asc' }).map(
			(f) => f.price
		);
		expect(asc).toEqual(['0.75', '1.50', '1.75', '1.75']);
		const desc = filterFoods(foods, { category: 'all', search: '', sort: 'price_desc' }).map(
			(f) => f.price
		);
		expect(desc[0]).toBe('1.75');
		const featured = filterFoods(foods, { category: 'all', search: '', sort: 'featured' });
		expect(featured[0].name_en).toBe('Chicken Rice');
		expect(featured.at(-1)?.name_en).toBe('Pork Rice');
	});
});
