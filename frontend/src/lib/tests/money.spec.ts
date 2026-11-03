import { describe, expect, it } from 'vitest';
import {
	centsToString,
	formatCents,
	formatMoney,
	normalizePrice,
	toCents
} from '#lib/utils/money.ts';

describe('money', () => {
	it('parses decimal strings into exact integer cents', () => {
		expect(toCents('1.50')).toBe(150);
		expect(toCents('0.75')).toBe(75);
		expect(toCents('2')).toBe(200);
		expect(toCents('1.5')).toBe(150);
		expect(toCents('0.05')).toBe(5);
		expect(() => toCents('1.505')).toThrow();
		expect(() => toCents('abc')).toThrow();
	});

	it('never suffers floating point drift', () => {
		// 0.1 + 0.2 !== 0.3 in floating point; cents arithmetic is exact.
		expect(centsToString(toCents('0.10') + toCents('0.20'))).toBe('0.30');
		const total = Array.from({ length: 100 }, () => toCents('0.07')).reduce((a, b) => a + b, 0);
		expect(centsToString(total)).toBe('7.00');
	});

	it('formats for display', () => {
		expect(formatCents(375)).toBe('$3.75');
		expect(formatCents(5)).toBe('$0.05');
		expect(formatCents(-150)).toBe('-$1.50');
		expect(formatMoney('12.5')).toBe('$12.50');
		expect(formatCents(125375)).toBe('$1,253.75');
		expect(formatCents(-123456789)).toBe('-$1,234,567.89');
	});

	it('normalizes admin price input', () => {
		expect(normalizePrice('1.5')).toBe('1.50');
		expect(normalizePrice(' $2 ')).toBe('2.00');
		expect(normalizePrice('0')).toBeNull();
		expect(normalizePrice('-1')).toBeNull();
		expect(normalizePrice('1.234')).toBeNull();
		expect(normalizePrice('12345')).toBeNull();
	});
});
