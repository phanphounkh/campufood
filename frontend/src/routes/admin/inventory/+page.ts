import { attempt } from '#lib/components/admin/errors.ts';
import { getInventory, getMovements, getStoreSettings } from '#lib/services/admin.ts';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url, depends }) => {
	depends('admin:inventory');
	const movementPage = Math.max(1, Number(url.searchParams.get('mpage')) || 1);
	const [items, movements, settings] = await Promise.all([
		attempt(() => getInventory({}, fetch)),
		attempt(() => getMovements({ page: movementPage }, fetch)),
		attempt(() => getStoreSettings(fetch))
	]);
	return {
		lowOnly: url.searchParams.get('low') === '1',
		items: items.ok ? items.value : null,
		movements: movements.ok ? movements.value : null,
		threshold: settings.ok ? settings.value.low_stock_threshold : null,
		movementPage,
		error: items.ok ? null : items.error
	};
};
