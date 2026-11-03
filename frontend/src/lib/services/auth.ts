import { browser } from '$app/env';
import { api, ApiError, readCookie, type Fetch } from './api';
import type { Session, User } from '#lib/types/api.ts';

export const login = (email: string, password: string, requireStaff = false) =>
	api<Session>('/auth/login', {
		method: 'POST',
		body: { email, password, require_staff: requireStaff }
	});

export const register = (body: { name: string; email: string; phone?: string; password: string }) =>
	api<Session>('/auth/register', { method: 'POST', body });

export const logout = () => api<{ message: string }>('/auth/logout', { method: 'POST' });

/** The logged-in user, or null when there is no valid session. */
export async function currentUser(fetch?: Fetch): Promise<User | null> {
	// The readable CSRF cookie is set together with the session: without it there is no
	// session, so skip the request (and the 401 it would log in the browser console).
	if (browser && !readCookie('ce_csrf')) return null;
	try {
		return await api<User>('/auth/me', { fetch });
	} catch (err) {
		if (err instanceof ApiError && err.status === 401) return null;
		throw err;
	}
}
