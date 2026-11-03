import { attempt } from '#lib/components/admin/errors.ts';
import { getReport, type Granularity } from '#lib/services/admin.ts';
import { shiftDays, todayISO } from '#lib/utils/format.ts';
import type { PageLoad } from './$types';

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export const load: PageLoad = async ({ fetch, url }) => {
	const today = todayISO();
	const rawTo = url.searchParams.get('to');
	const rawFrom = url.searchParams.get('from');
	const to = rawTo && ISO_DATE.test(rawTo) ? rawTo : today;
	const from = rawFrom && ISO_DATE.test(rawFrom) ? rawFrom : shiftDays(to, -29);
	const rawG = url.searchParams.get('g');
	const granularity: Granularity = rawG === 'week' || rawG === 'month' ? rawG : 'day';

	if (from > to) {
		return { from, to, granularity, report: null, error: null, invalidRange: true };
	}
	const result = await attempt(() =>
		getReport({ date_from: from, date_to: to, granularity }, fetch)
	);
	return {
		from,
		to,
		granularity,
		report: result.ok ? result.value : null,
		error: result.ok ? null : result.error,
		invalidRange: false
	};
};
