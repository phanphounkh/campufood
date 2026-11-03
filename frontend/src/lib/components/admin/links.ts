import { resolve } from '$app/paths';
import type { ResolvedPathname } from '$app/types';
import { buildQuery } from '#lib/services/api.ts';

export type AdminRoute =
	| '/admin'
	| '/admin/login'
	| '/admin/orders'
	| '/admin/menu'
	| '/admin/categories'
	| '/admin/inventory'
	| '/admin/customers'
	| '/admin/payments'
	| '/admin/reports'
	| '/admin/settings';

type Query = Record<string, string | number | null | undefined>;

/** A base-path-aware admin URL with an optional query string. */
export function adminHref(route: AdminRoute, query?: Query): ResolvedPathname {
	return `${resolve(route)}${buildQuery(query)}` as ResolvedPathname;
}

/** Store front (outside the admin area). */
export function storeHref(): ResolvedPathname {
	return resolve('/(client)');
}
