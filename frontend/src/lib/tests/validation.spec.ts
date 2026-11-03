import { describe, expect, it } from 'vitest';
import {
	checkoutSchema,
	fieldErrors,
	foodSchema,
	validateImageFile
} from '#lib/utils/validation.ts';

const validCheckout = {
	customer_name: '  Sokha   Chan ',
	customer_phone: '012 345 678',
	student_id: '',
	pickup_time: '2026-11-04T12:00:00+07:00',
	notes: ''
};

describe('checkout validation', () => {
	it('accepts a valid guest checkout and normalizes fields', () => {
		const result = checkoutSchema.safeParse(validCheckout);
		expect(result.success).toBe(true);
		expect(result.data).toMatchObject({
			customer_name: 'Sokha Chan',
			student_id: null,
			notes: null
		});
	});

	it('reports each invalid field with a translatable key', () => {
		const result = checkoutSchema.safeParse({
			...validCheckout,
			customer_name: ' a ',
			customer_phone: '12ab',
			pickup_time: ''
		});
		expect(result.success).toBe(false);
		expect(fieldErrors(result.error!)).toEqual({
			customer_name: 'validation.nameRequired',
			customer_phone: 'validation.phoneInvalid',
			pickup_time: 'validation.pickupRequired'
		});
	});

	it('requires 8–15 digit phone numbers', () => {
		for (const phone of ['1234567', '+855 1234567890123']) {
			expect(checkoutSchema.safeParse({ ...validCheckout, customer_phone: phone }).success).toBe(
				false
			);
		}
		for (const phone of ['012345678', '+855 12 345 678', '(012) 345-678']) {
			expect(checkoutSchema.safeParse({ ...validCheckout, customer_phone: phone }).success).toBe(
				true
			);
		}
	});

	it('limits notes to 300 characters', () => {
		const result = checkoutSchema.safeParse({ ...validCheckout, notes: 'x'.repeat(301) });
		expect(result.success).toBe(false);
	});
});

describe('food form validation', () => {
	const base = {
		name_en: 'Chicken Rice',
		name_km: 'បាយមាន់',
		description_en: '',
		description_km: '',
		category_id: '1',
		price: '1.5',
		stock_quantity: '10',
		image_url: null,
		is_available: true,
		is_featured: false
	};

	it('normalizes price and numbers', () => {
		const result = foodSchema.safeParse(base);
		expect(result.success).toBe(true);
		expect(result.data).toMatchObject({ price: '1.50', category_id: 1, stock_quantity: 10 });
	});

	it('rejects bad prices, stock and missing names', () => {
		const result = foodSchema.safeParse({
			...base,
			price: '1.999',
			stock_quantity: '-1',
			name_km: ' '
		});
		expect(fieldErrors(result.error!)).toMatchObject({
			price: 'validation.priceInvalid',
			stock_quantity: 'validation.stockInvalid',
			name_km: 'validation.required'
		});
	});

	it('validates image uploads', () => {
		expect(validateImageFile(new File(['x'], 'a.gif', { type: 'image/gif' }))).toBe(
			'validation.imageType'
		);
		const big = new File([new Uint8Array(6 * 1024 * 1024)], 'a.png', { type: 'image/png' });
		expect(validateImageFile(big)).toBe('validation.imageSize');
		expect(validateImageFile(new File(['x'], 'a.webp', { type: 'image/webp' }))).toBeNull();
	});
});
