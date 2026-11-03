import { browser } from '$app/env';
import type { ApiErrorBody } from '#lib/types/api.ts';

export const API_BASE = '/api/v1';
const CSRF_COOKIE = 'ce_csrf';
const UNSAFE = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

export type Fetch = typeof fetch;
type Query = Record<string, string | number | boolean | null | undefined | (string | number)[]>;

export class ApiError extends Error {
	constructor(
		public status: number,
		public code: string,
		message: string,
		public details: unknown = null
	) {
		super(message);
		this.name = 'ApiError';
	}

	/** Field-level messages from a 422 response, keyed by field name. */
	get fieldErrors(): Record<string, string> {
		if (!Array.isArray(this.details)) return {};
		const out: Record<string, string> = {};
		for (const d of this.details as { field?: string; message?: string }[]) {
			if (d.field && d.message && !out[d.field]) out[d.field] = d.message;
		}
		return out;
	}
}

export function readCookie(name: string): string | null {
	if (!browser) return null;
	const match = document.cookie.split('; ').find((c) => c.startsWith(`${name}=`));
	return match ? decodeURIComponent(match.slice(name.length + 1)) : null;
}

export function buildQuery(query?: Query): string {
	if (!query) return '';
	const params = new URLSearchParams();
	for (const [key, value] of Object.entries(query)) {
		if (value === undefined || value === null || value === '') continue;
		if (Array.isArray(value)) value.forEach((v) => params.append(key, String(v)));
		else params.set(key, String(value));
	}
	const qs = params.toString();
	return qs ? `?${qs}` : '';
}

export interface RequestOptions {
	method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
	body?: unknown;
	query?: Query;
	/** Use SvelteKit's `fetch` inside load functions. */
	fetch?: Fetch;
	/** Guest order access token (X-Order-Token). */
	orderToken?: string | null;
	headers?: Record<string, string>;
	signal?: AbortSignal;
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
	const method = options.method ?? 'GET';
	const headers: Record<string, string> = { Accept: 'application/json', ...options.headers };
	let body: BodyInit | undefined;

	if (options.body instanceof FormData) {
		body = options.body;
	} else if (options.body !== undefined) {
		headers['Content-Type'] = 'application/json';
		body = JSON.stringify(options.body);
	}
	if (UNSAFE.has(method)) {
		const csrf = readCookie(CSRF_COOKIE);
		if (csrf) headers['X-CSRF-Token'] = csrf;
	}
	if (options.orderToken) headers['X-Order-Token'] = options.orderToken;

	const doFetch = options.fetch ?? fetch;
	let response: Response;
	try {
		response = await doFetch(`${API_BASE}${path}${buildQuery(options.query)}`, {
			method,
			headers,
			body,
			credentials: 'same-origin',
			signal: options.signal
		});
	} catch (err) {
		if ((err as Error)?.name === 'AbortError') throw err;
		throw new ApiError(0, 'NETWORK_ERROR', 'Network error. Check your connection and try again.');
	}

	if (response.status === 204) return undefined as T;
	const isJson = response.headers.get('content-type')?.includes('application/json');
	const data = isJson ? await response.json().catch(() => null) : null;

	if (!response.ok) {
		const err = (data as ApiErrorBody | null)?.error;
		throw new ApiError(
			response.status,
			err?.code ?? 'HTTP_ERROR',
			err?.message ?? `Request failed (${response.status})`,
			err?.details ?? null
		);
	}
	return data as T;
}
