import { ApiError, type Fetch } from './api.ts';
import { getOrder } from './orders.ts';
import { adoptTokenFromHash, orderToken } from '#lib/stores/guestOrders.ts';
import type { Order } from '#lib/types/api.ts';

/**
 * Load an order using the best credential available on this device: a token shared through a
 * private link (#t=...), a token remembered from checkout, or the logged-in session.
 */
export async function loadOrderForGuest(
	id: string,
	fetch?: Fetch
): Promise<{ order: Order | null; token: string | null }> {
	const token = adoptTokenFromHash(id) ?? orderToken(id);
	try {
		return { order: await getOrder(id, token, fetch), token };
	} catch (err) {
		if (err instanceof ApiError && (err.status === 404 || err.status === 422)) {
			return { order: null, token };
		}
		throw err;
	}
}
