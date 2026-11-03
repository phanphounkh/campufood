<script lang="ts">
	import '../app.css';
	import Toaster from '#lib/components/ui/Toaster.svelte';
	import { i18n } from '#lib/i18n/index.svelte.ts';
	import type { LayoutProps } from './$types';

	let { data, children }: LayoutProps = $props();

	// Set synchronously so the server renders in the visitor's language.
	// svelte-ignore state_referenced_locally
	i18n.locale = data.locale;
</script>

{@render children()}
<Toaster />
