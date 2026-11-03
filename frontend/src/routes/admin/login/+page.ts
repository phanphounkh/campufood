import { redirect } from '@sveltejs/kit';
import type { ResolvedPathname } from '$app/types';
import { adminHref } from '#lib/components/admin/links.ts';
import { currentUser } from '#lib/services/auth.ts';
import type { PageLoad } from './$types';

/** Only allow same-site relative paths as the post-login destination. */
function safeNext(value: string | null): ResolvedPathname {
	// `next` comes from our own url.pathname, so it is already base-path aware.
	return value && value.startsWith(adminHref('/admin')) && !value.startsWith('//')
		? (value as ResolvedPathname)
		: adminHref('/admin');
}

export const load: PageLoad = async ({ fetch, url }) => {
	const next = safeNext(url.searchParams.get('next'));
	const user = await currentUser(fetch).catch(() => null);
	if (user && (user.role === 'admin' || user.role === 'staff')) redirect(303, next);
	return { next, forbidden: url.searchParams.has('forbidden') };
};
