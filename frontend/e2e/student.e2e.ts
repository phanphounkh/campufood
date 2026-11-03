import { expect, test } from '@playwright/test';

test.describe('student ordering journey', () => {
	test('browse, filter, drag to cart, checkout, demo-pay and track', async ({ page }) => {
		await page.goto('/');
		await expect(page.getByRole('heading', { level: 1 })).toContainText(
			'Delicious Meals for Students'
		);
		await page.getByRole('link', { name: 'Order Now' }).first().click();
		await expect(page).toHaveURL(/\/menu/);

		// Category filter + search
		await page.getByRole('button', { name: 'Drinks', exact: true }).click();
		await expect(page.getByTestId('food-card')).toHaveCount(4);
		await page.getByRole('button', { name: 'All', exact: true }).click();
		await page.getByTestId('menu-search').fill('sandwich');
		await expect(page.getByTestId('food-card')).toHaveCount(1);
		await page.getByTestId('menu-search').fill('');

		// Add to cart button (twice) → Chicken Rice × 2
		const chicken = page.getByTestId('food-card').filter({ hasText: 'Chicken Rice' });
		await chicken.getByTestId('add-to-cart').click();
		await chicken.getByTestId('add-to-cart').click();

		// Drag & drop Iced Milk Tea into the cart panel
		const tea = page.getByTestId('food-card').filter({ hasText: 'Iced Milk Tea' });
		const from = (await tea.boundingBox())!;
		const to = (await page.getByTestId('cart-panel').boundingBox())!;
		await page.mouse.move(from.x + from.width / 2, from.y + 100);
		await page.mouse.down();
		await page.mouse.move(from.x + from.width / 2 + 30, from.y + 130, { steps: 5 });
		await page.mouse.move(to.x + to.width / 2, to.y + to.height / 2, { steps: 15 });
		await expect(page.getByTestId('cart-panel').getByText('Drop here')).toBeVisible();
		await page.mouse.up();

		await expect(page.getByTestId('cart-line')).toHaveCount(2);
		await expect(page.getByTestId('cart-total')).toHaveText('$3.75');
		await expect(page.getByTestId('cart-count')).toHaveText('3');

		// The cart survives a refresh
		await page.reload();
		await expect(page.getByTestId('cart-total')).toHaveText('$3.75');

		// Checkout validation
		await page.getByRole('link', { name: /Proceed to Checkout/ }).click();
		await page.getByTestId('place-order').click();
		await expect(page.getByText('Please enter your name')).toBeVisible();
		await expect(page.getByText(/Enter a valid phone number/)).toBeVisible();

		await page.fill('#customer_name', 'Sokha Chan');
		await page.fill('#customer_phone', '012 345 678');
		await page.fill('#notes', 'Less spicy please');
		await expect(page.getByTestId('checkout-total')).toHaveText('$3.75');
		await page.getByTestId('place-order').click();

		// Demo KHQR payment
		await page.waitForURL(/\/pay$/);
		await expect(page.getByTestId('demo-banner')).toHaveText(
			/DEMO PAYMENT — NO REAL MONEY WILL BE TRANSFERRED/
		);
		await expect(page.getByTestId('pay-amount')).toHaveText('$3.75');
		await expect(page.getByTestId('countdown')).toContainText(/\d\d:\d\d/);
		await expect(page.getByRole('img', { name: /Demo QR code/ })).toBeVisible();
		await page.getByTestId('simulate-payment').click();
		await expect(page.getByTestId('payment-success')).toContainText('Payment successful!');

		// Tracking
		await page.getByTestId('track-order').click();
		await expect(page.getByTestId('order-number')).toContainText(/Order CE-\d+/);
		await expect(page.getByText('Confirmed').first()).toBeVisible();
		await expect(page.getByText('Paid', { exact: true })).toBeVisible();
		await expect(page.getByText('Less spicy please')).toBeVisible();

		// My Orders lists it (guest token remembered on this device)
		await page.getByRole('link', { name: 'My Orders' }).first().click();
		await expect(page.getByTestId('orders-list')).toContainText('$3.75');
	});

	test('switches between English and Khmer', async ({ page }) => {
		await page.goto('/menu');
		await page.getByRole('button', { name: 'KH', exact: true }).click();
		await expect(page.getByRole('heading', { level: 1 })).toHaveText('មុខម្ហូបរបស់យើង');
		await expect(page.locator('html')).toHaveAttribute('lang', 'km');
		await page.reload(); // the choice persists (cookie) and is rendered by the server
		await expect(page.getByRole('heading', { level: 1 })).toHaveText('មុខម្ហូបរបស់យើង');
		await page.getByRole('button', { name: 'EN', exact: true }).click();
		await expect(page.getByRole('heading', { level: 1 })).toHaveText('Our Menu');
	});

	test('guests cannot open someone else’s order', async ({ page }) => {
		await page.goto('/orders/00000000-0000-4000-8000-000000000000');
		await expect(page.getByText('Order not found')).toBeVisible();
	});
});
