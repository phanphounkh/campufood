import { browser } from '$app/env';
import type { Food } from '#lib/types/api.ts';
import { centsToString, toCents } from '#lib/utils/money.ts';

export interface CartLine {
	foodId: number;
	name_en: string;
	name_km: string;
	/** Unit price as an exact decimal string ("1.50"), as last seen from the API. */
	price: string;
	image_url: string | null;
	quantity: number;
	/** Upper bound for this line: min(stock, per-order limit). */
	maxQuantity: number;
}

export type AddResult = 'added' | 'max' | 'unavailable';

export const STORAGE_KEY = 'campuseats.cart.v1';
export const MAX_PER_ITEM = 20;

function isLine(value: unknown): value is CartLine {
	const v = value as CartLine;
	return (
		!!v &&
		Number.isInteger(v.foodId) &&
		typeof v.name_en === 'string' &&
		typeof v.price === 'string' &&
		/^\d+(\.\d{1,2})?$/.test(v.price) &&
		Number.isInteger(v.quantity) &&
		v.quantity > 0
	);
}

function maxFor(food: Food): number {
	return Math.min(MAX_PER_ITEM, Math.max(0, food.stock_quantity));
}

/**
 * Shopping cart. Totals are integer cents (display only — the server recomputes prices).
 * Persisted to localStorage so a refresh keeps the cart, and synced across tabs.
 */
export class CartStore {
	lines = $state<CartLine[]>([]);
	/** Increments on every add; UI uses it to animate the cart badge. */
	pulse = $state(0);
	drawerOpen = $state(false);
	#storage: Storage | null;
	#loaded = false;

	constructor(storage: Storage | null = browser ? localStorage : null) {
		this.#storage = storage;
	}

	get count(): number {
		return this.lines.reduce((sum, line) => sum + line.quantity, 0);
	}

	get subtotalCents(): number {
		return this.lines.reduce((sum, line) => sum + toCents(line.price) * line.quantity, 0);
	}

	get totalCents(): number {
		return this.subtotalCents;
	}

	/** Exact decimal string of the total, sent to the API as `expected_total`. */
	get totalString(): string {
		return centsToString(this.totalCents);
	}

	quantityOf(foodId: number): number {
		return this.lines.find((l) => l.foodId === foodId)?.quantity ?? 0;
	}

	load(): void {
		if (this.#loaded || !this.#storage) return;
		this.#loaded = true;
		this.#readStorage();
		if (browser) {
			window.addEventListener('storage', (event) => {
				if (event.key === STORAGE_KEY) this.#readStorage();
			});
		}
	}

	#readStorage(): void {
		try {
			const raw = this.#storage?.getItem(STORAGE_KEY);
			const parsed: unknown = raw ? JSON.parse(raw) : [];
			this.lines = Array.isArray(parsed) ? parsed.filter(isLine) : [];
		} catch {
			this.lines = [];
		}
	}

	#save(): void {
		try {
			this.#storage?.setItem(STORAGE_KEY, JSON.stringify(this.lines));
		} catch {
			/* storage full or disabled: the cart still works for this page view */
		}
	}

	add(food: Food, quantity = 1): AddResult {
		if (food.is_sold_out || !food.is_available || food.is_archived) return 'unavailable';
		const max = maxFor(food);
		const line = this.lines.find((l) => l.foodId === food.id);
		const current = line?.quantity ?? 0;
		if (current >= max) return 'max';
		const next = Math.min(max, current + quantity);
		if (line) {
			Object.assign(line, {
				quantity: next,
				price: food.price,
				maxQuantity: max,
				name_en: food.name_en,
				name_km: food.name_km,
				image_url: food.image_url
			});
		} else {
			this.lines.push({
				foodId: food.id,
				name_en: food.name_en,
				name_km: food.name_km,
				price: food.price,
				image_url: food.image_url,
				quantity: next,
				maxQuantity: max
			});
		}
		this.pulse++;
		this.#save();
		return 'added';
	}

	setQuantity(foodId: number, quantity: number): void {
		const line = this.lines.find((l) => l.foodId === foodId);
		if (!line) return;
		if (quantity <= 0) return this.remove(foodId);
		line.quantity = Math.min(quantity, line.maxQuantity || MAX_PER_ITEM, MAX_PER_ITEM);
		this.#save();
	}

	increment(foodId: number): void {
		const line = this.lines.find((l) => l.foodId === foodId);
		if (line) this.setQuantity(foodId, line.quantity + 1);
	}

	decrement(foodId: number): void {
		const line = this.lines.find((l) => l.foodId === foodId);
		if (line) this.setQuantity(foodId, line.quantity - 1);
	}

	remove(foodId: number): void {
		this.lines = this.lines.filter((l) => l.foodId !== foodId);
		this.#save();
	}

	clear(): void {
		this.lines = [];
		this.#save();
	}

	/**
	 * Reconcile the cart with fresh menu data: update prices and names, clamp quantities to
	 * stock and drop items that are gone. Returns true if anything the customer pays changed.
	 */
	sync(foods: Food[]): boolean {
		const byId: Record<number, Food> = Object.fromEntries(foods.map((f) => [f.id, f]));
		let changed = false;
		const next: CartLine[] = [];
		for (const line of this.lines) {
			const food = byId[line.foodId];
			if (!food || food.is_sold_out || food.is_archived || !food.is_available) {
				changed = true;
				continue;
			}
			const max = maxFor(food);
			const quantity = Math.min(line.quantity, max);
			if (food.price !== line.price || quantity !== line.quantity) changed = true;
			next.push({
				...line,
				price: food.price,
				name_en: food.name_en,
				name_km: food.name_km,
				image_url: food.image_url,
				quantity,
				maxQuantity: max
			});
		}
		this.lines = next;
		this.#save();
		return changed;
	}
}

export const cart = new CartStore();
