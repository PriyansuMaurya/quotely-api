import { describe, expect, it, vi } from 'vitest';
import { fetchRandomQuote, isQuote, QuoteError } from './quotes';

const VALID = {
	text: 'It always seems impossible until it is done.',
	author: 'Nelson Mandela',
	quote: '"It always seems impossible until it is done." - Nelson Mandela'
};

function jsonResponse(body: unknown, status = 200): Response {
	return new Response(JSON.stringify(body), {
		status,
		headers: { 'Content-Type': 'application/json' }
	});
}

describe('isQuote', () => {
	it('accepts a complete quote', () => {
		expect(isQuote(VALID)).toBe(true);
	});

	it.each([
		['null', null],
		['a string', 'nope'],
		['missing author', { text: 'x', quote: 'x' }],
		['empty text', { text: '   ', author: 'A', quote: 'x' }],
		['non-string author', { text: 'x', author: 42, quote: 'x' }]
	])('rejects %s', (_label, value) => {
		expect(isQuote(value)).toBe(false);
	});
});

describe('fetchRandomQuote', () => {
	it('returns the parsed quote', async () => {
		const fetchImpl = vi.fn(async () => jsonResponse(VALID));

		const quote = await fetchRandomQuote({
			baseUrl: 'https://api.test',
			fetchImpl: fetchImpl as unknown as typeof fetch
		});

		expect(quote).toEqual(VALID);
		expect(fetchImpl).toHaveBeenCalledWith(
			'https://api.test/api/v1/quotes/random',
			expect.objectContaining({ method: 'GET' })
		);
	});

	it('throws an http error carrying the status', async () => {
		const fetchImpl = vi.fn(async () => jsonResponse({ detail: 'boom' }, 500));

		await expect(
			fetchRandomQuote({ fetchImpl: fetchImpl as unknown as typeof fetch })
		).rejects.toMatchObject({ kind: 'http', status: 500 });
	});

	it('throws a payload error for an unexpected shape', async () => {
		const fetchImpl = vi.fn(async () => jsonResponse({ text: 'only text' }));

		await expect(
			fetchRandomQuote({ fetchImpl: fetchImpl as unknown as typeof fetch })
		).rejects.toBeInstanceOf(QuoteError);
	});

	it('throws a payload error when the body is not JSON', async () => {
		const fetchImpl = vi.fn(async () => new Response('<html>nope</html>', { status: 200 }));

		await expect(
			fetchRandomQuote({ fetchImpl: fetchImpl as unknown as typeof fetch })
		).rejects.toMatchObject({ kind: 'payload' });
	});

	it('throws a network error when the request fails', async () => {
		const fetchImpl = vi.fn(async () => {
			throw new TypeError('Failed to fetch');
		});

		await expect(
			fetchRandomQuote({ fetchImpl: fetchImpl as unknown as typeof fetch })
		).rejects.toMatchObject({ kind: 'network' });
	});

	it('classifies a slow request as a timeout', async () => {
		vi.useFakeTimers();
		const fetchImpl = vi.fn(
			(_url: RequestInfo | URL, init?: RequestInit) =>
				new Promise<Response>((_resolve, reject) => {
					init?.signal?.addEventListener('abort', () =>
						reject(new DOMException('Aborted', 'AbortError'))
					);
				})
		);

		const pending = fetchRandomQuote({
			fetchImpl: fetchImpl as unknown as typeof fetch,
			timeoutMs: 50
		});
		const assertion = expect(pending).rejects.toMatchObject({ kind: 'timeout' });

		await vi.advanceTimersByTimeAsync(100);
		await assertion;
		vi.useRealTimers();
	});
});
