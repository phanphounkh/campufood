<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import LayoutDashboard from '@lucide/svelte/icons/layout-dashboard';
	import ClipboardList from '@lucide/svelte/icons/clipboard-list';
	import Utensils from '@lucide/svelte/icons/utensils';
	import Tags from '@lucide/svelte/icons/tags';
	import Boxes from '@lucide/svelte/icons/boxes';
	import Users from '@lucide/svelte/icons/users';
	import CreditCard from '@lucide/svelte/icons/credit-card';
	import ChartColumn from '@lucide/svelte/icons/chart-column';
	import Settings from '@lucide/svelte/icons/settings';
	import LogOut from '@lucide/svelte/icons/log-out';
	import Logo from '#lib/components/ui/Logo.svelte';
	import { t } from '#lib/i18n/index.svelte.ts';
	import type { User } from '#lib/types/api.ts';
	import { adminState } from './state.svelte.ts';

	let {
		user,
		onlogout,
		onnavigate
	}: {
		user: User;
		onlogout: () => void;
		onnavigate?: () => void;
	} = $props();

	const items = [
		{ href: '/admin', key: 'admin.nav.dashboard', icon: LayoutDashboard },
		{ href: '/admin/orders', key: 'admin.nav.orders', icon: ClipboardList, badge: true },
		{ href: '/admin/menu', key: 'admin.nav.menu', icon: Utensils },
		{ href: '/admin/categories', key: 'admin.nav.categories', icon: Tags },
		{ href: '/admin/inventory', key: 'admin.nav.inventory', icon: Boxes },
		{ href: '/admin/customers', key: 'admin.nav.customers', icon: Users },
		{ href: '/admin/payments', key: 'admin.nav.payments', icon: CreditCard },
		{ href: '/admin/reports', key: 'admin.nav.reports', icon: ChartColumn },
		{ href: '/admin/settings', key: 'admin.nav.settings', icon: Settings }
	] as const;

	function isActive(href: string): boolean {
		const path = page.url.pathname;
		return href === '/admin' ? path === '/admin' : path === href || path.startsWith(`${href}/`);
	}

	const initials = $derived(
		user.name
			.split(/\s+/)
			.map((part) => part[0])
			.slice(0, 2)
			.join('')
			.toUpperCase()
	);
</script>

<div class="flex h-full flex-col bg-navy text-white">
	<div class="px-5 pt-6 pb-5">
		<Logo variant="dark" subtitle={t('admin.subtitle')} href={resolve('/admin')} />
	</div>

	<nav class="flex-1 overflow-y-auto px-3" aria-label={t('admin.nav.main')}>
		<ul class="space-y-1">
			{#each items as item (item.href)}
				{@const active = isActive(item.href)}
				{@const Icon = item.icon}
				<li>
					<a
						href={resolve(item.href)}
						onclick={onnavigate}
						aria-current={active ? 'page' : undefined}
						class="group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition
							{active
							? 'bg-brand-600 text-white shadow-[0_8px_20px_-10px_rgb(100_37_216/0.9)]'
							: 'text-white/70 hover:bg-white/8 hover:text-white'}"
					>
						<Icon
							class="size-[18px] shrink-0 {active ? '' : 'text-white/60 group-hover:text-white'}"
						/>
						<span class="flex-1">{t(item.key)}</span>
						{#if 'badge' in item && adminState.waiting > 0}
							<span
								class="grid min-w-5 place-items-center rounded-full px-1.5 text-[11px] font-bold tabular-nums
									{active ? 'bg-white text-brand-700' : 'bg-danger-ink text-white'}"
								title={t('admin.nav.ordersBadge', { count: adminState.waiting })}
							>
								{adminState.waiting}
								<span class="sr-only"
									>{t('admin.nav.ordersBadge', { count: adminState.waiting })}</span
								>
							</span>
						{/if}
					</a>
				</li>
			{/each}
		</ul>
	</nav>

	<div class="border-t border-white/10 p-3">
		<div class="flex items-center gap-3 rounded-xl bg-white/5 px-3 py-3">
			<span
				class="grid size-9 shrink-0 place-items-center rounded-full bg-brand-500 text-xs font-bold"
				aria-hidden="true">{initials}</span
			>
			<div class="min-w-0 flex-1">
				<p class="truncate text-sm font-semibold">{user.name}</p>
				<p class="truncate text-xs text-white/55">
					{t(`admin.role.${user.role}`)} · {user.email}
				</p>
			</div>
		</div>
		<button
			type="button"
			class="mt-2 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-white/70 transition hover:bg-white/8 hover:text-white"
			onclick={onlogout}
		>
			<LogOut class="size-[18px] text-white/60" />
			{t('admin.nav.logout')}
		</button>
	</div>
</div>
