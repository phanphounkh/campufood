import type { Locale } from '#lib/i18n/locales.ts';

export const CANTEEN_TZ = 'Asia/Phnom_Penh';

const intlLocale = (locale: Locale) => (locale === 'km' ? 'km-KH' : 'en-US');

export function formatTime(iso: string, locale: Locale, timeZone = CANTEEN_TZ): string {
	return new Intl.DateTimeFormat(intlLocale(locale), {
		hour: 'numeric',
		minute: '2-digit',
		timeZone
	}).format(new Date(iso));
}

export function formatDate(iso: string, locale: Locale, timeZone = CANTEEN_TZ): string {
	return new Intl.DateTimeFormat(intlLocale(locale), {
		day: 'numeric',
		month: 'short',
		year: 'numeric',
		timeZone
	}).format(new Date(iso));
}

export function formatDateTime(iso: string, locale: Locale, timeZone = CANTEEN_TZ): string {
	return new Intl.DateTimeFormat(intlLocale(locale), {
		day: 'numeric',
		month: 'short',
		hour: 'numeric',
		minute: '2-digit',
		timeZone
	}).format(new Date(iso));
}

/** Is `iso` on the same canteen-local calendar day as now? */
export function isToday(iso: string, timeZone = CANTEEN_TZ): boolean {
	const fmt = new Intl.DateTimeFormat('en-CA', { timeZone, dateStyle: 'short' });
	return fmt.format(new Date(iso)) === fmt.format(new Date());
}

export function todayISO(timeZone = CANTEEN_TZ): string {
	return new Intl.DateTimeFormat('en-CA', { timeZone, dateStyle: 'short' }).format(new Date());
}

export function shiftDays(isoDate: string, days: number): string {
	const d = new Date(`${isoDate}T00:00:00Z`);
	d.setUTCDate(d.getUTCDate() + days);
	return d.toISOString().slice(0, 10);
}

export function formatCountdown(ms: number): string {
	const total = Math.max(0, Math.floor(ms / 1000));
	const m = Math.floor(total / 60);
	const s = total % 60;
	return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export function formatNumber(value: number, locale: Locale): string {
	return new Intl.NumberFormat(intlLocale(locale)).format(value);
}
