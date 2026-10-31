/**
 * Runtime configuration.
 *
 * The API base URL is read at build time so the same code works locally and on a
 * static host with no server to inject configuration. A default is supplied
 * because a missing variable should not break the build — the deployed API is the
 * sensible fallback for this app.
 */

const DEFAULT_API_BASE_URL = 'https://quotely-api-mvyq.onrender.com';

function normalise(url: string): string {
	return url.trim().replace(/\/+$/, '');
}

export const apiBaseUrl = normalise(
	(import.meta.env.PUBLIC_API_BASE_URL as string | undefined) ?? DEFAULT_API_BASE_URL
);

export const randomQuotePath = '/api/v1/quotes/random';
