import { browser } from '$app/env';

/**
 * Guest orders are protected by an unguessable access token returned once at checkout.
 * We keep it on this device so the student can track (and pay for) the order later.
 */
export interface RememberedOrder {
	id: string;
	number: string;
	token: string;
	total: string;
	createdAt: string;
}

const KEY = 'campuseats.orders.v1';
const MAX = 30;

function read(): RememberedOrder[] {
	if (!browser) return [];
	try {
		const parsed: unknown = JSON.parse(localStorage.getItem(KEY) ?? '[]');
		return Array.isArray(parsed)
			? parsed.filter((o) => o && typeof o.id === 'string' && typeof o.token === 'string')
			: [];
	} catch {
		return [];
	}
}

function write(orders: RememberedOrder[]): void {
	try {
		localStorage.setItem(KEY, JSON.stringify(orders.slice(0, MAX)));
	} catch {
		/* ignore */
	}
}

export function rememberOrder(order: RememberedOrder): void {
	write([order, ...read().filter((o) => o.id !== order.id)]);
}

export function rememberedOrders(): RememberedOrder[] {
	return read();
}

export function orderToken(id: string): string | null {
	return read().find((o) => o.id === id)?.token ?? null;
}

/** Accept a token shared via a private link fragment (#t=...), which never reaches servers. */
export function adoptTokenFromHash(id: string, number = ''): string | null {
	if (!browser) return null;
	const match = /(?:^#|&)t=([A-Za-z0-9_-]{20,})/.exec(location.hash);
	if (!match) return null;
	const existing = read().find((o) => o.id === id);
	rememberOrder({
		id,
		number: existing?.number ?? number,
		token: match[1],
		total: existing?.total ?? '',
		createdAt: existing?.createdAt ?? new Date().toISOString()
	});
	history.replaceState(history.state, '', location.pathname + location.search);
	return match[1];
}

export function forgetOrder(id: string): void {
	write(read().filter((o) => o.id !== id));
}
