import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

/** Fail on serious/critical WCAG 2.1 A/AA violations. */
async function audit(page: Page) {
	const results = await new AxeBuilder({ page })
		.withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
		.analyze();
	const blocking = results.violations.filter((v) =>
		['serious', 'critical'].includes(v.impact ?? '')
	);
	expect(
		blocking.map((v) => `${v.id}: ${v.help} (${v.nodes.map((n) => n.target.join(' ')).join(', ')})`)
	).toEqual([]);
}

for (const path of ['/', '/menu', '/about', '/login', '/orders']) {
	test(`accessibility: ${path}`, async ({ page }) => {
		await page.goto(path);
		await page.waitForLoadState('networkidle');
		await audit(page);
	});
}

test('accessibility: Khmer menu', async ({ page, context }) => {
	await context.addCookies([{ name: 'ce_locale', value: 'km', url: 'http://localhost:4173' }]);
	await page.goto('/menu');
	await expect(page.locator('html')).toHaveAttribute('lang', 'km');
	await audit(page);
});

test('accessibility: checkout with items', async ({ page }) => {
	await page.goto('/menu');
	await page
		.getByTestId('food-card')
		.filter({ hasText: 'Fried Rice' })
		.getByTestId('add-to-cart')
		.click();
	await page.goto('/checkout');
	await page.waitForLoadState('networkidle');
	await audit(page);
});
