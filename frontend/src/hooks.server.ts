import type { Handle } from '@sveltejs/kit/hooks';
import { API_INTERNAL_URL } from '$app/env/private';
import { isLocale, LOCALE_COOKIE, type Locale } from '#lib/i18n/locales.ts';

/**
 * The browser only ever talks to this origin. Requests to /api and /media are forwarded to
 * the FastAPI backend, so the session cookie stays first-party and no CORS is needed.
 */
const API_URL = API_INTERNAL_URL;
const PROXIED = /^\/(api|media)\//;

// Hop-by-hop headers must not be forwarded by a proxy.
const HOP_BY_HOP = [
	'connection',
	'keep-alive',
	'proxy-authenticate',
	'proxy-authorization',
	'te',
	'trailer',
	'transfer-encoding',
	'upgrade',
	'host',
	'content-length'
];

async function proxy(event: Parameters<Handle>[0]['event']): Promise<Response> {
	const { request, url } = event;
	const headers = new Headers(request.headers);
	for (const name of HOP_BY_HOP) headers.delete(name);
	// Overwrite (never append to) any client-supplied value so it cannot be spoofed.
	headers.set('x-forwarded-for', event.getClientAddress());
	headers.set('x-forwarded-proto', url.protocol.replace(':', ''));
	headers.set('x-forwarded-host', url.host);
	// Ask for an uncompressed body: Node's fetch decodes it anyway.
	headers.delete('accept-encoding');

	const hasBody = !['GET', 'HEAD'].includes(request.method);
	let upstream: Response;
	try {
		upstream = await fetch(`${API_URL}${url.pathname}${url.search}`, {
			method: request.method,
			headers,
			body: hasBody ? await request.arrayBuffer() : undefined,
			redirect: 'manual'
		});
	} catch {
		return new Response(
			JSON.stringify({
				error: {
					code: 'API_UNAVAILABLE',
					message: 'The CampusEats server is not reachable. Please try again shortly.',
					details: null
				}
			}),
			{ status: 503, headers: { 'content-type': 'application/json' } }
		);
	}

	const responseHeaders = new Headers(upstream.headers);
	responseHeaders.delete('content-encoding');
	responseHeaders.delete('content-length');
	responseHeaders.delete('transfer-encoding');
	return new Response(upstream.body, {
		status: upstream.status,
		statusText: upstream.statusText,
		headers: responseHeaders
	});
}

function detectLocale(cookie: string | undefined, acceptLanguage: string | null): Locale {
	if (isLocale(cookie)) return cookie;
	return acceptLanguage?.toLowerCase().startsWith('km') ? 'km' : 'en';
}

export const handle: Handle = async ({ event, resolve }) => {
	if (PROXIED.test(event.url.pathname)) {
		return proxy(event);
	}

	const locale = detectLocale(
		event.cookies.get(LOCALE_COOKIE),
		event.request.headers.get('accept-language')
	);
	event.locals.locale = locale;

	const response = await resolve(event, {
		transformPageChunk: ({ html }) => html.replace('%lang%', locale),
		// Universal loads read the content type of API responses.
		filterSerializedResponseHeaders: (name) => name === 'content-type'
	});
	response.headers.set('X-Content-Type-Options', 'nosniff');
	response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
	response.headers.set('X-Frame-Options', 'DENY');
	response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
	return response;
};
