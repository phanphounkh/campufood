import { describe, expect, it } from 'vitest';
import { formatSlotTime, pickupSlots, tzOffsetMinutes } from '#lib/utils/pickup.ts';

const base = {
	timeZone: 'Asia/Phnom_Penh',
	opening: '07:00',
	closing: '17:00',
	minPrepMinutes: 15
};

describe('pickup slots', () => {
	it('uses the canteen time zone regardless of the device', () => {
		expect(tzOffsetMinutes(new Date('2026-11-03T05:00:00Z'), 'Asia/Phnom_Penh')).toBe(420);
	});

	it('starts after the preparation time, in 15-minute steps', () => {
		// 10:07 in Phnom Penh (03:07 UTC) → first slot 10:30 (10:22 rounded up).
		const slots = pickupSlots({ ...base, now: new Date('2026-11-03T03:07:00Z') });
		expect(slots[0]).toEqual({ value: '2026-11-03T10:30:00+07:00', time: '10:30', day: 'today' });
		expect(slots.at(-1)?.time).toBe('17:00');
		expect(slots.every((s) => s.day === 'today')).toBe(true);
	});

	it('offers tomorrow when the canteen is (nearly) closed', () => {
		// 16:50 local → no slot left today.
		const slots = pickupSlots({ ...base, now: new Date('2026-11-03T09:50:00Z') });
		expect(slots[0]).toEqual({
			value: '2026-11-04T07:00:00+07:00',
			time: '07:00',
			day: 'tomorrow'
		});
	});

	it('handles times before opening and the date change at midnight', () => {
		// 23:30 UTC on Nov 2 = 06:30 on Nov 3 in Phnom Penh.
		const slots = pickupSlots({ ...base, now: new Date('2026-11-02T23:30:00Z') });
		expect(slots[0].value).toBe('2026-11-03T07:00:00+07:00');
	});

	it('formats slot times per locale', () => {
		expect(formatSlotTime('13:30', 'en')).toBe('1:30 PM');
		expect(formatSlotTime('00:15', 'en')).toBe('12:15 AM');
		expect(formatSlotTime('13:30', 'km')).toBe('13:30');
	});
});
