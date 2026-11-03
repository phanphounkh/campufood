<script lang="ts">
	import { reveal } from '#lib/actions/reveal.ts';
	import { page } from '$app/state';
	import Wallet from '@lucide/svelte/icons/wallet';
	import Timer from '@lucide/svelte/icons/timer';
	import ChefHat from '@lucide/svelte/icons/chef-hat';
	import Clock from '@lucide/svelte/icons/clock';
	import Phone from '@lucide/svelte/icons/phone';
	import Mail from '@lucide/svelte/icons/mail';
	import MapPin from '@lucide/svelte/icons/map-pin';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import { t } from '#lib/i18n/index.svelte.ts';

	const settings = $derived(page.data.settings);
	const reasons = [
		{ icon: Wallet, title: 'about.why1.title', text: 'about.why1.text' },
		{ icon: Timer, title: 'about.why2.title', text: 'about.why2.text' },
		{ icon: ChefHat, title: 'about.why3.title', text: 'about.why3.text' }
	] as const;
</script>

<svelte:head><title>{t('about.title')}</title></svelte:head>

<section class="bg-gradient-to-b from-brand-50 to-white">
	<div class="container-page grid items-center gap-10 py-14 lg:grid-cols-2">
		<div use:reveal={{ from: 'left' }}>
			<h1 class="text-4xl font-extrabold tracking-tight">{t('about.title')}</h1>
			<p class="mt-5 text-lg text-ink-soft">{t('about.text')}</p>
			<a href="/menu" class="btn btn-primary btn-lg mt-8"
				>{t('home.orderNow')}<ArrowRight class="size-4" /></a
			>
		</div>
		<img
			use:reveal={{ from: 'right' }}
			src="/images/hero.jpg"
			alt=""
			class="aspect-[5/4] w-full rounded-[28px] object-cover shadow-lift"
		/>
	</div>
</section>

<section class="container-page grid gap-5 py-10 md:grid-cols-3">
	{#each reasons as reason (reason.title)}
		{@const Icon = reason.icon}
		<div class="card p-6" use:reveal>
			<span class="grid size-12 place-items-center rounded-2xl bg-brand-50 text-brand-600"
				><Icon class="size-6" /></span
			>
			<h2 class="mt-4 font-bold">{t(reason.title)}</h2>
			<p class="mt-1 text-sm text-ink-muted">{t(reason.text)}</p>
		</div>
	{/each}
</section>

{#if settings}
	<section class="container-page grid gap-5 md:grid-cols-3">
		<div class="card p-6" use:reveal>
			<h2 class="flex items-center gap-2 font-bold">
				<Clock class="size-4 text-brand-600" />{t('about.hours')}
			</h2>
			<p class="mt-2 text-ink-soft">
				{t('footer.hoursValue', { open: settings.opening_time, close: settings.closing_time })}
			</p>
		</div>
		<div class="card p-6" use:reveal>
			<h2 class="flex items-center gap-2 font-bold">
				<Phone class="size-4 text-brand-600" />{t('about.contact')}
			</h2>
			<p class="mt-2 text-ink-soft">{settings.store_phone}</p>
			<p class="flex items-center gap-1.5 text-ink-soft">
				<Mail class="size-3.5" />{settings.store_email}
			</p>
		</div>
		<div class="card p-6" use:reveal>
			<h2 class="flex items-center gap-2 font-bold">
				<MapPin class="size-4 text-brand-600" />{t('about.location')}
			</h2>
			<p class="mt-2 text-ink-soft">{settings.store_address}</p>
		</div>
	</section>
{/if}
