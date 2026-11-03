<script lang="ts">
	import { page } from '$app/state';
	import SearchX from '@lucide/svelte/icons/search-x';
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';
	import Logo from '#lib/components/ui/Logo.svelte';
	import { t } from '#lib/i18n/index.svelte.ts';

	const notFound = $derived(page.status === 404);
</script>

<svelte:head><title>{page.status} · CampusEats</title></svelte:head>

<main class="grid min-h-dvh place-items-center bg-canvas px-4">
	<div class="card w-full max-w-md p-8 text-center">
		<div class="flex justify-center"><Logo /></div>
		<div
			class="mx-auto mt-8 grid size-16 place-items-center rounded-2xl bg-brand-50 text-brand-600"
		>
			{#if notFound}<SearchX class="size-8" />{:else}<TriangleAlert class="size-8" />{/if}
		</div>
		<p class="mt-5 text-sm font-bold text-brand-600">{page.status}</p>
		<h1 class="mt-1 text-2xl font-extrabold">
			{notFound ? t('common.notFound') : t('common.errorTitle')}
		</h1>
		<p class="mt-2 text-sm text-ink-muted">
			{notFound ? t('common.notFoundText') : page.error?.message}
		</p>
		<a href="/" class="btn btn-primary mt-6">{t('common.goHome')}</a>
	</div>
</main>
