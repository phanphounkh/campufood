import { api, type Fetch } from './api';
import type {
	DemoConfirmResult,
	Order,
	OrderCreateInput,
	OrderCreated,
	OrderStatus,
	Page,
	PaymentCheckout,
	PaymentStatusInfo
} from '#lib/types/api.ts';

// ── Student ───────────────────────────────────────────────────

export const createOrder = (body: OrderCreateInput) =>
	api<OrderCreated>('/orders', { method: 'POST', body });

export const getOrder = (id: string, orderToken?: string | null, fetch?: Fetch) =>
	api<Order>(`/orders/${id}`, { orderToken, fetch });

export const cancelOrder = (id: string, orderToken?: string | null) =>
	api<Order>(`/orders/${id}/cancel`, { method: 'POST', orderToken });

export const myOrders = (page = 1, fetch?: Fetch) =>
	api<Page<Order>>('/orders/mine', { query: { page, page_size: 20 }, fetch });

// ── Demo KHQR payment ─────────────────────────────────────────

export const openDemoPayment = (orderId: string, orderToken?: string | null, fetch?: Fetch) =>
	api<PaymentCheckout>('/payments/demo/create', {
		method: 'POST',
		body: { order_id: orderId },
		orderToken,
		fetch
	});

export const confirmDemoPayment = (
	orderId: string,
	paymentId: string,
	orderToken?: string | null
) =>
	api<DemoConfirmResult>('/payments/demo/confirm', {
		method: 'POST',
		body: { order_id: orderId, payment_id: paymentId },
		orderToken
	});

export const paymentStatus = (paymentId: string, orderToken?: string | null) =>
	api<PaymentStatusInfo>(`/payments/${paymentId}/status`, { orderToken });

// ── Staff ─────────────────────────────────────────────────────

export interface AdminOrderQuery {
	status?: OrderStatus[];
	search?: string;
	date_from?: string;
	date_to?: string;
	page?: number;
	page_size?: number;
}

export const listAdminOrders = (query: AdminOrderQuery = {}, fetch?: Fetch) =>
	api<Page<Order>>('/admin/orders', { query: { ...query }, fetch });

export const getAdminOrder = (id: string, fetch?: Fetch) =>
	api<Order>(`/admin/orders/${id}`, { fetch });

export const ordersSummary = (fetch?: Fetch) =>
	api<Record<OrderStatus | 'all', number>>('/admin/orders-summary', { fetch });

export const updateOrderStatus = (id: string, status: OrderStatus, reason?: string) =>
	api<Order>(`/orders/${id}/status`, { method: 'PATCH', body: { status, reason } });
