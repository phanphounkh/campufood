import { defineEnvVars } from '@sveltejs/kit/env';

/** Server-side configuration (read from the environment / repo-level .env at startup). */
export const variables = defineEnvVars({
	API_INTERNAL_URL: {
		description: 'Base URL of the FastAPI backend that /api and /media are proxied to.',
		schema: (value) => (value || 'http://127.0.0.1:8000').replace(/\/$/, '')
	}
});
