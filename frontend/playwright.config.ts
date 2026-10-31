import { defineConfig, devices } from '@playwright/test';

const PORT = 4173;
const BASE_URL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
	testDir: './e2e',
	fullyParallel: true,
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 2 : 0,
	reporter: 'list',
	use: {
		baseURL: BASE_URL,
		trace: 'on-first-retry'
	},
	projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
	webServer: {
		// Test the real production build, not the dev server. The host is pinned to
		// 127.0.0.1 because preview otherwise binds only to localhost, which resolves
		// to ::1 on some platforms while Playwright polls IPv4.
		command: `npm run build && npm run preview -- --port ${PORT} --strictPort --host 127.0.0.1`,
		url: BASE_URL,
		reuseExistingServer: !process.env.CI,
		timeout: 180_000
	}
});
