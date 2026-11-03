import { expect, type Page } from '@playwright/test';

export const ADMIN_EMAIL =
	process.env.E2E_ADMIN_EMAIL ?? process.env.SEED_ADMIN_EMAIL ?? 'admin@campuseats.local';
export const ADMIN_PASSWORD =
	process.env.E2E_ADMIN_PASSWORD ?? process.env.SEED_ADMIN_PASSWORD ?? '';

/** Add dishes from the menu and complete a guest checkout. Returns the order number. */
export async function placeGuestOrder(
	page: Page,
	dishes: string[],
	name = 'E2E Student'
): Promise<string> {
	await page.goto('/menu');
	for (const dish of dishes) {
		await page
			.getByTestId('food-card')
			.filter({ hasText: dish })
			.getByTestId('add-to-cart')
			.click();
	}
	await page.goto('/checkout');
	await page.fill('#customer_name', name);
	await page.fill('#customer_phone', '012 345 678');
	await page.getByTestId('place-order').click();
	await page.waitForURL(/\/orders\/[0-9a-f-]+\/pay$/);
	await expect(page.getByTestId('demo-banner')).toContainText('DEMO PAYMENT');
	const label = await page
		.getByText(/Order CE-\d+/)
		.first()
		.textContent();
	return /CE-\d+/.exec(label ?? '')![0];
}
