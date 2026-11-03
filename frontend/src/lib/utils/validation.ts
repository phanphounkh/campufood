/**
 * Client-side validation (Zod). Messages are i18n keys, translated where they are shown.
 * The API validates everything again; this is for fast, friendly feedback.
 */
import { z } from 'zod';
import { normalizePrice } from './money';

const trimmed = (min: number, max: number, minKey: string, maxKey = 'validation.tooLong') =>
	z
		.string()
		.transform((v) => v.replace(/\s+/g, ' ').trim())
		.pipe(z.string().min(min, { message: minKey }).max(max, { message: maxKey }));

const optionalText = (max: number) =>
	z
		.string()
		.max(max, { message: 'validation.tooLong' })
		.transform((v) => v.trim() || null)
		.nullable()
		.optional();

export const phoneSchema = z
	.string()
	.trim()
	.regex(/^\+?[\d\s\-().]+$/, { message: 'validation.phoneInvalid' })
	.refine(
		(v) => {
			const digits = v.replace(/\D/g, '').length;
			return digits >= 8 && digits <= 15;
		},
		{ message: 'validation.phoneInvalid' }
	);

export const checkoutSchema = z.object({
	customer_name: trimmed(2, 80, 'validation.nameRequired'),
	customer_phone: phoneSchema,
	student_id: optionalText(40),
	pickup_time: z.string().min(1, { message: 'validation.pickupRequired' }),
	notes: optionalText(300)
});
export type CheckoutForm = z.input<typeof checkoutSchema>;

export const loginSchema = z.object({
	email: z.string().trim().min(3, { message: 'validation.emailInvalid' }).includes('@', {
		message: 'validation.emailInvalid'
	}),
	password: z.string().min(1, { message: 'validation.passwordRequired' })
});

export const registerSchema = z.object({
	name: trimmed(2, 80, 'validation.nameRequired'),
	email: z.email({ message: 'validation.emailInvalid' }),
	phone: z.union([z.literal(''), phoneSchema]).optional(),
	password: z.string().min(8, { message: 'validation.passwordShort' }).max(128)
});

const price = z.string().transform((v, ctx) => {
	const normalized = normalizePrice(v);
	if (!normalized) {
		ctx.addIssue({ code: 'custom', message: 'validation.priceInvalid' });
		return z.NEVER;
	}
	return normalized;
});

export const foodSchema = z.object({
	name_en: trimmed(1, 120, 'validation.required'),
	name_km: trimmed(1, 120, 'validation.required'),
	description_en: z
		.string()
		.max(500, { message: 'validation.tooLong' })
		.transform((v) => v.trim()),
	description_km: z
		.string()
		.max(500, { message: 'validation.tooLong' })
		.transform((v) => v.trim()),
	category_id: z.coerce.number().int().positive({ message: 'validation.categoryRequired' }),
	price,
	stock_quantity: z.coerce
		.number({ message: 'validation.stockInvalid' })
		.int({ message: 'validation.stockInvalid' })
		.min(0, { message: 'validation.stockInvalid' })
		.max(100000, { message: 'validation.stockInvalid' }),
	image_url: z.string().nullable(),
	is_available: z.boolean(),
	is_featured: z.boolean()
});
export type FoodFormInput = z.input<typeof foodSchema>;

export const categorySchema = z.object({
	name_en: trimmed(1, 80, 'validation.required'),
	name_km: trimmed(1, 80, 'validation.required'),
	slug: z
		.string()
		.trim()
		.regex(/^([a-z0-9]+(?:-[a-z0-9]+)*)?$/, { message: 'validation.slugInvalid' })
		.optional(),
	sort_order: z.coerce.number().int().min(0).max(1000)
});

/** Map a Zod error to `{ field: i18nKey }` (first issue per field). */
export function fieldErrors(error: z.ZodError): Record<string, string> {
	const out: Record<string, string> = {};
	for (const issue of error.issues) {
		const key = String(issue.path[0] ?? '_');
		if (!out[key]) out[key] = issue.message;
	}
	return out;
}

export const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

export function validateImageFile(file: File): string | null {
	if (!IMAGE_TYPES.includes(file.type)) return 'validation.imageType';
	if (file.size > MAX_IMAGE_BYTES) return 'validation.imageSize';
	return null;
}
