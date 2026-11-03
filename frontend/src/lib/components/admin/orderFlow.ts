import type { Order, OrderStatus } from '#lib/types/api.ts';

/** The single forward step staff can take from each status (mirrors the API state machine). */
export const NEXT_STEP: Partial<Record<OrderStatus, { to: OrderStatus; labelKey: string }>> = {
	confirmed: { to: 'preparing', labelKey: 'admin.orders.accept' },
	preparing: { to: 'ready', labelKey: 'admin.orders.markReady' },
	ready: { to: 'completed', labelKey: 'admin.orders.complete' }
};

export const CANCELLABLE: OrderStatus[] = ['pending_payment', 'confirmed', 'preparing', 'ready'];

export const ORDER_STATUSES: OrderStatus[] = [
	'pending_payment',
	'confirmed',
	'preparing',
	'ready',
	'completed',
	'cancelled'
];

export function itemCount(order: Order): number {
	return order.items.reduce((sum, item) => sum + item.quantity, 0);
}

export function itemName(item: Order['items'][number], locale: 'en' | 'km'): string {
	return (locale === 'km' && item.food_name_km_snapshot) || item.food_name_snapshot;
}

export function isPaid(order: Order): boolean {
	return order.payment?.status === 'paid';
}
