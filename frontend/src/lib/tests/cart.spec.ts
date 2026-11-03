import { beforeEach, describe, expect, it } from 'vitest';
import { CartStore, MAX_PER_ITEM, STORAGE_KEY } from '#lib/stores/cart.svelte.ts';
import { chickenRice, makeFood, MemoryStorage, milkTea } from './fixtures.ts';

describe('cart', () => {
	let storage: MemoryStorage;
	let cart: CartStore;

	beforeEach(() => {
		storage = new MemoryStorage();
		cart = new CartStore(storage);
		cart.load();
	});

	it('adds items and calculates totals instantly (Chicken Rice ×2 + Milk Tea = $3.75)', () => {
		expect(cart.add(chickenRice())).toBe('added');
		expect(cart.add(chickenRice())).toBe('added');
		expect(cart.add(milkTea())).toBe('added');
		expect(cart.lines).toHaveLength(2);
		expect(cart.count).toBe(3);
		expect(cart.subtotalCents).toBe(375);
		expect(cart.totalString).toBe('3.75');
	});

	it('changes quantities and removes items at zero', () => {
		cart.add(chickenRice());
		cart.increment(101);
		expect(cart.quantityOf(101)).toBe(2);
		cart.decrement(101);
		cart.decrement(101);
		expect(cart.quantityOf(101)).toBe(0);
		expect(cart.lines).toHaveLength(0);
	});

	it('caps quantities at stock and the per-order limit', () => {
		const lowStock = makeFood({ id: 7, stock_quantity: 2 });
		cart.add(lowStock);
		cart.add(lowStock);
		expect(cart.add(lowStock)).toBe('max');
		expect(cart.quantityOf(7)).toBe(2);
		cart.add(chickenRice(), 50);
		expect(cart.quantityOf(101)).toBe(MAX_PER_ITEM);
	});

	it('refuses sold-out and unavailable food', () => {
		expect(cart.add(makeFood({ is_sold_out: true, stock_quantity: 0 }))).toBe('unavailable');
		expect(cart.add(makeFood({ is_available: false, is_sold_out: true }))).toBe('unavailable');
		expect(cart.count).toBe(0);
	});

	it('removes a single item and clears the cart', () => {
		cart.add(chickenRice());
		cart.add(milkTea());
		cart.remove(101);
		expect(cart.lines.map((l) => l.foodId)).toEqual([102]);
		cart.clear();
		expect(cart.count).toBe(0);
	});

	it('persists to storage so a refresh keeps the cart', () => {
		cart.add(chickenRice(), 2);
		const reloaded = new CartStore(storage);
		reloaded.load();
		expect(reloaded.quantityOf(101)).toBe(2);
		expect(reloaded.totalString).toBe('3.00');
	});

	it('ignores corrupted storage', () => {
		storage.setItem(STORAGE_KEY, '{not json');
		const reloaded = new CartStore(storage);
		reloaded.load();
		expect(reloaded.lines).toEqual([]);
		storage.setItem(STORAGE_KEY, JSON.stringify([{ foodId: 1, price: '1.0.0', quantity: 1 }]));
		const filtered = new CartStore(storage);
		filtered.load();
		expect(filtered.lines).toEqual([]);
	});

	it('syncs with fresh menu data: new prices, clamped stock, removed items', () => {
		cart.add(chickenRice(), 3);
		cart.add(milkTea());
		const changed = cart.sync([
			{ ...chickenRice(), price: '1.75', stock_quantity: 2 },
			{ ...milkTea(), is_sold_out: true, stock_quantity: 0 }
		]);
		expect(changed).toBe(true);
		expect(cart.lines).toHaveLength(1);
		expect(cart.lines[0].price).toBe('1.75');
		expect(cart.quantityOf(101)).toBe(2);
		expect(cart.totalString).toBe('3.50');
		expect(cart.sync([{ ...chickenRice(), price: '1.75', stock_quantity: 2 }])).toBe(false);
	});
});
