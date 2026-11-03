<script lang="ts">
	import Phone from '@lucide/svelte/icons/phone';
	import Mail from '@lucide/svelte/icons/mail';
	import MapPin from '@lucide/svelte/icons/map-pin';
	import Clock from '@lucide/svelte/icons/clock';
	import ThumbsUp from '@lucide/svelte/icons/thumbs-up';
	import Send from '@lucide/svelte/icons/send';
	import Camera from '@lucide/svelte/icons/camera';
	import Logo from '#lib/components/ui/Logo.svelte';
	import type { PublicSettings } from '#lib/types/api.ts';
	import { t } from '#lib/i18n/index.svelte.ts';

	let { settings }: { settings: PublicSettings | null } = $props();

	const name = $derived(settings?.store_name ?? 'CampusEats');
	const socials = $derived(
		[
			{ href: settings?.facebook_url, label: 'Facebook', icon: ThumbsUp },
			{ href: settings?.telegram_url, label: 'Telegram', icon: Send },
			{ href: settings?.instagram_url, label: 'Instagram', icon: Camera }
		].filter((s) => s.href)
	);
</script>

<footer class="mt-24 bg-navy text-white/80">
	<div class="container-page grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1.2fr_1fr]">
		<div>
			<Logo variant="dark" subtitle={settings?.store_tagline} />
			<p class="mt-4 max-w-xs text-sm leading-relaxed text-white/65">{t('footer.about')}</p>
			{#if socials.length}
				<p class="mt-6 text-xs font-bold tracking-wider text-white/50 uppercase">
					{t('footer.follow')}
				</p>
				<div class="mt-3 flex gap-2">
					{#each socials as social (social.label)}
						{@const Icon = social.icon}
						<a
							href={social.href}
							target="_blank"
							rel="noopener noreferrer"
							class="grid size-10 place-items-center rounded-xl bg-white/10 text-white transition hover:bg-brand-600"
							aria-label={social.label}
							title={social.label}
						>
							<Icon class="size-4" />
						</a>
					{/each}
				</div>
			{/if}
		</div>

		<div>
			<h2 class="text-sm font-bold text-white">{t('footer.explore')}</h2>
			<ul class="mt-4 space-y-2.5 text-sm">
				<li><a class="hover:text-white" href="/menu">{t('nav.menu')}</a></li>
				<li><a class="hover:text-white" href="/orders">{t('nav.orders')}</a></li>
				<li><a class="hover:text-white" href="/about">{t('nav.about')}</a></li>
				<li><a class="hover:text-white" href="/login">{t('nav.login')}</a></li>
			</ul>
		</div>

		<div>
			<h2 class="text-sm font-bold text-white">{t('footer.contact')}</h2>
			<ul class="mt-4 space-y-3 text-sm">
				{#if settings?.store_phone}
					<li class="flex gap-2.5">
						<Phone class="mt-0.5 size-4 shrink-0 text-brand-300" />
						<a class="hover:text-white" href="tel:{settings.store_phone.replace(/\s/g, '')}"
							>{settings.store_phone}</a
						>
					</li>
				{/if}
				{#if settings?.store_email}
					<li class="flex gap-2.5">
						<Mail class="mt-0.5 size-4 shrink-0 text-brand-300" />
						<a class="hover:text-white" href="mailto:{settings.store_email}"
							>{settings.store_email}</a
						>
					</li>
				{/if}
				{#if settings?.store_address}
					<li class="flex gap-2.5">
						<MapPin class="mt-0.5 size-4 shrink-0 text-brand-300" />
						<span>{settings.store_address}</span>
					</li>
				{/if}
			</ul>
		</div>

		<div>
			<h2 class="text-sm font-bold text-white">{t('footer.hours')}</h2>
			<p class="mt-4 flex gap-2.5 text-sm">
				<Clock class="mt-0.5 size-4 shrink-0 text-brand-300" />
				{t('footer.hoursValue', {
					open: settings?.opening_time ?? '07:00',
					close: settings?.closing_time ?? '17:00'
				})}
			</p>
		</div>
	</div>
	<div class="border-t border-white/10">
		<div
			class="container-page flex flex-col gap-2 py-5 text-xs text-white/50 sm:flex-row sm:justify-between"
		>
			<p>{t('footer.rights', { year: new Date().getFullYear(), name })}</p>
			<p>{t('footer.demo')}</p>
		</div>
	</div>
</footer>
