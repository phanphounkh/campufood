import { attempt } from '#lib/components/admin/errors.ts';
import { getStoreSettings, listStaff } from '#lib/services/admin.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, parent, depends }) => {
	depends('admin:settings');
	const { user } = await parent();
	const [settings, staff] = await Promise.all([
		attempt(() => getStoreSettings(fetch)),
		user.role === 'admin' ? attempt(() => listStaff(fetch)) : Promise.resolve(null)
	]);
	return {
		settings: settings.ok ? settings.value : null,
		staff: staff && staff.ok ? staff.value : null,
		error: settings.ok ? null : settings.error
	};
};
