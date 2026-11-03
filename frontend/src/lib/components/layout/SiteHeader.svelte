<script lang="ts">
	import { slide } from 'svelte/transition';
	import { page } from '$app/state';
	import { goto, invalidateAll } from '$app/navigation';
	import ShoppingCart from '@lucide/svelte/icons/shopping-cart';
	import User from '@lucide/svelte/icons/user';
	import LogOut from '@lucide/svelte/icons/log-out';
	import Menu from '@lucide/svelte/icons/menu';
	import X from '@lucide/svelte/icons/x';
	import Receipt from '@lucide/svelte/icons/receipt';
	import LayoutDashboard from '@lucide/svelte/icons/layout-dashboard';
	import Logo from '#lib/components/ui/Logo.svelte';
	import LanguageSwitcher from '#lib/components/ui/LanguageSwitcher.svelte';
	import { cart } from '#lib/stores/cart.svelte.ts';
	import { drag, dropZone } from '#lib/stores/dnd.svelte.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { logout } from '#lib/services/auth.ts';
	import type { User as UserType } from '#lib/types/api.ts';
	import { t } from '#lib/i18n/index.svelte.ts';

	let { user }: { user: UserType | null } = $props();

	let mobileOpen = $state(false);
	let accountOpen = $state(false);
	let cartButton: HTMLButtonElement | undefined = $state();
	const cartHover = $derived(drag.dragging && drag.activeZone === cartButton);

	const links = [
		{ href: '/', key: 'nav.home' },
		{ href: '/menu', key: 'nav.menu' },
		{ href: '/orders', key: 'nav.orders' },
		{ href: '/about', key: 'nav.about' }
	] as const;

	function isActive(href: string): boolean {
		return href === '/' ? page.url.pathname === '/' : page.url.pathname.startsWith(href);
	}

	async function signOut() {
		accountOpen = false;
		mobileOpen = false;
		try {
			await logout();
		} finally {
			await invalidateAll();
			toast.info(t('auth.loggedOut'));
			await goto('/');
		}
	}

	$effect(() => {
		void page.url.pathname;
		mobileOpen = false;
		accountOpen = false;
	});
</script>

<svelte:window
	onclick={(e) => {
		if (accountOpen && !(e.target as HTMLElement).closest('[data-account-menu]'))
			accountOpen = false;
	}}
/>

<header class="sticky top-0 z-30 border-b border-line/70 bg-white/85 backdrop-blur-xl">
	<div class="container-page flex h-16 items-center gap-4 lg:h-[4.5rem]">
		<Logo />

		<nav class="ml-6 hidden items-center gap-1 md:flex" aria-label="Main">
			{#each links as link (link.href)}
				<a
					href={link.href}
					class="rounded-xl px-3.5 py-2 text-sm font-semibold transition
						{isActive(link.href) ? 'bg-brand-50 text-brand-700' : 'text-ink-soft hover:text-brand-700'}"
					aria-current={isActive(link.href) ? 'page' : undefined}
				>
					{t(link.key)}
				</a>
			{/each}
		</nav>

		<div class="ml-auto flex items-center gap-2">
			<div class="hidden sm:block"><LanguageSwitcher /></div>

			<button
				bind:this={cartButton}
				use:dropZone
				type="button"
				class="relative grid size-11 place-items-center rounded-xl border transition
					{cartHover
					? 'scale-110 border-brand-500 bg-brand-100 text-brand-700'
					: 'border-line bg-white text-ink hover:bg-brand-50 hover:text-brand-700'}"
				aria-label={t('nav.cartWithCount', { count: cart.count })}
				data-testid="header-cart"
				onclick={() => (cart.drawerOpen = true)}
			>
				{#key cart.pulse}
					<ShoppingCart class="size-5 {cart.pulse ? 'animate-pop' : ''}" />
				{/key}
				{#if cart.count > 0}
					<span
						class="absolute -top-1.5 -right-1.5 grid h-5 min-w-5 place-items-center rounded-full bg-brand-600 px-1 text-[11px] font-bold text-white ring-2 ring-white"
						data-testid="cart-count"
					>
						{cart.count}
					</span>
				{/if}
			</button>

			<div class="relative hidden md:block" data-account-menu>
				{#if user}
					<button
						type="button"
						class="flex h-11 items-center gap-2 rounded-xl border border-line bg-white pr-3 pl-1.5 text-sm font-semibold hover:bg-brand-50"
						aria-expanded={accountOpen}
						aria-haspopup="menu"
						onclick={() => (accountOpen = !accountOpen)}
					>
						<span
							class="grid size-8 place-items-center rounded-lg bg-brand-100 font-bold text-brand-700 uppercase"
						>
							{user.name.charAt(0)}
						</span>
						<span class="max-w-28 truncate">{user.name.split(' ')[0]}</span>
					</button>
					{#if accountOpen}
						<div
							class="absolute right-0 mt-2 w-56 rounded-2xl border border-line bg-white p-1.5 shadow-lift"
							role="menu"
							transition:slide={{ duration: 150 }}
						>
							<p class="truncate px-3 pt-2 pb-1 text-xs text-ink-muted">{user.email}</p>
							<a
								href="/orders"
								class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm hover:bg-brand-50"
								role="menuitem"
							>
								<Receipt class="size-4" />{t('nav.orders')}
							</a>
							{#if user.role !== 'customer'}
								<a
									href="/admin"
									class="flex items-center gap-2 rounded-xl px-3 py-2 text-sm hover:bg-brand-50"
									role="menuitem"
								>
									<LayoutDashboard class="size-4" />{t('nav.admin')}
								</a>
							{/if}
							<button
								type="button"
								class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-danger-ink hover:bg-red-50"
								role="menuitem"
								onclick={signOut}
							>
								<LogOut class="size-4" />{t('nav.logout')}
							</button>
						</div>
					{/if}
				{:else}
					<a href="/login" class="btn btn-secondary h-11" aria-label={t('nav.login')}>
						<User class="size-4" />
						<span class="hidden lg:inline">{t('nav.login')}</span>
					</a>
				{/if}
			</div>

			<button
				type="button"
				class="icon-btn md:hidden"
				aria-label={mobileOpen ? t('nav.closeMenu') : t('nav.openMenu')}
				aria-expanded={mobileOpen}
				onclick={() => (mobileOpen = !mobileOpen)}
			>
				{#if mobileOpen}<X class="size-5" />{:else}<Menu class="size-5" />{/if}
			</button>
		</div>
	</div>

	{#if mobileOpen}
		<nav
			class="border-t border-line bg-white md:hidden"
			transition:slide={{ duration: 200 }}
			aria-label="Mobile"
		>
			<div class="container-page flex flex-col gap-1 py-3">
				{#each links as link (link.href)}
					<a
						href={link.href}
						class="rounded-xl px-3 py-2.5 font-semibold {isActive(link.href)
							? 'bg-brand-50 text-brand-700'
							: 'text-ink'}"
					>
						{t(link.key)}
					</a>
				{/each}
				<div class="mt-2 flex items-center justify-between border-t border-line pt-3">
					<LanguageSwitcher />
					{#if user}
						<button type="button" class="btn btn-ghost" onclick={signOut}>
							<LogOut class="size-4" />{t('nav.logout')}
						</button>
					{:else}
						<a href="/login" class="btn btn-secondary"><User class="size-4" />{t('nav.login')}</a>
					{/if}
				</div>
				{#if user && user.role !== 'customer'}
					<a href="/admin" class="btn btn-soft mt-1"
						><LayoutDashboard class="size-4" />{t('nav.admin')}</a
					>
				{/if}
			</div>
		</nav>
	{/if}
</header>
