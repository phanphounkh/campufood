import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Browser, type Page } from '@playwright/test';
import { ADMIN_EMAIL, ADMIN_PASSWORD, placeGuestOrder } from './helpers.ts';

test.skip(!ADMIN_PASSWORD, 'Set E2E_ADMIN_PASSWORD or SEED_ADMIN_PASSWORD to run admin tests');

async function adminPage(browser: Browser): Promise<Page> {
	const page = await (
		await browser.newContext({ viewport: { width: 1440, height: 900 } })
	).newPage();
	await page.goto('/admin');
	await expect(page).toHaveURL(/\/admin\/login/); // protected route redirects
	await page.fill('#email', ADMIN_EMAIL);
	await page.fill('#password', ADMIN_PASSWORD);
	await page.getByRole('button', { name: 'Sign in' }).click();
	await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
	return page;
}

async function paidStudentOrder(browser: Browser, name: string) {
	const student = await (await browser.newContext()).newPage();
	const number = await placeGuestOrder(student, ['Chicken Rice', 'Iced Milk Tea'], name);
	await student.getByTestId('simulate-payment').click();
	await expect(student.getByTestId('payment-success')).toBeVisible();
	await student.getByTestId('track-order').click();
	await expect(student.getByTestId('order-timeline')).toBeVisible();
	return { student, number };
}

test('admin processes a paid order from confirmed to completed', async ({ browser }) => {
	const { student, number } = await paidStudentOrder(browser, 'E2E Kitchen Flow');
	const admin = await adminPage(browser);

	await admin.goto('/admin/orders');
	await admin.getByRole('textbox', { name: 'Search order #, name or phone' }).fill(number);
	const row = admin.locator('tr', { hasText: number });
	await expect(row).toContainText('Confirmed');
	await expect(row).toContainText('Paid');

	await row.getByRole('button', { name: 'Accept' }).click();
	await expect(row).toContainText('Preparing');
	await row.getByRole('button', { name: 'Mark ready' }).click();
	await expect(row).toContainText('Ready for Pickup');

	// The student's tracking page polls and shows the update.
	await expect(student.getByText('Your food is ready!')).toBeVisible({ timeout: 15_000 });

	await row.getByRole('button', { name: 'Complete' }).click();
	await expect(row).toContainText('Completed');
	await expect(student.getByText('Completed').first()).toBeVisible({ timeout: 15_000 });
});

test('admin cancels a paid order with a reason (refund + student sees it)', async ({ browser }) => {
	const { student, number } = await paidStudentOrder(browser, 'E2E Cancel Flow');
	const admin = await adminPage(browser);

	await admin.goto('/admin/orders');
	await admin.getByRole('textbox', { name: 'Search order #, name or phone' }).fill(number);
	const row = admin.locator('tr', { hasText: number });
	await row.getByRole('button', { name: new RegExp(`Cancel.*${number}`) }).click();
	const dialog = admin.getByRole('dialog');
	await dialog.getByRole('textbox').fill('Out of chicken today');
	await dialog.getByRole('button', { name: /Cancel order/ }).click();
	await expect(row).toContainText('Cancelled');
	await expect(row).toContainText('Refunded');

	await expect(student.getByText('Reason: Out of chicken today')).toBeVisible({ timeout: 15_000 });
});

test('admin pages pass automated accessibility checks', async ({ browser }) => {
	const admin = await adminPage(browser);
	for (const path of ['/admin', '/admin/orders', '/admin/menu', '/admin/reports']) {
		await admin.goto(path);
		await admin.waitForLoadState('networkidle');
		const results = await new AxeBuilder({ page: admin }).withTags(['wcag2a', 'wcag2aa']).analyze();
		const blocking = results.violations.filter((v) =>
			['serious', 'critical'].includes(v.impact ?? '')
		);
		expect(
			blocking.map((v) => `${path} ${v.id}: ${v.nodes.map((n) => n.target).join(', ')}`)
		).toEqual([]);
	}
});
