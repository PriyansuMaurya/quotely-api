/**
 * Quote API client.
 *
 * Failures are classified rather than collapsed into one message: a dropped
 * connection, a slow server and a malformed payload need different words in the
 * UI. `fetchImpl` is injectable so tests never touch the network.
 */

import { apiBaseUrl, randomQuotePath } from './config';

export interface Quote {
	text: string;
	author: string;
	quote: string;
}

export type QuoteErrorKind = 'network' | 'timeout' | 'http' | 'payload';

const MESSAGES: Record<QuoteErrorKind, string> = {
	network:
		"We couldn't reach the quotes service. It may be offline, or it may not accept requests from this site.",
	timeout: 'The quotes service took too long to respond. Please try again.',
	http: 'The quotes service returned an error.',
	payload: 'The quotes service sent a response we could not read.'
};

export class QuoteError extends Error {
	readonly kind: QuoteErrorKind;
	readonly status?: number;

	constructor(kind: QuoteErrorKind, options: { status?: number; detail?: string } = {}) {
		const suffix = options.status ? ` (HTTP ${options.status})` : '';
		super(options.detail ?? `${MESSAGES[kind]}${suffix}`);
		this.name = 'QuoteError';
		this.kind = kind;
		this.status = options.status;
	}
}

export function isQuote(value: unknown): value is Quote {
	if (typeof value !== 'object' || value === null) return false;
	const candidate = value as Record<string, unknown>;
	return (
		typeof candidate.text === 'string' &&
		candidate.text.trim().length > 0 &&
		typeof candidate.author === 'string' &&
		candidate.author.trim().length > 0 &&
		typeof candidate.quote === 'string'
	);
}

export interface FetchQuoteOptions {
	baseUrl?: string;
	fetchImpl?: typeof fetch;
	/** Caller cancellation, e.g. component teardown. */
	signal?: AbortSignal;
	timeoutMs?: number;
}

const DEFAULT_TIMEOUT_MS = 12_000;

export async function fetchRandomQuote(options: FetchQuoteOptions = {}): Promise<Quote> {
	const {
		baseUrl = apiBaseUrl,
		fetchImpl = fetch,
		signal,
		timeoutMs = DEFAULT_TIMEOUT_MS
	} = options;

	const controller = new AbortController();
	const abort = () => controller.abort();
	const timer = setTimeout(abort, timeoutMs);
	signal?.addEventListener('abort', abort, { once: true });

	try {
		const response = await fetchImpl(`${baseUrl}${randomQuotePath}`, {
			method: 'GET',
			headers: { Accept: 'application/json' },
			signal: controller.signal
		});

		if (!response.ok) {
			throw new QuoteError('http', { status: response.status });
		}

		let payload: unknown;
		try {
			payload = await response.json();
		} catch {
			throw new QuoteError('payload');
		}

		if (!isQuote(payload)) {
			throw new QuoteError('payload');
		}

		return payload;
	} catch (error) {
		if (error instanceof QuoteError) throw error;
		// A timeout aborts the request, so distinguish it from caller cancellation.
		if (controller.signal.aborted && !signal?.aborted) {
			throw new QuoteError('timeout');
		}
		throw new QuoteError('network');
	} finally {
		clearTimeout(timer);
		signal?.removeEventListener('abort', abort);
	}
}
