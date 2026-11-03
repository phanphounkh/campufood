import { browser } from '$app/env';
import { en, type MessageKey } from './en';
import { km } from './km';
import { adminEn, type AdminKey } from './admin.en';
import { adminKm } from './admin.km';
import { LOCALE_COOKIE, type Locale } from './locales';

export type { Locale } from './locales';
export type TranslationKey = MessageKey | AdminKey;
type Params = Record<string, string | number>;

const dictionaries: Record<Locale, Record<TranslationKey, string>> = {
	en: { ...en, ...adminEn },
	km: { ...km, ...adminKm }
};

/**
 * Reactive locale. The root layout sets it from the `ce_locale` cookie on every render
 * (server and client), so SSR output matches the visitor's language.
 */
class I18n {
	locale = $state<Locale>('en');

	/** Translate a key. Dynamic keys (e.g. `status.${s}`) fall back to English, then the key. */
	t = (key: TranslationKey | (string & {}), params?: Params): string => {
		const dict = dictionaries[this.locale] as Record<string, string>;
		let text = dict[key] ?? (dictionaries.en as Record<string, string>)[key] ?? key;
		if (params) {
			for (const [name, value] of Object.entries(params)) {
				text = text.replaceAll(`{${name}}`, String(value));
			}
		}
		return text;
	};

	setLocale(locale: Locale): void {
		this.locale = locale;
		if (browser) {
			document.cookie = `${LOCALE_COOKIE}=${locale}; path=/; max-age=31536000; samesite=lax`;
			document.documentElement.lang = locale;
		}
	}

	/** Pick `name_km` / `name_en` (etc.) for the current locale, falling back to English. */
	pick = <T extends object>(obj: T, field: string): string => {
		const record = obj as Record<string, unknown>;
		const value = record[`${field}_${this.locale}`];
		return (typeof value === 'string' && value) || String(record[`${field}_en`] ?? '');
	};

	/** The same field in the *other* language (shown as a secondary line). */
	pickOther = <T extends object>(obj: T, field: string): string => {
		const other = this.locale === 'en' ? 'km' : 'en';
		return String((obj as Record<string, unknown>)[`${field}_${other}`] ?? '');
	};
}

export const i18n = new I18n();
export const t = i18n.t;
