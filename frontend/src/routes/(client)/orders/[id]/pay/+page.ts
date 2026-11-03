import { loadOrderForGuest } from '#lib/services/orderAccess.ts';
import { openDemoPayment } from '#lib/services/orders.ts';
import type { PageLoad } from './$types';

// Order access tokens live in localStorage, so these pages render in the browser.
export const ssr = false;

export const load: PageLoad = async ({ params, fetch }) => {
	const result = await loadOrderForGuest(params.id, fetch);
	if (!result.order) return { ...result, payment: null };
	const payment = await openDemoPayment(params.id, result.token, fetch).catch(() => null);
	return { ...result, payment };
};
