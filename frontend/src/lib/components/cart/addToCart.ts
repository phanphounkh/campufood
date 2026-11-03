import { cart } from '#lib/stores/cart.svelte.ts';
import { toast } from '#lib/stores/toast.svelte.ts';
import { i18n, t } from '#lib/i18n/index.svelte.ts';
import type { Food } from '#lib/types/api.ts';

/** Add a dish to the cart with user feedback (shared by buttons, drag-and-drop and keyboard). */
export function addToCart(food: Food, quantity = 1): boolean {
	const name = i18n.pick(food, 'name');
	const result = cart.add(food, quantity);
	if (result === 'added') {
		toast.success(t('food.added', { name }));
		return true;
	}
	if (result === 'max') {
		toast.info(t('food.maxReached', { count: Math.min(20, food.stock_quantity) }));
	} else {
		toast.error(`${name}: ${t('food.soldOut')}`);
	}
	return false;
}
