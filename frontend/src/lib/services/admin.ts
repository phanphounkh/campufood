import { api, API_BASE, buildQuery, type Fetch } from './api';
import type {
	AdminPayment,
	Customer,
	Dashboard,
	InventoryItem,
	InventoryMovement,
	Page,
	PaymentStatus,
	PaymentSummary,
	Report,
	Role,
	StoreSettings,
	User
} from '#lib/types/api.ts';

export type DashboardRange = 'today' | '7d' | '30d';
export type Granularity = 'day' | 'week' | 'month';

export const getDashboard = (range: DashboardRange, fetch?: Fetch) =>
	api<Dashboard>('/admin/dashboard', { query: { range }, fetch });

export interface ReportQuery {
	date_from?: string;
	date_to?: string;
	granularity?: Granularity;
}

export const getReport = (query: ReportQuery, fetch?: Fetch) =>
	api<Report>('/admin/reports', { query: { ...query }, fetch });

/** Same-origin URL; the session cookie authorises the download. */
export const reportCsvUrl = (query: ReportQuery) =>
	`${API_BASE}/admin/reports/export${buildQuery({ ...query })}`;

export const getInventory = (query: { search?: string; low_only?: boolean } = {}, fetch?: Fetch) =>
	api<InventoryItem[]>('/admin/inventory', { query, fetch });

export interface InventoryUpdate {
	mode: 'set' | 'adjust';
	quantity: number;
	reason: 'restock' | 'manual_adjustment';
	note?: string;
	is_available?: boolean;
}

export const updateInventory = (foodId: number, body: InventoryUpdate) =>
	api<InventoryItem>(`/admin/inventory/${foodId}`, { method: 'PATCH', body });

export const getMovements = (query: { food_id?: number; page?: number } = {}, fetch?: Fetch) =>
	api<Page<InventoryMovement>>('/admin/inventory/movements', { query, fetch });

export const getCustomers = (query: { search?: string; page?: number } = {}, fetch?: Fetch) =>
	api<Page<Customer>>('/admin/customers', { query, fetch });

export const getPayments = (
	query: { status?: PaymentStatus; search?: string; page?: number } = {},
	fetch?: Fetch
) => api<Page<AdminPayment>>('/admin/payments', { query, fetch });

export const getPaymentSummary = (fetch?: Fetch) =>
	api<PaymentSummary>('/admin/payments/summary', { fetch });

export const getStoreSettings = (fetch?: Fetch) => api<StoreSettings>('/admin/settings', { fetch });

export const updateStoreSettings = (body: Partial<StoreSettings>) =>
	api<StoreSettings>('/admin/settings', { method: 'PATCH', body });

export const listStaff = (fetch?: Fetch) => api<User[]>('/admin/users', { fetch });

export const createStaff = (body: {
	name: string;
	email: string;
	phone?: string;
	password: string;
	role: Exclude<Role, 'customer'>;
}) => api<User>('/admin/users', { method: 'POST', body });

export const updateStaff = (id: number, body: { role?: Role; is_active?: boolean }) =>
	api<User>(`/admin/users/${id}`, { method: 'PATCH', body });
