import { getPublicSettings } from '#lib/services/catalog.ts';
import { currentUser } from '#lib/services/auth.ts';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ fetch }) => {
	const [settings, user] = await Promise.all([
		getPublicSettings(fetch).catch(() => null),
		currentUser(fetch).catch(() => null)
	]);
	return { settings, user };
};
