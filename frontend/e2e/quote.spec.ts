import { expect, test } from '@playwright/test';

const API_GLOB = '**/api/v1/quotes/random';

function quoteBody(text: string, author: string) {
	return { text, author, quote: `"${text}" - ${author}` };
}

test('renders a quote and fetches a new one on refresh', async ({ page }) => {
	const responses = [
		quoteBody('The journey of a thousand miles begins with one step.', 'Lao Tzu'),
		quoteBody('Simplicity is the ultimate sophistication.', 'Leonardo da Vinci')
	];
	let calls = 0;

	await page.route(API_GLOB, async (route) => {
		// Anything beyond the second call repeats the last quote.
		const index = Math.min(calls, responses.length - 1);
		calls += 1;
		await route.fulfill({ status: 200, json: responses[index] });
	});

	await page.goto('/');

	await expect(
		page.getByText('The journey of a thousand miles begins with one step.')
	).toBeVisible();
	await expect(page.getByText('Lao Tzu')).toBeVisible();

	await page.getByRole('button', { name: /new quote/i }).click();

	await expect(page.getByText('Simplicity is the ultimate sophistication.')).toBeVisible();
	await expect(page.getByText('Leonardo da Vinci')).toBeVisible();
});

test('announces quotes through a polite live region', async ({ page }) => {
	await page.route(API_GLOB, (route) =>
		route.fulfill({ status: 200, json: quoteBody('A quote about accessibility.', 'An Author') })
	);

	await page.goto('/');

	const liveRegion = page.locator('[aria-live="polite"]');
	await expect(liveRegion).toHaveAttribute('aria-atomic', 'true');
	await expect(liveRegion).toContainText('A quote about accessibility.');
});

test('shows an accessible error when the API fails', async ({ page }) => {
	await page.route(API_GLOB, (route) => route.fulfill({ status: 500, json: { detail: 'boom' } }));

	await page.goto('/');

	const alert = page.getByRole('alert');
	await expect(alert).toBeVisible();
	await expect(alert).toContainText(/returned an error/i);
	await expect(page.getByRole('button', { name: /new quote/i })).toBeEnabled();
});

test('is usable at a mobile viewport without horizontal scrolling', async ({ page }) => {
	await page.setViewportSize({ width: 375, height: 667 });
	await page.route(API_GLOB, (route) =>
		route.fulfill({ status: 200, json: quoteBody('Small screens deserve big type.', 'A Designer') })
	);

	await page.goto('/');
	await expect(page.getByText('Small screens deserve big type.')).toBeVisible();

	const overflow = await page.evaluate(
		() => document.documentElement.scrollWidth - document.documentElement.clientWidth
	);
	expect(overflow).toBeLessThanOrEqual(0);
});
