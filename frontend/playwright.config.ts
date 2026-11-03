import { readFileSync } from 'node:fs';
import { defineConfig, devices } from '@playwright/test';

/**
 * End-to-end tests run the production build (`vite preview`) against the real FastAPI
 * backend and PostgreSQL. Start them first:  docker compose up -d db  +  the API on :8000.
 */

// Load the repo-level .env so tests can log in as the seeded admin.
try {
	for (const line of readFileSync(new URL('../.env', import.meta.url), 'utf8').split('\n')) {
		const match = /^([A-Z0-9_]+)=(.*)$/.exec(line.trim());
		if (match && process.env[match[1]] === undefined) process.env[match[1]] = match[2];
	}
} catch {
	/* no .env: rely on the environment */
}

const PORT = 4173;

export default defineConfig({
	testDir: 'e2e',
	testMatch: '**/*.e2e.ts',
	fullyParallel: false,
	workers: 1,
	retries: process.env.CI ? 1 : 0,
	timeout: 60_000,
	reporter: [['list']],
	use: {
		baseURL: `http://localhost:${PORT}`,
		trace: 'retain-on-failure',
		screenshot: 'only-on-failure'
	},
	projects: [
		{
			name: 'desktop',
			use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
			testIgnore: '**/mobile.e2e.ts'
		},
		{ name: 'mobile', use: { ...devices['Pixel 7'] }, testMatch: '**/mobile.e2e.ts' }
	],
	webServer: {
		command: 'npm run build && npm run preview',
		port: PORT,
		reuseExistingServer: !process.env.CI,
		timeout: 180_000
	}
});
