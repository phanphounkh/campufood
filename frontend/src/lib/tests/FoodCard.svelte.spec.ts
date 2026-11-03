import { beforeEach, describe, expect, it } from 'vitest';
import { render } from 'vitest-browser-svelte';
import FoodCard from '#lib/components/food/FoodCard.svelte';
import { cart } from '#lib/stores/cart.svelte.ts';
import { i18n } from '#lib/i18n/index.svelte.ts';
import { chickenRice, makeFood } from './fixtures.ts';

describe('FoodCard', () => {
	beforeEach(() => {
		cart.clear();
		i18n.locale = 'en';
	});

	it('shows the dish in both languages with price, category and availability', async () => {
		const screen = render(FoodCard, { food: chickenRice() });
		await expect.element(screen.getByRole('heading', { name: 'Chicken Rice' })).toBeInTheDocument();
		await expect.element(screen.getByText('បាយមាន់')).toBeInTheDocument();
		await expect.element(screen.getByText('$1.50')).toBeInTheDocument();
		await expect.element(screen.getByText('Rice', { exact: true })).toBeInTheDocument();
		await expect.element(screen.getByText('Available')).toBeInTheDocument();
	});

	it('adds to the cart with the Add button', async () => {
		const screen = render(FoodCard, { food: chickenRice() });
		await screen.getByRole('button', { name: 'Add Chicken Rice to cart' }).click();
		await screen.getByRole('button', { name: 'Add Chicken Rice to cart' }).click();
		expect(cart.quantityOf(101)).toBe(2);
		await expect.element(screen.getByText('2 in cart')).toBeInTheDocument();
	});

	it('has a keyboard-accessible drag handle that adds the dish', async () => {
		const screen = render(FoodCard, { food: chickenRice() });
		const handle = screen.getByRole('button', { name: /Drag Chicken Rice to the cart/ });
		await handle.click();
		expect(cart.count).toBe(1);
	});

	it('marks sold-out dishes and disables adding', async () => {
		const screen = render(FoodCard, {
			food: makeFood({ name_en: 'Pumpkin Custard', is_sold_out: true, stock_quantity: 0 })
		});
		await expect.element(screen.getByText('Sold out').first()).toBeInTheDocument();
		await expect.element(screen.getByTestId('add-to-cart')).toBeDisabled();
		expect(cart.count).toBe(0);
	});

	it('renders Khmer as the primary language when selected', async () => {
		i18n.locale = 'km';
		const screen = render(FoodCard, { food: chickenRice() });
		await expect.element(screen.getByRole('heading', { name: 'បាយមាន់' })).toBeInTheDocument();
		await expect.element(screen.getByText('Chicken Rice')).toBeInTheDocument();
	});
});
