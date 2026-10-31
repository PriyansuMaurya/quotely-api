import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import { afterEach, describe, expect, it, vi } from 'vitest';
import Page from './+page.svelte';

function quoteResponse(text: string, author: string, status = 200): Response {
	return new Response(JSON.stringify({ text, author, quote: `"${text}" - ${author}` }), {
		status,
		headers: { 'Content-Type': 'application/json' }
	});
}

function stubFetch(impl: () => Promise<Response>) {
	const mock = vi.fn(impl);
	vi.stubGlobal('fetch', mock);
	return mock;
}

afterEach(() => {
	// Vitest globals are off, so testing-library cannot register its own cleanup.
	cleanup();
	vi.unstubAllGlobals();
});

describe('quote page', () => {
	it('shows a loading state before the quote arrives', async () => {
		stubFetch(() => new Promise(() => {}));

		render(Page);

		expect(await screen.findByText(/loading a new quote/i)).toBeInTheDocument();
		expect(screen.getByRole('button', { name: /fetching/i })).toBeDisabled();
	});

	it('renders the quote and author once loaded', async () => {
		stubFetch(async () => quoteResponse('Stay hungry, stay foolish.', 'Steve Jobs'));

		render(Page);

		expect(await screen.findByText('Stay hungry, stay foolish.')).toBeInTheDocument();
		expect(screen.getByText('Steve Jobs')).toBeInTheDocument();
	});

	it('exposes a polite live region for assistive technology', async () => {
		stubFetch(async () => quoteResponse('A quote.', 'An Author'));

		const { container } = render(Page);
		await screen.findByText('A quote.');

		const liveRegion = container.querySelector('[aria-live="polite"]');
		expect(liveRegion).not.toBeNull();
		expect(liveRegion).toHaveAttribute('aria-atomic', 'true');
	});

	it('shows an accessible error and offers a retry when the API fails', async () => {
		stubFetch(async () => quoteResponse('x', 'y', 500));

		render(Page);

		const alert = await screen.findByRole('alert');
		expect(alert).toHaveTextContent(/returned an error/i);
		expect(screen.getByRole('button', { name: /new quote/i })).toBeEnabled();
	});

	it('recovers from an error when retried', async () => {
		let attempt = 0;
		stubFetch(async () => {
			attempt += 1;
			return attempt === 1
				? quoteResponse('x', 'y', 503)
				: quoteResponse('Second time lucky.', 'An Author');
		});

		render(Page);
		await screen.findByRole('alert');

		await fireEvent.click(screen.getByRole('button', { name: /new quote/i }));

		expect(await screen.findByText('Second time lucky.')).toBeInTheDocument();
		expect(screen.queryByRole('alert')).not.toBeInTheDocument();
	});

	it('fetches a different quote on refresh', async () => {
		let attempt = 0;
		const mock = stubFetch(async () => {
			attempt += 1;
			return quoteResponse(`Quote ${attempt}`, `Author ${attempt}`);
		});

		render(Page);
		await screen.findByText('Quote 1');

		await fireEvent.click(screen.getByRole('button', { name: /new quote/i }));

		await waitFor(() => expect(screen.getByText('Quote 2')).toBeInTheDocument());
		expect(mock).toHaveBeenCalledTimes(2);
	});
});
