<script lang="ts">
	import { reveal } from '#lib/actions/reveal.ts';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import QrCode from '@lucide/svelte/icons/qr-code';
	import ShoppingBag from '@lucide/svelte/icons/shopping-bag';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import CircleAlert from '@lucide/svelte/icons/circle-alert';
	import Clock from '@lucide/svelte/icons/clock';
	import Lock from '@lucide/svelte/icons/lock';
	import CartLineItem from '#lib/components/cart/CartLineItem.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import { cart } from '#lib/stores/cart.svelte.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { rememberOrder } from '#lib/stores/guestOrders.ts';
	import { createOrder } from '#lib/services/orders.ts';
	import { listFoods } from '#lib/services/catalog.ts';
	import { ApiError } from '#lib/services/api.ts';
	import { checkoutSchema, fieldErrors } from '#lib/utils/validation.ts';
	import { pickupSlots, formatSlotTime } from '#lib/utils/pickup.ts';
	import { formatCents } from '#lib/utils/money.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const settings = $derived(page.data.settings);
	const user = $derived(page.data.user);
	const PROFILE_KEY = 'campuseats.customer.v1';

	let form = $state({
		customer_name: '',
		customer_phone: '',
		student_id: '',
		pickup_time: '',
		notes: ''
	});
	let errors = $state<Record<string, string>>({});
	let formError = $state('');
	let submitting = $state(false);

	const slots = $derived(
		settings
			? pickupSlots({
					timeZone: settings.timezone,
					opening: settings.opening_time,
					closing: settings.closing_time,
					minPrepMinutes: settings.min_prep_minutes
				})
			: []
	);
	const todaySlots = $derived(slots.filter((s) => s.day === 'today'));
	const tomorrowSlots = $derived(slots.filter((s) => s.day === 'tomorrow'));

	onMount(() => {
		cart.load();
		const hadItems = cart.lines.length > 0;
		if (cart.sync(data.foods) && hadItems) toast.info(t('cart.updatedPrices'));
		try {
			const saved = JSON.parse(localStorage.getItem(PROFILE_KEY) ?? '{}');
			form.customer_name = saved.customer_name ?? user?.name ?? '';
			form.customer_phone = saved.customer_phone ?? user?.phone ?? '';
			form.student_id = saved.student_id ?? '';
		} catch {
			form.customer_name = user?.name ?? '';
		}
	});

	$effect(() => {
		if (!form.pickup_time && slots.length) form.pickup_time = slots[0].value;
	});

	async function resyncCart(message: string) {
		try {
			const foods = await listFoods({ page_size: 100 });
			cart.sync(foods.items);
		} catch {
			/* keep the current cart */
		}
		formError = message;
	}

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		formError = '';
		const parsed = checkoutSchema.safeParse(form);
		if (!parsed.success) {
			errors = fieldErrors(parsed.error);
			document.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();
			return;
		}
		errors = {};
		if (!cart.lines.length) return;

		submitting = true;
		try {
			const result = await createOrder({
				...parsed.data,
				items: cart.lines.map((l) => ({ food_id: l.foodId, quantity: l.quantity })),
				expected_total: cart.totalString
			});
			rememberOrder({
				id: result.order.id,
				number: result.order.order_number,
				token: result.access_token,
				total: result.order.total,
				createdAt: result.order.created_at
			});
			try {
				localStorage.setItem(
					PROFILE_KEY,
					JSON.stringify({
						customer_name: parsed.data.customer_name,
						customer_phone: parsed.data.customer_phone,
						student_id: parsed.data.student_id ?? ''
					})
				);
			} catch {
				/* ignore */
			}
			cart.clear();
			await goto(`/orders/${result.order.id}/pay`, { replace: true });
		} catch (err) {
			if (!(err instanceof ApiError)) {
				formError = t('common.errorTitle');
			} else if (err.code === 'ITEMS_UNAVAILABLE') {
				await resyncCart(t('checkout.itemsUnavailable'));
			} else if (err.code === 'PRICE_CHANGED') {
				await resyncCart(t('checkout.priceChanged'));
			} else if (err.code === 'STORE_CLOSED') {
				formError = t('checkout.closed');
			} else if (err.code === 'INVALID_PICKUP_TIME') {
				errors = { pickup_time: err.message };
			} else if (err.code === 'VALIDATION_ERROR') {
				errors = err.fieldErrors;
				formError = err.message;
			} else {
				formError = err.message;
			}
		} finally {
			submitting = false;
		}
	}

	const inputClass = (field: string) =>
		`w-full ${errors[field] ? 'border-danger focus:border-danger focus:ring-red-100' : ''}`;
</script>

<svelte:head><title>{t('checkout.title')} · CampusEats</title></svelte:head>

<div class="container-page py-8">
	<a href="/menu" class="btn btn-ghost -ml-3"><ArrowLeft class="size-4" />{t('cart.browse')}</a>
	<h1 class="mt-3 text-3xl font-extrabold tracking-tight">{t('checkout.title')}</h1>
	<p class="mt-1 text-ink-muted">{t('checkout.subtitle')}</p>

	{#if cart.lines.length === 0 && !submitting}
		<div class="card mt-8" use:reveal={{ from: 'zoom' }}>
			<EmptyState icon={ShoppingBag} title={t('checkout.emptyCart')} text={t('cart.emptyHint')}>
				<a href="/menu" class="btn btn-primary">{t('cart.browse')}</a>
			</EmptyState>
		</div>
	{:else}
		<form class="mt-8 grid gap-8 lg:grid-cols-[minmax(0,1fr)_400px]" novalidate onsubmit={submit}>
			<div class="space-y-6">
				{#if settings && !settings.accepting_orders}
					<p
						class="flex items-start gap-2 rounded-2xl bg-amber-50 p-4 text-sm font-medium text-amber-900"
					>
						<CircleAlert class="mt-0.5 size-4 shrink-0" />{t('checkout.closed')}
					</p>
				{/if}

				<section class="card p-5 sm:p-6" use:reveal>
					<div class="flex flex-wrap items-baseline justify-between gap-2">
						<h2 class="text-lg font-bold">{t('checkout.details')}</h2>
						<p class="text-sm text-ink-muted">
							{#if user}
								{t('checkout.loggedInAs', { name: user.name })}
							{:else}
								{t('checkout.guest')}
								<a href="/login?next=/checkout" class="font-semibold text-brand-700 hover:underline"
									>{t('checkout.loginHint')}</a
								>
							{/if}
						</p>
					</div>

					<div class="mt-5 grid gap-5 sm:grid-cols-2">
						<div class="sm:col-span-2">
							<label class="label" for="customer_name">{t('checkout.name')}</label>
							<input
								id="customer_name"
								name="customer_name"
								autocomplete="name"
								bind:value={form.customer_name}
								placeholder={t('checkout.namePlaceholder')}
								class={inputClass('customer_name')}
								aria-invalid={!!errors.customer_name}
								aria-describedby={errors.customer_name ? 'customer_name-error' : undefined}
							/>
							{#if errors.customer_name}<p id="customer_name-error" class="field-error">
									{t(errors.customer_name)}
								</p>{/if}
						</div>
						<div>
							<label class="label" for="customer_phone">{t('checkout.phone')}</label>
							<input
								id="customer_phone"
								name="customer_phone"
								type="tel"
								inputmode="tel"
								autocomplete="tel"
								bind:value={form.customer_phone}
								placeholder={t('checkout.phonePlaceholder')}
								class={inputClass('customer_phone')}
								aria-invalid={!!errors.customer_phone}
								aria-describedby={errors.customer_phone ? 'customer_phone-error' : undefined}
							/>
							{#if errors.customer_phone}<p id="customer_phone-error" class="field-error">
									{t(errors.customer_phone)}
								</p>{/if}
						</div>
						<div>
							<label class="label" for="student_id">
								{t('checkout.studentId')}
								<span class="font-normal text-ink-muted">({t('common.optional')})</span>
							</label>
							<input
								id="student_id"
								name="student_id"
								bind:value={form.student_id}
								class={inputClass('student_id')}
							/>
							{#if errors.student_id}<p class="field-error">{t(errors.student_id)}</p>{/if}
						</div>
						<div class="sm:col-span-2">
							<label class="label" for="pickup_time">{t('checkout.pickup')}</label>
							{#if slots.length}
								<div class="relative">
									<Clock
										class="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-ink-muted"
									/>
									<select
										id="pickup_time"
										name="pickup_time"
										bind:value={form.pickup_time}
										class="{inputClass('pickup_time')} rounded-xl border-line pl-10"
										aria-invalid={!!errors.pickup_time}
										data-testid="pickup-select"
									>
										{#if todaySlots.length}
											<optgroup label={t('common.today')}>
												{#each todaySlots as slot (slot.value)}
													<option value={slot.value}
														>{t('common.today')} · {formatSlotTime(slot.time, i18n.locale)}</option
													>
												{/each}
											</optgroup>
										{/if}
										{#if tomorrowSlots.length}
											<optgroup label={t('common.tomorrow')}>
												{#each tomorrowSlots as slot (slot.value)}
													<option value={slot.value}
														>{t('common.tomorrow')} · {formatSlotTime(
															slot.time,
															i18n.locale
														)}</option
													>
												{/each}
											</optgroup>
										{/if}
									</select>
								</div>
							{:else}
								<p class="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-900">
									{t('checkout.noSlots')}
								</p>
							{/if}
							{#if settings}
								<p class="mt-1.5 text-xs text-ink-muted">
									{t('checkout.pickupHint', {
										open: settings.opening_time,
										close: settings.closing_time
									})}
								</p>
							{/if}
							{#if errors.pickup_time}<p class="field-error">{t(errors.pickup_time)}</p>{/if}
						</div>
						<div class="sm:col-span-2">
							<label class="label" for="notes">
								{t('checkout.notes')}
								<span class="font-normal text-ink-muted">({t('common.optional')})</span>
							</label>
							<textarea
								id="notes"
								name="notes"
								rows="2"
								maxlength="300"
								bind:value={form.notes}
								placeholder={t('checkout.notesPlaceholder')}
								class={inputClass('notes')}></textarea>
						</div>
					</div>
				</section>

				<section class="card p-5 sm:p-6" use:reveal>
					<h2 class="text-lg font-bold">{t('checkout.payment')}</h2>
					<div
						class="mt-4 flex items-start gap-4 rounded-2xl border-2 border-brand-600 bg-brand-50/60 p-4"
					>
						<span
							class="grid size-11 shrink-0 place-items-center rounded-xl bg-brand-600 text-white"
						>
							<QrCode class="size-5" />
						</span>
						<div>
							<p class="font-bold text-ink">{t('checkout.khqr')}</p>
							<p class="text-sm text-ink-muted">{t('checkout.khqrHint')}</p>
						</div>
						<span
							class="mt-1 ml-auto grid size-5 place-items-center rounded-full border-2 border-brand-600"
							aria-hidden="true"
						>
							<span class="size-2.5 rounded-full bg-brand-600"></span>
						</span>
					</div>
				</section>
			</div>

			<aside use:reveal={{ from: 'right' }}>
				<div class="card sticky top-24 p-5 sm:p-6">
					<h2 class="text-lg font-bold">{t('checkout.summary')}</h2>
					<ul class="mt-2 divide-y divide-line">
						{#each cart.lines as line (line.foodId)}
							<CartLineItem {line} compact />
						{/each}
					</ul>
					<dl class="mt-3 space-y-1.5 border-t border-line pt-4 text-sm">
						<div class="flex justify-between text-ink-soft">
							<dt>{t('cart.subtotal')}</dt>
							<dd class="font-semibold tabular-nums">{formatCents(cart.subtotalCents)}</dd>
						</div>
						<div class="flex justify-between text-ink-soft">
							<dt>{t('cart.serviceFee')}</dt>
							<dd class="font-semibold">{t('common.free')}</dd>
						</div>
						<div class="flex items-baseline justify-between pt-2">
							<dt class="text-lg font-extrabold">{t('cart.total')}</dt>
							<dd
								class="text-2xl font-extrabold text-brand-600 tabular-nums"
								data-testid="checkout-total"
							>
								{formatCents(cart.totalCents)}
							</dd>
						</div>
					</dl>

					{#if formError}
						<p
							class="mt-4 flex items-start gap-2 rounded-xl bg-red-50 p-3 text-sm font-medium text-danger-ink"
							role="alert"
						>
							<CircleAlert class="mt-0.5 size-4 shrink-0" />{formError}
						</p>
					{/if}

					<button
						type="submit"
						class="btn btn-primary btn-lg mt-5 w-full"
						disabled={submitting ||
							!cart.lines.length ||
							!slots.length ||
							settings?.accepting_orders === false}
						data-testid="place-order"
					>
						{#if submitting}
							<LoaderCircle class="size-4 animate-spin" />{t('checkout.placing')}
						{:else}
							{t('checkout.placeOrder', { total: formatCents(cart.totalCents) })}
						{/if}
					</button>
					<p class="mt-3 flex items-center justify-center gap-1.5 text-xs text-ink-muted">
						<Lock class="size-3" />{t('footer.demo')}
					</p>
				</div>
			</aside>
		</form>
	{/if}
</div>
