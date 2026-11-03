<script lang="ts">
	import { onMount } from 'svelte';
	import SiteHeader from '#lib/components/layout/SiteHeader.svelte';
	import SiteFooter from '#lib/components/layout/SiteFooter.svelte';
	import CartDrawer from '#lib/components/cart/CartDrawer.svelte';
	import DragGhost from '#lib/components/cart/DragGhost.svelte';
	import { cart } from '#lib/stores/cart.svelte.ts';
	import type { LayoutProps } from './$types';

	let { data, children }: LayoutProps = $props();

	onMount(() => cart.load());
</script>

<a
	href="#main"
	class="sr-only z-50 rounded-xl bg-brand-600 px-4 py-2 text-white focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
>
	Skip to content
</a>

<div class="flex min-h-dvh flex-col">
	<SiteHeader user={data.user} />
	<main id="main" class="flex-1">
		{@render children()}
	</main>
	<SiteFooter settings={data.settings} />
</div>

<CartDrawer />
<DragGhost />
