<script lang="ts">
	import { reveal } from '#lib/actions/reveal.ts';
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
	import RisingText from '#lib/components/ui/RisingText.svelte';
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

	// Hero letter animation: the emoji lands just after the last letter.
	const TITLE_STAGGER = 35;
	const title = $derived(t('home.title'));
	const emojiDelay = $derived(Array.from(title).length * TITLE_STAGGER + 250);

	// Hero slideshow: the campus photo, then featured dishes that have a picture.
	const SLIDE_INTERVAL = 4500;
	const slides = $derived([
		{ src: '/images/hero.jpg', food: null as Food | null },
		...data.featured
			.filter((f) => f.image_url)
			.slice(0, 4)
			.map((f) => ({ src: f.image_url as string, food: f as Food | null }))
	]);
	let current = $state(0);
	let paused = $state(false);
	const active = $derived(current % slides.length);
	// The floating card follows the dish on screen.
	const cardFood = $derived(slides[active].food ?? star);

	$effect(() => {
		const count = slides.length;
		const from = active;
		if (count < 2 || paused || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
		// Re-armed after every change, so a manual pick gets a full interval too.
		const timer = setTimeout(() => (current = (from + 1) % count), SLIDE_INTERVAL);
		return () => clearTimeout(timer);
	});
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
				aria-label={title}
			>
				<RisingText text={title} delay={150} stagger={TITLE_STAGGER} />
				{#key title}
					<span
						class="inline-block animate-fade-up"
						style:animation-delay="{emojiDelay}ms"
						aria-hidden="true">🍱</span
					>
				{/key}
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
			role="region"
			aria-roledescription="carousel"
			aria-label={t('home.slideshow')}
			onmouseenter={() => (paused = true)}
			onmouseleave={() => (paused = false)}
			onfocusin={() => (paused = true)}
			onfocusout={() => (paused = false)}
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
				<div
					class="absolute inset-[11%] isolate overflow-hidden rounded-full bg-brand-100 shadow-[0_40px_80px_-30px_rgb(23_22_56/0.55)]"
				>
					{#each slides as slide, i (i)}
						<img
							src={slide.src}
							alt=""
							class="absolute inset-0 size-full object-cover transition-[opacity,transform] duration-[1200ms] ease-out {i ===
							active
								? 'scale-100 opacity-100'
								: 'scale-110 opacity-0'}"
							loading={i === 0 ? 'eager' : 'lazy'}
							fetchpriority={i === 0 ? 'high' : undefined}
							decoding="async"
						/>
					{/each}
				</div>
				{#if cardFood}
					<div
						class="absolute top-[8%] -left-2 flex items-center gap-3 rounded-2xl bg-white/95 p-2.5 pr-4 shadow-lift backdrop-blur sm:left-0"
					>
						{#key cardFood.id}
							<img
								src={cardFood.image_url}
								alt=""
								class="size-11 animate-fade-up rounded-xl object-cover"
							/>
							<div class="animate-fade-up">
								<p class="text-sm font-bold" lang={i18n.locale}>{i18n.pick(cardFood, 'name')}</p>
								<p class="flex items-center gap-1 text-xs text-ink-muted">
									<Star class="size-3 fill-amber-400 text-amber-400" />
									4.9 · <span class="font-bold text-brand-600">{formatMoney(cardFood.price)}</span>
								</p>
							</div>
						{/key}
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
			{#if slides.length > 1}
				<div class="mt-3 flex justify-center gap-1">
					{#each slides as slide, i (i)}
						<button
							type="button"
							class="group grid h-6 place-items-center px-1"
							aria-label={t('home.showSlide', {
								n: i + 1,
								name: slide.food ? i18n.pick(slide.food, 'name') : 'CampusEats'
							})}
							aria-current={i === active ? 'true' : undefined}
							onclick={() => (current = i)}
						>
							<span
								class="block h-2 rounded-full transition-all duration-300 {i === active
									? 'w-6 bg-brand-600'
									: 'w-2 bg-brand-200 group-hover:bg-brand-400'}"
							></span>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</section>

<!-- How it works -->
<section id="how-it-works" class="container-page scroll-mt-24 py-16">
	<div class="mx-auto max-w-2xl text-center" use:reveal>
		<h2 class="text-3xl font-extrabold tracking-tight">{t('home.stepsTitle')}</h2>
		<p class="mt-3 text-ink-muted">{t('home.stepsSubtitle')}</p>
	</div>
	<ol class="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
		{#each steps as step, i (step.title)}
			{@const Icon = step.icon}
			<li class="card relative p-6 transition hover:-translate-y-1 hover:shadow-lift" use:reveal>
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
	<div class="flex flex-wrap items-end justify-between gap-4" use:reveal>
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
		class="relative isolate overflow-hidden rounded-[28px] bg-brand-700 px-6 py-12 text-center text-white sm:px-12"
		use:reveal={{ from: 'zoom', duration: 900 }}
	>
		<!--
			Poster: a strip of dishes, multiplied with brand purple. Multiply can never be lighter
			than the purple itself, so the white text keeps AA contrast over any part of the photo.
		-->
		<img
			src="/images/cta-poster.jpg"
			alt=""
			class="absolute inset-0 -z-10 size-full object-cover"
			loading="lazy"
			decoding="async"
		/>
		<div
			class="pointer-events-none absolute inset-0 -z-10 bg-brand-500 mix-blend-multiply"
			aria-hidden="true"
		></div>
		<div
			class="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_center,rgb(45_16_102/0.6),transparent_75%)]"
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
