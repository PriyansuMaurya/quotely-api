<script lang="ts">
	import { onMount } from 'svelte';
	import LoadingSkeleton from '#lib/components/LoadingSkeleton.svelte';
	import QuoteCard from '#lib/components/QuoteCard.svelte';
	import RefreshButton from '#lib/components/RefreshButton.svelte';
	import { fetchRandomQuote, QuoteError, type Quote } from '#lib/quotes';

	type Status = 'idle' | 'loading' | 'success' | 'error';

	let status = $state<Status>('idle');
	let quote = $state<Quote | null>(null);
	let errorMessage = $state<string | null>(null);
	// Incremented on every success so the card remounts and replays its entrance.
	let version = $state(0);

	let controller: AbortController | null = null;

	const isLoading = $derived(status === 'loading');
	const isEmpty = $derived(status === 'idle' && quote === null);

	async function loadQuote(): Promise<void> {
		// Supersede any in-flight request so a fast double-click cannot let an older
		// response overwrite a newer one.
		controller?.abort();
		const current = new AbortController();
		controller = current;

		status = 'loading';
		errorMessage = null;

		try {
			const next = await fetchRandomQuote({ signal: current.signal });
			if (current.signal.aborted) return;
			quote = next;
			version += 1;
			status = 'success';
		} catch (error) {
			if (current.signal.aborted) return;
			quote = null;
			errorMessage =
				error instanceof QuoteError
					? error.message
					: 'Something went wrong while loading a quote. Please try again.';
			status = 'error';
		}
	}

	onMount(() => {
		loadQuote();
		return () => controller?.abort();
	});
</script>

<svelte:head>
	<title>Quotely — a random quote, on demand</title>
	<meta
		name="description"
		content="A minimal client for the Quotely API. Get an inspiring quote and its author with a single click."
	/>
</svelte:head>

<main
	class="relative flex min-h-dvh flex-col items-center justify-center overflow-hidden px-4 py-10
	       sm:px-6 sm:py-16"
>
	<!-- Decorative background: purely visual, hidden from assistive technology. -->
	<div aria-hidden="true" class="pointer-events-none absolute inset-0 -z-10">
		<div
			class="absolute -top-32 left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-indigo-600/25
			       blur-3xl sm:h-96 sm:w-96"
		></div>
		<div
			class="absolute -right-20 bottom-0 h-64 w-64 rounded-full bg-fuchsia-600/20 blur-3xl
			       sm:h-80 sm:w-80"
		></div>
	</div>

	<div class="w-full max-w-2xl">
		<header class="mb-8 text-center sm:mb-12">
			<p class="text-xs font-semibold tracking-[0.28em] text-indigo-300/80 uppercase">Quotely</p>
			<h1 class="mt-3 font-display text-3xl tracking-tight text-slate-50 sm:text-4xl">
				A thought for right now
			</h1>
		</header>

		<section
			class="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/40
			       backdrop-blur-xl sm:p-10"
			aria-labelledby="quote-heading"
		>
			<h2 id="quote-heading" class="sr-only">Random quote</h2>

			<!-- Polite live region: a new quote is announced, not interrupted. -->
			<div aria-live="polite" aria-atomic="true" aria-busy={isLoading}>
				{#if isLoading}
					<LoadingSkeleton />
					<p class="sr-only">Loading a new quote…</p>
				{:else if status === 'error'}
					<div class="py-2" role="alert">
						<p class="text-base text-rose-200 sm:text-lg">{errorMessage}</p>
						<p class="mt-2 text-sm text-slate-400">
							This usually clears up on a second attempt.
						</p>
					</div>
				{:else if quote}
					{#key version}
						<div class="animate-[quote-in_420ms_ease-out]">
							<QuoteCard {quote} />
						</div>
					{/key}
				{:else if isEmpty}
					<p class="text-base text-slate-400">
						Press “New quote” to fetch something worth reading.
					</p>
				{/if}
			</div>

			<div class="mt-8 flex flex-wrap items-center gap-3 sm:mt-10">
				<RefreshButton {isLoading} onRefresh={loadQuote} />
			</div>
		</section>

		<footer class="mt-8 text-center text-xs text-slate-500 sm:mt-10">
			Quotes from the
			<a
				class="rounded underline decoration-slate-600 underline-offset-4 transition-colors
				       hover:text-slate-300 focus-visible:ring-2 focus-visible:ring-indigo-300
				       focus-visible:outline-none"
				href="https://quotely-api-mvyq.onrender.com/docs"
				rel="noreferrer"
				target="_blank"
			>
				Quotely API
			</a>
			· served as static HTML
		</footer>
	</div>
</main>

<style>
	@keyframes quote-in {
		from {
			opacity: 0;
			transform: translateY(8px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
