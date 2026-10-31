<script lang="ts">
	let {
		isLoading,
		onRefresh
	}: {
		isLoading: boolean;
		onRefresh: () => void;
	} = $props();
</script>

<button
	type="button"
	onclick={onRefresh}
	disabled={isLoading}
	aria-busy={isLoading}
	class="group inline-flex items-center gap-2.5 rounded-full bg-gradient-to-r from-indigo-500
	       to-fuchsia-500 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-950/40
	       transition-transform duration-200 ease-out hover:scale-[1.02] active:scale-[0.99]
	       focus-visible:ring-2 focus-visible:ring-indigo-300 focus-visible:ring-offset-2
	       focus-visible:ring-offset-slate-950 focus-visible:outline-none
	       disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:scale-100"
>
	<svg
		class="h-4 w-4 transition-transform duration-500 ease-out {isLoading
			? 'animate-spin'
			: 'group-hover:rotate-180'}"
		viewBox="0 0 24 24"
		fill="none"
		stroke="currentColor"
		stroke-width="2.2"
		stroke-linecap="round"
		stroke-linejoin="round"
		aria-hidden="true"
	>
		<path d="M21 12a9 9 0 1 1-2.64-6.36" />
		<path d="M21 3v6h-6" />
	</svg>
	<span>{isLoading ? 'Fetching…' : 'New quote'}</span>
</button>
