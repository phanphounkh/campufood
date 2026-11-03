/** Types mirroring the FastAPI schemas. Money values are 2-decimal strings, e.g. "1.50". */

export type Money = string;
export type Role = 'admin' | 'staff' | 'customer';
export type OrderStatus =
	'pending_payment' | 'confirmed' | 'preparing' | 'ready' | 'completed' | 'cancelled';
export type PaymentStatus = 'pending' | 'paid' | 'failed' | 'expired' | 'cancelled' | 'refunded';
export type InventoryReason =
	'initial' | 'restock' | 'manual_adjustment' | 'order_reserved' | 'order_released';

export interface Page<T> {
	items: T[];
	total: number;
	page: number;
	page_size: number;
}

export interface CategoryBrief {
	id: number;
	slug: string;
	name_en: string;
	name_km: string;
}

export interface Category extends CategoryBrief {
	sort_order: number;
	created_at: string;
	food_count: number;
}

export interface Food {
	id: number;
	category_id: number;
	category: CategoryBrief;
	name_en: string;
	name_km: string;
	description_en: string;
	description_km: string;
	price: Money;
	image_url: string | null;
	stock_quantity: number;
	is_available: boolean;
	is_featured: boolean;
	is_archived: boolean;
	is_sold_out: boolean;
	created_at: string;
	updated_at: string;
}

export interface FoodInput {
	category_id: number;
	name_en: string;
	name_km: string;
	description_en: string;
	description_km: string;
	price: Money;
	image_url: string | null;
	stock_quantity: number;
	is_available: boolean;
	is_featured: boolean;
}

export interface User {
	id: number;
	name: string;
	email: string;
	phone: string | null;
	role: Role;
	is_active: boolean;
	created_at: string;
}

export interface Session {
	user: User;
	csrf_token: string;
	expires_at: string;
}

export interface OrderItem {
	id: number;
	food_id: number | null;
	food_name_snapshot: string;
	food_name_km_snapshot: string;
	quantity: number;
	unit_price: Money;
	line_total: Money;
}

export interface Payment {
	id: string;
	order_id: string;
	provider: string;
	amount: Money;
	currency: string;
	status: PaymentStatus;
	transaction_reference: string | null;
	expires_at: string;
	paid_at: string | null;
	refunded_at: string | null;
	created_at: string;
}

export interface PaymentCheckout extends Payment {
	qr_payload: string | null;
	is_demo: boolean;
}

export interface Order {
	id: string;
	order_number: string;
	user_id: number | null;
	customer_name: string;
	customer_phone: string;
	student_id: string | null;
	pickup_time: string;
	notes: string | null;
	subtotal: Money;
	total: Money;
	status: OrderStatus;
	cancel_reason: string | null;
	created_at: string;
	updated_at: string;
	items: OrderItem[];
	payment: Payment | null;
}

export interface OrderCreateInput {
	customer_name: string;
	customer_phone: string;
	student_id?: string | null;
	pickup_time: string;
	notes?: string | null;
	items: { food_id: number; quantity: number }[];
	expected_total?: Money;
}

export interface OrderCreated {
	order: Order;
	payment: PaymentCheckout;
	access_token: string;
}

export interface PaymentStatusInfo {
	payment_id: string;
	order_id: string;
	order_number: string;
	status: PaymentStatus;
	order_status: OrderStatus;
	amount: Money;
	currency: string;
	expires_at: string;
	paid_at: string | null;
	transaction_reference: string | null;
}

export interface DemoConfirmResult extends PaymentStatusInfo {
	already_confirmed: boolean;
}

export interface StoreSettings {
	store_name: string;
	store_tagline: string;
	store_phone: string;
	store_email: string;
	store_address: string;
	opening_time: string;
	closing_time: string;
	accepting_orders: boolean;
	min_prep_minutes: number;
	payment_expiry_minutes: number;
	low_stock_threshold: number;
	facebook_url: string;
	telegram_url: string;
	instagram_url: string;
}

export interface PublicSettings extends StoreSettings {
	demo_payments_enabled: boolean;
	timezone: string;
	currency: string;
}

// ── Admin ─────────────────────────────────────────────────────

export interface KpiValue<T = number | Money> {
	value: T;
	previous: T;
	change_pct: number | null;
}

export interface TimePoint {
	label: string;
	start: string;
	orders: number;
	revenue: Money;
}

export interface PopularItem {
	food_id: number | null;
	name_en: string;
	name_km: string;
	image_url: string | null;
	quantity: number;
	revenue: Money;
}

export interface RecentOrder {
	id: string;
	order_number: string;
	customer_name: string;
	item_count: number;
	items_summary: string;
	total: Money;
	payment_status: PaymentStatus | null;
	status: OrderStatus;
	created_at: string;
}

export interface Dashboard {
	range: 'today' | '7d' | '30d';
	generated_at: string;
	total_orders: KpiValue<number>;
	revenue: KpiValue<Money>;
	completed_orders: KpiValue<number>;
	average_order_value: KpiValue<Money>;
	pending_orders: number;
	in_progress_orders: number;
	awaiting_payment: number;
	low_stock_count: number;
	sales_over_time: TimePoint[];
	daily_revenue: TimePoint[];
	orders_by_status: { status: OrderStatus; count: number }[];
	popular_items: PopularItem[];
	recent_orders: RecentOrder[];
}

export interface ReportPeriod {
	period: string;
	start: string;
	orders: number;
	items_sold: number;
	gross_sales: Money;
	refunds: Money;
	net_revenue: Money;
	cancelled_orders: number;
}

export interface Report {
	date_from: string;
	date_to: string;
	granularity: 'day' | 'week' | 'month';
	totals: {
		orders: number;
		items_sold: number;
		gross_sales: Money;
		refunds: Money;
		net_revenue: Money;
		cancelled_orders: number;
		refunded_orders: number;
		average_order_value: Money;
	};
	periods: ReportPeriod[];
	best_sellers: PopularItem[];
}

export interface InventoryItem {
	food_id: number;
	name_en: string;
	name_km: string;
	category_name_en: string;
	image_url: string | null;
	stock_quantity: number;
	is_available: boolean;
	low_stock: boolean;
	reserved_quantity: number;
	updated_at: string;
}

export interface InventoryMovement {
	id: number;
	food_id: number;
	food_name_en: string;
	order_id: string | null;
	order_number: string | null;
	quantity_change: number;
	reason: InventoryReason;
	note: string | null;
	created_at: string;
}

export interface Customer {
	customer_phone: string;
	customer_name: string;
	is_registered: boolean;
	email: string | null;
	orders_count: number;
	paid_orders: number;
	total_spent: Money;
	first_order_at: string;
	last_order_at: string;
}

export interface AdminPayment extends Payment {
	order_number: string;
	customer_name: string;
}

export interface PaymentSummary {
	collected: Money;
	refunded: Money;
	pending: Money;
	count_by_status: Record<PaymentStatus, number>;
}

export interface ApiErrorBody {
	error: {
		code: string;
		message: string;
		details: unknown;
	};
}
