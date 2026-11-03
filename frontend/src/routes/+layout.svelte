<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { markHydrated } from '#lib/actions/reveal.ts';
	import Toaster from '#lib/components/ui/Toaster.svelte';
	import { i18n } from '#lib/i18n/index.svelte.ts';
	import type { LayoutProps } from './$types';

	let { data, children }: LayoutProps = $props();

	// Set synchronously so the server renders in the visitor's language.
	// svelte-ignore state_referenced_locally
	i18n.locale = data.locale;

	// Every element hydrated so far has already run its reveal action; anything mounted from
	// the next task on (client navigation, late data) is new and should animate in.
	onMount(() => {
		const timer = setTimeout(markHydrated);
		return () => clearTimeout(timer);
	});
</script>

{@render children()}
<Toaster />
