<script lang="ts">
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import CirclePlay from '@lucide/svelte/icons/circle-play';
	import ClipboardList from '@lucide/svelte/icons/clipboard-list';
	import ShoppingCart from '@lucide/svelte/icons/shopping-cart';
	import QrCode from '@lucide/svelte/icons/qr-code';
	import HandPlatter from '@lucide/svelte/icons/hand-platter';
	import Clock from '@lucide/svelte/icons/clock';
	import Star from '@lucide/svelte/icons/star';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import Sparkles from '@lucide/svelte/icons/sparkles';
	import FoodCard from '#lib/components/food/FoodCard.svelte';
	import FoodDetailModal from '#lib/components/food/FoodDetailModal.svelte';
	import FloatingCartButton from '#lib/components/cart/FloatingCartButton.svelte';
	import type { Food } from '#lib/types/api.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { formatMoney } from '#lib/utils/money.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	let selected = $state<Food | null>(null);

	const steps = [
		{ icon: ClipboardList, title: 'home.step1.title', text: 'home.step1.text' },
		{ icon: ShoppingCart, title: 'home.step2.title', text: 'home.step2.text' },
		{ icon: QrCode, title: 'home.step3.title', text: 'home.step3.text' },
		{ icon: HandPlatter, title: 'home.step4.title', text: 'home.step4.text' }
	] as const;

	const star = $derived(data.featured[0]);
</script>

<svelte:head>
	<title>CampusEats — {t('home.title')}</title>
</svelte:head>

<!-- Hero -->
<section class="relative overflow-hidden bg-gradient-to-b from-brand-50 via-white to-white">
	<div
		class="pointer-events-none absolute -top-40 -right-40 size-[36rem] rounded-full bg-brand-200/40 blur-3xl"
		aria-hidden="true"
	></div>
	<div
		class="pointer-events-none absolute top-1/2 -left-32 size-72 rounded-full bg-amber-100/60 blur-3xl"
		aria-hidden="true"
	></div>

	<div
		class="container-page relative grid items-center gap-12 pt-10 pb-16 lg:grid-cols-2 lg:pt-16 lg:pb-24"
	>
		<div class="animate-fade-up">
			<span class="chip border border-brand-200 bg-white px-3 py-1 text-brand-700 shadow-sm">
				<Sparkles class="size-3.5" />
				{t('home.badge')}
			</span>
			<h1
				class="mt-5 text-4xl font-extrabold tracking-tight text-ink sm:text-5xl lg:text-6xl lg:leading-[1.05]"
			>
				{t('home.title')}
				<span aria-hidden="true">🍱</span>
			</h1>
			<p class="mt-5 max-w-lg text-lg text-ink-soft">{t('home.subtitle')}</p>
			<div class="mt-8 flex flex-wrap gap-3">
				<a href="/menu" class="btn btn-primary btn-lg">
					{t('home.orderNow')}
					<ArrowRight class="size-4" />
				</a>
				<a href="#how-it-works" class="btn btn-secondary btn-lg">
					<CirclePlay class="size-4 text-brand-600" />
					{t('home.howItWorks')}
				</a>
			</div>
			<dl class="mt-10 flex flex-wrap gap-x-10 gap-y-4">
				<div>
					<dt class="text-sm text-ink-muted">{t('home.statMeals')}</dt>
					<dd class="text-2xl font-extrabold text-ink">{data.mealCount}+</dd>
				</div>
				<div>
					<dt class="text-sm text-ink-muted">{t('home.statPickup')}</dt>
					<dd class="text-2xl font-extrabold text-ink">~15 min</dd>
				</div>
				{#if data.cheapest}
					<div>
						<dt class="text-sm text-ink-muted">{t('home.statPrice')}</dt>
						<dd class="text-2xl font-extrabold text-brand-600">{formatMoney(data.cheapest)}</dd>
					</div>
				{/if}
			</dl>
		</div>

		<div
			class="relative mx-auto w-full max-w-lg animate-fade-up [animation-delay:120ms] lg:max-w-none"
		>
			<div class="relative aspect-square">
				<div
					class="absolute inset-[6%] rounded-full bg-gradient-to-br from-brand-100 to-brand-50 ring-1 ring-brand-100"
					aria-hidden="true"
				></div>
				<svg
					class="absolute inset-0 size-full text-brand-300"
					viewBox="0 0 400 400"
					fill="none"
					aria-hidden="true"
				>
					<circle
						cx="200"
						cy="200"
						r="188"
						stroke="currentColor"
						stroke-width="1.5"
						stroke-dasharray="4 10"
					/>
				</svg>
				<img
					src="/images/hero.jpg"
					alt=""
					class="absolute inset-[11%] size-[78%] rounded-full object-cover shadow-[0_40px_80px_-30px_rgb(23_22_56/0.55)]"
					fetchpriority="high"
				/>
				{#if star}
					<div
						class="absolute top-[8%] -left-2 flex items-center gap-3 rounded-2xl bg-white/95 p-2.5 pr-4 shadow-lift backdrop-blur sm:left-0"
					>
						<img src={star.image_url} alt="" class="size-11 rounded-xl object-cover" />
						<div>
							<p class="text-sm font-bold" lang={i18n.locale}>{i18n.pick(star, 'name')}</p>
							<p class="flex items-center gap-1 text-xs text-ink-muted">
								<Star class="size-3 fill-amber-400 text-amber-400" />
								4.9 · <span class="font-bold text-brand-600">{formatMoney(star.price)}</span>
							</p>
						</div>
					</div>
				{/if}
				<div
					class="absolute right-0 bottom-[10%] flex items-center gap-3 rounded-2xl bg-white/95 p-3 pr-4 shadow-lift backdrop-blur"
				>
					<span class="grid size-10 place-items-center rounded-xl bg-green-50 text-success-ink">
						<CircleCheck class="size-5" />
					</span>
					<div>
						<p class="text-sm font-bold">{t('status.ready')}</p>
						<p class="flex items-center gap-1 text-xs text-ink-muted">
							<Clock class="size-3" /> 12:30
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</section>

<!-- How it works -->
<section id="how-it-works" class="container-page scroll-mt-24 py-16">
	<div class="mx-auto max-w-2xl text-center">
		<h2 class="text-3xl font-extrabold tracking-tight">{t('home.stepsTitle')}</h2>
		<p class="mt-3 text-ink-muted">{t('home.stepsSubtitle')}</p>
	</div>
	<ol class="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
		{#each steps as step, i (step.title)}
			{@const Icon = step.icon}
			<li class="card relative p-6 transition hover:-translate-y-1 hover:shadow-lift">
				<span
					class="absolute top-5 right-5 text-4xl font-extrabold text-brand-100"
					aria-hidden="true">{i + 1}</span
				>
				<span class="grid size-12 place-items-center rounded-2xl bg-brand-50 text-brand-600">
					<Icon class="size-6" />
				</span>
				<h3 class="mt-5 font-bold">{t(step.title)}</h3>
				<p class="mt-1.5 text-sm text-ink-muted">{t(step.text)}</p>
			</li>
		{/each}
	</ol>
</section>

<!-- Featured -->
<section class="container-page py-8">
	<div class="flex flex-wrap items-end justify-between gap-4">
		<div>
			<h2 class="text-3xl font-extrabold tracking-tight">{t('home.featuredTitle')}</h2>
			<p class="mt-2 text-ink-muted">{t('home.featuredSubtitle')}</p>
		</div>
		<a href="/menu" class="btn btn-soft">
			{t('home.viewMenu')}
			<ArrowRight class="size-4" />
		</a>
	</div>
	<div class="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
		{#each data.featured.slice(0, 4) as food (food.id)}
			<FoodCard {food} onopen={(f) => (selected = f)} />
		{/each}
	</div>
</section>

<!-- CTA -->
<section class="container-page pt-12">
	<div
		class="relative overflow-hidden rounded-[28px] bg-gradient-to-br from-brand-600 to-brand-800 px-6 py-12 text-center text-white sm:px-12"
	>
		<div
			class="pointer-events-none absolute -top-24 -right-24 size-72 rounded-full bg-white/10"
			aria-hidden="true"
		></div>
		<div
			class="pointer-events-none absolute -bottom-32 -left-16 size-72 rounded-full bg-white/5"
			aria-hidden="true"
		></div>
		<h2 class="relative text-3xl font-extrabold">{t('home.ctaTitle')}</h2>
		<p class="relative mx-auto mt-3 max-w-md text-white/80">{t('home.ctaText')}</p>
		<a href="/menu" class="btn btn-lg relative mt-7 bg-white text-brand-700 hover:bg-brand-50">
			{t('home.orderNow')}
			<ArrowRight class="size-4" />
		</a>
	</div>
</section>

<FoodDetailModal bind:food={selected} />
<FloatingCartButton />
