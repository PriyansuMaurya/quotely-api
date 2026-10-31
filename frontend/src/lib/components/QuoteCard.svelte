<script lang="ts">
	import type { Quote } from '#lib/quotes';

	let { quote }: { quote: Quote } = $props();
</script>

<figure class="relative">
	<span
		aria-hidden="true"
		class="pointer-events-none absolute -top-8 -left-2 font-display text-7xl leading-none
		       text-indigo-400/25 select-none sm:-top-10 sm:-left-3 sm:text-8xl"
	>
		&ldquo;
	</span>

	<blockquote
		class="font-display text-2xl leading-snug tracking-tight text-balance text-slate-50
		       sm:text-3xl md:text-4xl"
	>
		{quote.text}
	</blockquote>

	<figcaption class="mt-6 flex items-center gap-3 sm:mt-8">
		<span aria-hidden="true" class="h-px w-8 bg-gradient-to-r from-indigo-400 to-fuchsia-400"></span>
		<span class="text-sm font-medium tracking-[0.12em] text-slate-400 uppercase sm:text-base">
			{quote.author}
		</span>
	</figcaption>
</figure>
