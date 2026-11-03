import type { Locale } from '#lib/i18n/locales.ts';
import type { TimePoint } from '#lib/types/api.ts';
import { toCents } from '#lib/utils/money.ts';
import type { ChartPoint } from './charts/scale.ts';

const intl = (locale: Locale) => (locale === 'km' ? 'km-KH' : 'en-US');

/** "2026-11-03" → "Nov 3" / "Mon, Nov 3" (dates are already canteen-local). */
export function dayLabels(isoDate: string, locale: Locale): { short: string; full: string } {
	const date = new Date(`${isoDate}T00:00:00Z`);
	const short = new Intl.DateTimeFormat(intl(locale), {
		month: 'short',
		day: 'numeric',
		timeZone: 'UTC'
	}).format(date);
	const full = new Intl.DateTimeFormat(intl(locale), {
		weekday: 'short',
		month: 'short',
		day: 'numeric',
		timeZone: 'UTC'
	}).format(date);
	return { short, full };
}

function hourLabels(label: string): { short: string; full: string } {
	const hour = Number(label.slice(0, 2));
	return { short: label, full: `${label}–${String(hour + 1).padStart(2, '0')}:00` };
}

export function revenuePoints(
	points: TimePoint[],
	locale: Locale,
	detail: (orders: number) => string
): ChartPoint[] {
	return points.map((p) => {
		const labels = /^\d{2}:\d{2}$/.test(p.label) ? hourLabels(p.label) : dayLabels(p.label, locale);
		return {
			label: labels.short,
			fullLabel: labels.full,
			value: toCents(p.revenue),
			detail: detail(p.orders)
		};
	});
}

export function orderPoints(
	points: TimePoint[],
	locale: Locale,
	detail: (revenue: string) => string
): ChartPoint[] {
	return points.map((p) => {
		const labels = /^\d{2}:\d{2}$/.test(p.label) ? hourLabels(p.label) : dayLabels(p.label, locale);
		return {
			label: labels.short,
			fullLabel: labels.full,
			value: p.orders,
			detail: detail(p.revenue)
		};
	});
}
