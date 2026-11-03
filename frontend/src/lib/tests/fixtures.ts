import type { Food } from '#lib/types/api.ts';

let nextId = 1;

export function makeFood(overrides: Partial<Food> = {}): Food {
	const id = overrides.id ?? nextId++;
	return {
		id,
		category_id: 1,
		category: { id: 1, slug: 'rice', name_en: 'Rice', name_km: 'បាយ' },
		name_en: `Food ${id}`,
		name_km: `ម្ហូប ${id}`,
		description_en: '',
		description_km: '',
		price: '1.50',
		image_url: null,
		stock_quantity: 50,
		is_available: true,
		is_featured: false,
		is_archived: false,
		is_sold_out: false,
		created_at: '2026-11-01T00:00:00Z',
		updated_at: '2026-11-01T00:00:00Z',
		...overrides
	};
}

export const chickenRice = () =>
	makeFood({
		id: 101,
		name_en: 'Chicken Rice',
		name_km: 'បាយមាន់',
		price: '1.50',
		is_featured: true
	});
export const milkTea = () =>
	makeFood({
		id: 102,
		name_en: 'Iced Milk Tea',
		name_km: 'តែទឹកដោះគោទឹកកក',
		price: '0.75',
		category_id: 2,
		category: { id: 2, slug: 'drinks', name_en: 'Drinks', name_km: 'ភេសជ្ជៈ' }
	});

export class MemoryStorage implements Storage {
	#data = new Map<string, string>();
	get length() {
		return this.#data.size;
	}
	clear() {
		this.#data.clear();
	}
	getItem(key: string) {
		return this.#data.get(key) ?? null;
	}
	key(index: number) {
		return [...this.#data.keys()][index] ?? null;
	}
	removeItem(key: string) {
		this.#data.delete(key);
	}
	setItem(key: string, value: string) {
		this.#data.set(key, value);
	}
}
