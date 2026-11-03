import { beforeEach, describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import CartPanel from '#lib/components/cart/CartPanel.svelte';
import { cart } from '#lib/stores/cart.svelte.ts';
import { i18n } from '#lib/i18n/index.svelte.ts';
import { chickenRice, milkTea } from './fixtures.ts';

describe('CartPanel', () => {
	beforeEach(() => {
		i18n.locale = 'en';
		cart.clear();
	});

	it('shows an empty state with a drop hint', async () => {
		const screen = render(CartPanel, { droppable: true });
		await expect.element(screen.getByText('Your cart is empty')).toBeInTheDocument();
		await expect
			.element(screen.getByText('Drag food here or tap + on a dish.'))
			.toBeInTheDocument();
	});

	it('calculates subtotal and total (Chicken Rice ×2 + Milk Tea = $3.75)', async () => {
		cart.add(chickenRice(), 2);
		cart.add(milkTea());
		const screen = render(CartPanel, {});
		await expect.element(screen.getByTestId('cart-total')).toHaveTextContent('$3.75');
		await expect.element(screen.getByText('× 2 = $3.00')).toBeInTheDocument();
		await expect.element(screen.getByText('(3 items)')).toBeInTheDocument();
	});

	it('updates totals instantly when quantities change', async () => {
		cart.add(chickenRice());
		const screen = render(CartPanel, {});
		await screen.getByRole('button', { name: 'Increase quantity of Chicken Rice' }).click();
		await expect.element(screen.getByTestId('cart-total')).toHaveTextContent('$3.00');
		await screen.getByRole('button', { name: 'Decrease quantity of Chicken Rice' }).click();
		await expect.element(screen.getByTestId('cart-total')).toHaveTextContent('$1.50');
		await screen.getByRole('button', { name: 'Remove Chicken Rice' }).click();
		await expect.element(screen.getByText('Your cart is empty')).toBeInTheDocument();
	});

	it('clears the cart after confirmation', async () => {
		cart.add(chickenRice());
		cart.add(milkTea());
		const screen = render(CartPanel, {});
		await screen.getByRole('button', { name: 'Clear' }).click();
		await screen.getByRole('dialog').getByRole('button', { name: 'Clear' }).click();
		expect(cart.count).toBe(0);
	});

	it('links to checkout', async () => {
		cart.add(milkTea());
		const screen = render(CartPanel, {});
		await expect
			.element(screen.getByRole('link', { name: /Proceed to Checkout/ }))
			.toHaveAttribute('href', '/checkout');
	});
});
