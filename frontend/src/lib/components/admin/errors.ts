import { goto } from '$app/navigation';
import { resolve } from '$app/paths';
import { ApiError } from '#lib/services/api.ts';
import { toast } from '#lib/stores/toast.svelte.ts';
import { t } from '#lib/i18n/index.svelte.ts';

/** A user-facing message for any error thrown by the API client. */
export function errorMessage(err: unknown): string {
	if (err instanceof ApiError) {
		if (err.status === 401) return t('admin.sessionExpired');
		return err.message;
	}
	return t('admin.loadError');
}

/** Toast the error; on an expired session, go back to the login page. */
export function reportError(err: unknown): void {
	toast.error(errorMessage(err));
	if (err instanceof ApiError && err.status === 401) {
		const next = encodeURIComponent(location.pathname + location.search);
		goto(resolve(`/admin/login?next=${next}`));
	}
}

/** Load-function helper: never throw, return the message for an inline error state. */
export async function attempt<T>(
	fn: () => Promise<T>
): Promise<{ ok: true; value: T } | { ok: false; error: string }> {
	try {
		return { ok: true, value: await fn() };
	} catch (err) {
		return { ok: false, error: errorMessage(err) };
	}
}
