import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [
		tailwindcss(),
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) =>
					filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},

			// Static output: the app is a single prerendered page served from a CDN.
			adapter: adapter()
		})
	],
	// SvelteKit already exposes PUBLIC_* variables; VITE_* is kept for convenience.
	envPrefix: ['PUBLIC_', 'VITE_'],
	resolve: process.env.VITEST ? { conditions: ['browser'] } : undefined,
	test: {
		environment: 'jsdom',
		include: ['src/**/*.test.ts'],
		setupFiles: ['./src/vitest-setup.ts'],
		restoreMocks: true,
		// e2e/ holds Playwright specs, which must not be collected by Vitest.
		exclude: ['e2e/**', 'node_modules/**']
	}
});
