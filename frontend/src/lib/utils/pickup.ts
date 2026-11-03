/**
 * Pickup time slots in the canteen's time zone (default Asia/Phnom_Penh), independent of the
 * visitor's own device time zone.
 */

export interface PickupSlot {
	/** ISO 8601 with offset, sent to the API. */
	value: string;
	/** "12:30" in canteen time. */
	time: string;
	day: 'today' | 'tomorrow';
}

interface ZonedParts {
	year: number;
	month: number;
	day: number;
	hour: number;
	minute: number;
}

function zonedParts(date: Date, timeZone: string): ZonedParts {
	const parts = new Intl.DateTimeFormat('en-US', {
		timeZone,
		year: 'numeric',
		month: '2-digit',
		day: '2-digit',
		hour: '2-digit',
		minute: '2-digit',
		hourCycle: 'h23'
	}).formatToParts(date);
	const get = (type: string) => Number(parts.find((p) => p.type === type)?.value);
	return {
		year: get('year'),
		month: get('month'),
		day: get('day'),
		hour: get('hour'),
		minute: get('minute')
	};
}

/** Offset of `timeZone` from UTC at `date`, in minutes (e.g. +420 for UTC+7). */
export function tzOffsetMinutes(date: Date, timeZone: string): number {
	const p = zonedParts(date, timeZone);
	const asUtc = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute);
	const truncated = Math.floor(date.getTime() / 60_000) * 60_000;
	return Math.round((asUtc - truncated) / 60_000);
}

function pad(n: number): string {
	return String(n).padStart(2, '0');
}

function toIsoWithOffset(utcMs: number, offsetMin: number): string {
	const local = new Date(utcMs + offsetMin * 60_000);
	const sign = offsetMin >= 0 ? '+' : '-';
	const abs = Math.abs(offsetMin);
	return (
		`${local.getUTCFullYear()}-${pad(local.getUTCMonth() + 1)}-${pad(local.getUTCDate())}` +
		`T${pad(local.getUTCHours())}:${pad(local.getUTCMinutes())}:00` +
		`${sign}${pad(Math.floor(abs / 60))}:${pad(abs % 60)}`
	);
}

function minutesOf(hhmm: string): number {
	const [h, m] = hhmm.split(':').map(Number);
	return h * 60 + m;
}

export function pickupSlots(options: {
	now?: Date;
	timeZone: string;
	opening: string;
	closing: string;
	minPrepMinutes: number;
	stepMinutes?: number;
}): PickupSlot[] {
	const now = options.now ?? new Date();
	const step = options.stepMinutes ?? 15;
	const offset = tzOffsetMinutes(now, options.timeZone);
	const today = zonedParts(now, options.timeZone);
	const nowMinutes = today.hour * 60 + today.minute;
	const open = minutesOf(options.opening);
	const close = minutesOf(options.closing);
	// UTC ms of local midnight today.
	const midnightUtc = Date.UTC(today.year, today.month - 1, today.day) - offset * 60_000;

	const slots: PickupSlot[] = [];
	for (const [dayIndex, day] of [
		[0, 'today'],
		[1, 'tomorrow']
	] as const) {
		const earliest = dayIndex === 0 ? nowMinutes + options.minPrepMinutes : 0;
		let start = Math.max(open, Math.ceil(earliest / step) * step);
		for (; start <= close; start += step) {
			const utcMs = midnightUtc + dayIndex * 86_400_000 + start * 60_000;
			slots.push({
				value: toIsoWithOffset(utcMs, offset),
				time: `${pad(Math.floor(start / 60))}:${pad(start % 60)}`,
				day
			});
		}
		// Offer tomorrow only when today is (nearly) over.
		if (dayIndex === 0 && slots.length >= 4) break;
	}
	return slots;
}

/** "13:30" → "1:30 PM" (en) or "13:30" (km). */
export function formatSlotTime(hhmm: string, locale: 'en' | 'km'): string {
	if (locale === 'km') return hhmm;
	const [h, m] = hhmm.split(':').map(Number);
	const suffix = h >= 12 ? 'PM' : 'AM';
	return `${((h + 11) % 12) + 1}:${pad(m)} ${suffix}`;
}
