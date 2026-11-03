import { error, redirect } from '@sveltejs/kit';
import { adminHref } from '#lib/components/admin/links.ts';
import type { User } from '#lib/types/api.ts';
import type { LayoutServerLoad } from './$types';

/**
 * Server-side guard for every /admin page. The API enforces roles on each request; this only
 * keeps non-staff visitors from seeing the admin shell at all.
 */
export const load: LayoutServerLoad = async ({ fetch, url }) => {
	const response = await fetch('/api/v1/auth/me');
	const next = url.pathname + url.search;

	if (response.status === 401) redirect(303, adminHref('/admin/login', { next }));
	if (!response.ok) error(503, 'The CampusEats API is not reachable right now.');

	const user = (await response.json()) as User;
	if (user.role !== 'admin' && user.role !== 'staff') {
		redirect(303, adminHref('/admin/login', { next, forbidden: 1 }));
	}
	return { user };
};
