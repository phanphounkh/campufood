// See https://svelte.dev/docs/kit/types#app.d.ts
import type { Locale } from '#lib/i18n/locales.ts';

declare global {
	namespace App {
		interface Error {
			code?: string;
		}
		interface Locals {
			locale: Locale;
		}
	}
}

export {};
