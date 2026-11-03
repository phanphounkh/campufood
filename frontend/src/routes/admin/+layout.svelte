<script lang="ts">
	import { adminHref, storeHref } from '#lib/components/admin/links.ts';
	import { onMount } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { afterNavigate, goto } from '$app/navigation';
	import { navigating, page } from '$app/state';
	import Menu from '@lucide/svelte/icons/menu';
	import X from '@lucide/svelte/icons/x';
	import Store from '@lucide/svelte/icons/store';
	import AdminSidebar from '#lib/components/admin/AdminSidebar.svelte';
	import { adminState } from '#lib/components/admin/state.svelte.ts';
	import LanguageSwitcher from '#lib/components/ui/LanguageSwitcher.svelte';
	import { logout } from '#lib/services/auth.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import type { LayoutProps } from './$types';

	let { data, children }: LayoutProps = $props();

	const titles: [string, string][] = [
		['/admin/orders', 'admin.nav.orders'],
		['/admin/menu', 'admin.nav.menu'],
		['/admin/categories', 'admin.nav.categories'],
		['/admin/inventory', 'admin.nav.inventory'],
		['/admin/customers', 'admin.nav.customers'],
		['/admin/payments', 'admin.nav.payments'],
		['/admin/reports', 'admin.nav.reports'],
		['/admin/settings', 'admin.nav.settings']
	];
	const sectionTitle = $derived(
		t(titles.find(([prefix]) => page.url.pathname.startsWith(prefix))?.[1] ?? 'admin.nav.dashboard')
	);

	onMount(() => {
		adminState.refreshSummary();
		const timer = setInterval(() => {
			if (document.visibilityState === 'visible') adminState.refreshSummary();
		}, 20_000);
		return () => clearInterval(timer);
	});

	afterNavigate(() => {
		adminState.sidebarOpen = false;
	});

	async function signOut() {
		try {
			await logout();
		} catch {
			/* the cookie is cleared server-side; navigate away regardless */
		}
		toast.info(t('admin.loggedOut'));
		await goto(adminHref('/admin/login'), { refreshAll: true });
	}

	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && adminState.sidebarOpen) adminState.sidebarOpen = false;
	}
</script>

<svelte:window onkeydown={onKeydown} />

<div class="min-h-dvh bg-canvas">
	<!-- Navigation progress -->
	{#if navigating.to}
		<div class="fixed inset-x-0 top-0 z-[60] h-0.5 overflow-hidden bg-brand-100" aria-hidden="true">
			<div class="h-full w-1/3 animate-[progress_1s_ease-in-out_infinite] bg-brand-600"></div>
		</div>
	{/if}

	<!-- Desktop sidebar -->
	<aside class="fixed inset-y-0 left-0 z-30 hidden w-64 lg:block">
		<AdminSidebar user={data.user} onlogout={signOut} />
	</aside>

	<!-- Mobile off-canvas sidebar -->
	{#if adminState.sidebarOpen}
		<div
			class="fixed inset-0 z-50 lg:hidden"
			role="dialog"
			aria-modal="true"
			aria-label={t('admin.nav.main')}
		>
			<button
				type="button"
				class="absolute inset-0 bg-ink/50 backdrop-blur-sm"
				aria-label={t('admin.closeSidebar')}
				transition:fade={{ duration: 150 }}
				onclick={() => (adminState.sidebarOpen = false)}
			></button>
			<div
				class="absolute inset-y-0 left-0 w-72 max-w-[85vw] shadow-2xl"
				transition:fly={{ x: -300, duration: 220 }}
			>
				<AdminSidebar
					user={data.user}
					onlogout={signOut}
					onnavigate={() => (adminState.sidebarOpen = false)}
				/>
				<button
					type="button"
					class="absolute top-5 right-3 grid size-9 place-items-center rounded-lg text-white/70 hover:bg-white/10 hover:text-white"
					aria-label={t('admin.closeSidebar')}
					onclick={() => (adminState.sidebarOpen = false)}
				>
					<X class="size-5" />
				</button>
			</div>
		</div>
	{/if}

	<div class="lg:pl-64">
		<header
			class="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-line bg-white/85 px-4 backdrop-blur sm:px-6 lg:px-8"
		>
			<button
				type="button"
				class="icon-btn -ml-2 lg:hidden"
				aria-label={t('admin.openSidebar')}
				aria-expanded={adminState.sidebarOpen}
				onclick={() => (adminState.sidebarOpen = true)}
			>
				<Menu class="size-5" />
			</button>
			<p class="flex-1 truncate text-sm font-semibold text-ink-muted">
				<span class="hidden sm:inline">{t('admin.title')} /</span>
				<span class="text-ink">{sectionTitle}</span>
			</p>
			<LanguageSwitcher />
			<a href={storeHref()} class="btn btn-secondary btn-sm hidden sm:inline-flex">
				<Store class="size-4" />{t('admin.viewStore')}
			</a>
		</header>

		<main
			id="main"
			class="mx-auto w-full max-w-[1400px] px-4 py-6 transition-opacity sm:px-6 lg:px-8 lg:py-8 {navigating.to
				? 'opacity-70'
				: ''}"
		>
			{@render children()}
		</main>
	</div>
</div>

<style>
	@keyframes -global-progress {
		from {
			transform: translateX(-100%);
		}
		to {
			transform: translateX(300%);
		}
	}
</style>
