import { expect, test } from '@playwright/test';

test('mobile: add to cart, floating cart and drawer', async ({ page }) => {
	await page.goto('/menu');
	await expect(page.getByTestId('cart-panel')).toBeHidden(); // no side panel on phones
	await page
		.getByTestId('food-card')
		.filter({ hasText: 'Fried Rice' })
		.getByTestId('add-to-cart')
		.tap();
	await page
		.getByTestId('food-card')
		.filter({ hasText: 'Sandwich' })
		.getByTestId('add-to-cart')
		.tap();
	const floating = page.getByTestId('floating-cart');
	await expect(floating).toBeVisible();
	await expect(floating).toContainText('$3.00');
	await floating.tap();
	const drawer = page.getByRole('dialog');
	await expect(drawer.getByTestId('cart-line')).toHaveCount(2);
	await drawer.getByRole('button', { name: 'Increase quantity of Sandwich' }).tap();
	await expect(drawer.getByTestId('cart-total')).toHaveText('$4.25');
	await drawer.getByRole('link', { name: /Proceed to Checkout/ }).tap();
	await expect(page).toHaveURL(/\/checkout/);
	await expect(page.getByTestId('checkout-total')).toHaveText('$4.25');
});
