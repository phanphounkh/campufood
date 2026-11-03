<script lang="ts">
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import CartPanel from '#lib/components/cart/CartPanel.svelte';
	import { t } from '#lib/i18n/index.svelte.ts';
</script>

<svelte:head><title>{t('cart.title')} · CampusEats</title></svelte:head>

<div class="container-page max-w-2xl py-8">
	<a href="/menu" class="btn btn-ghost mb-4 -ml-3"><ArrowLeft class="size-4" />{t('cart.browse')}</a
	>
	<CartPanel droppable class="min-h-96" />
</div>
