<script lang="ts">
	import { reveal } from '#lib/actions/reveal.ts';
	import { onDestroy, onMount } from 'svelte';
	import { page } from '$app/state';
	import QRCode from 'qrcode';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';
	import Info from '@lucide/svelte/icons/info';
	import Timer from '@lucide/svelte/icons/timer';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import PartyPopper from '@lucide/svelte/icons/party-popper';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import Hourglass from '@lucide/svelte/icons/hourglass';
	import CircleX from '@lucide/svelte/icons/circle-x';
	import SearchX from '@lucide/svelte/icons/search-x';
	import Smartphone from '@lucide/svelte/icons/smartphone';
	import StatusBadge from '#lib/components/ui/StatusBadge.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import ConfirmDialog from '#lib/components/ui/ConfirmDialog.svelte';
	import {
		cancelOrder,
		confirmDemoPayment,
		getOrder,
		paymentStatus
	} from '#lib/services/orders.ts';
	import { ApiError } from '#lib/services/api.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import type { Order, PaymentCheckout, PaymentStatus } from '#lib/types/api.ts';
	import { formatCountdown } from '#lib/utils/format.ts';
	import { formatMoney } from '#lib/utils/money.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	// svelte-ignore state_referenced_locally
	let order = $state<Order | null>(data.order);
	// svelte-ignore state_referenced_locally
	let payment = $state<PaymentCheckout | null>(data.payment);
	// svelte-ignore state_referenced_locally
	const token = data.token;
	// svelte-ignore state_referenced_locally
	let status = $state<PaymentStatus | null>(payment?.status ?? order?.payment?.status ?? null);
	let qrSvg = $state('');
	let now = $state(Date.now());
	let confirming = $state(false);
	let cancelling = $state(false);
	let askCancel = $state(false);
	let error = $state('');

	const demoEnabled = $derived(page.data.settings?.demo_payments_enabled !== false);
	const remaining = $derived(payment ? new Date(payment.expires_at).getTime() - now : 0);
	const view = $derived.by(() => {
		if (!order) return 'missing';
		if (status === 'paid' || (order.status !== 'pending_payment' && order.status !== 'cancelled'))
			return 'paid';
		if (order.status === 'cancelled') return status === 'expired' ? 'expired' : 'cancelled';
		if (status === 'expired' || (payment && remaining <= 0)) return 'expired';
		return 'pending';
	});

	$effect(() => {
		const payload = payment?.qr_payload;
		if (!payload) return;
		QRCode.toString(payload, {
			type: 'svg',
			margin: 1,
			errorCorrectionLevel: 'M',
			color: { dark: '#171638', light: '#ffffff' }
		}).then((svg) => (qrSvg = svg));
	});

	async function refresh() {
		if (!order || !payment) return;
		try {
			const info = await paymentStatus(payment.id, token);
			status = info.status;
			if (info.order_status !== order.status) order = await getOrder(order.id, token);
		} catch {
			/* transient network issue: try again next tick */
		}
	}

	let ticker: ReturnType<typeof setInterval> | undefined;
	let poller: ReturnType<typeof setInterval> | undefined;
	onMount(() => {
		ticker = setInterval(() => (now = Date.now()), 1000);
		poller = setInterval(() => {
			if (view === 'pending') refresh();
		}, 4000);
	});
	onDestroy(() => {
		clearInterval(ticker);
		clearInterval(poller);
	});

	// When the countdown hits zero, ask the server (it expires the order and releases stock).
	let expiryChecked = false;
	$effect(() => {
		if (payment && remaining <= 0 && !expiryChecked && status === 'pending') {
			expiryChecked = true;
			refresh();
		}
	});

	async function simulate() {
		if (!order || !payment) return;
		confirming = true;
		error = '';
		try {
			const result = await confirmDemoPayment(order.id, payment.id, token);
			status = result.status;
			order = await getOrder(order.id, token);
		} catch (err) {
			if (err instanceof ApiError && err.code === 'PAYMENT_EXPIRED') {
				status = 'expired';
				order = await getOrder(order.id, token).catch(() => order);
			} else if (err instanceof ApiError && err.code === 'DEMO_DISABLED') {
				error = t('pay.demoDisabled');
			} else {
				error = err instanceof Error ? err.message : t('common.errorTitle');
			}
		} finally {
			confirming = false;
		}
	}

	async function cancel() {
		if (!order) return;
		cancelling = true;
		try {
			order = await cancelOrder(order.id, token);
			status = order.payment?.status ?? 'cancelled';
			askCancel = false;
			toast.info(t('pay.cancelledTitle'));
		} catch (err) {
			toast.error(err instanceof Error ? err.message : t('common.errorTitle'));
		} finally {
			cancelling = false;
		}
	}
</script>

<svelte:head><title>{t('pay.title')} · CampusEats</title></svelte:head>

<div class="container-page max-w-xl py-8">
	{#if view === 'missing' || !order}
		<div class="card" use:reveal={{ from: 'zoom' }}>
			<EmptyState icon={SearchX} title={t('orders.notFound')} text={t('orders.notFoundText')}>
				<a href="/orders" class="btn btn-primary">{t('nav.orders')}</a>
			</EmptyState>
		</div>
	{:else}
		<div class="flex items-center gap-2">
			<a href="/orders/{order.id}" class="icon-btn -ml-2" aria-label={t('common.back')}
				><ArrowLeft class="size-5" /></a
			>
			<h1 class="flex-1 text-center text-2xl font-extrabold tracking-tight">{t('pay.title')}</h1>
			<span class="size-10" aria-hidden="true"></span>
		</div>

		<div
			class="mt-5 flex items-center justify-center gap-2 rounded-2xl border border-amber-300 bg-amber-50 px-4 py-3 text-center text-sm font-extrabold tracking-wide text-amber-900"
			role="note"
			data-testid="demo-banner"
		>
			<TriangleAlert class="size-4 shrink-0" />
			{t('pay.demoBanner')}
		</div>

		{#if view === 'paid'}
			<section
				class="card mt-5 overflow-hidden text-center"
				data-testid="payment-success"
				use:reveal={{ from: 'zoom' }}
			>
				<div class="bg-gradient-to-b from-green-50 to-white px-6 pt-10 pb-6">
					<div
						class="mx-auto grid size-20 animate-pop place-items-center rounded-full bg-success text-white shadow-[0_12px_30px_-10px_rgb(22_163_74/0.7)]"
					>
						<CircleCheck class="size-10" />
					</div>
					<h2 class="mt-5 flex items-center justify-center gap-2 text-2xl font-extrabold">
						{t('pay.successTitle')}
						<PartyPopper class="size-6 text-brand-600" />
					</h2>
					<p class="mx-auto mt-2 max-w-sm text-ink-muted">
						{t('pay.successText', { number: order.order_number })}
					</p>
				</div>
				<dl class="mx-6 grid grid-cols-2 gap-3 border-t border-line py-5 text-left text-sm">
					<div>
						<dt class="text-ink-muted">{t('pay.order')}</dt>
						<dd class="font-bold">{order.order_number}</dd>
					</div>
					<div>
						<dt class="text-ink-muted">{t('pay.totalAmount')}</dt>
						<dd class="font-bold text-brand-600">{formatMoney(order.total)}</dd>
					</div>
					<div>
						<dt class="text-ink-muted">{t('orders.status')}</dt>
						<dd><StatusBadge status={order.status} /></dd>
					</div>
					{#if order.payment?.transaction_reference}
						<div>
							<dt class="text-ink-muted">{t('pay.reference')}</dt>
							<dd class="font-mono text-xs font-semibold">{order.payment.transaction_reference}</dd>
						</div>
					{/if}
				</dl>
				<div class="px-6 pb-6">
					<a
						href="/orders/{order.id}"
						class="btn btn-primary btn-lg w-full"
						data-testid="track-order">{t('pay.trackOrder')}</a
					>
				</div>
			</section>
		{:else if view === 'expired' || view === 'cancelled'}
			<section class="card mt-5 p-8 text-center" use:reveal={{ from: 'zoom' }}>
				<div
					class="mx-auto grid size-16 place-items-center rounded-2xl bg-slate-100 text-slate-500"
				>
					{#if view === 'expired'}<Hourglass class="size-8" />{:else}<CircleX class="size-8" />{/if}
				</div>
				<h2 class="mt-4 text-xl font-extrabold">
					{view === 'expired' ? t('pay.expiredTitle') : t('pay.cancelledTitle')}
				</h2>
				<p class="mx-auto mt-2 max-w-sm text-sm text-ink-muted">{t('pay.expiredText')}</p>
				<a href="/menu" class="btn btn-primary mt-6">{t('pay.orderAgain')}</a>
			</section>
		{:else if payment}
			<section class="card mt-5 p-5 sm:p-6" use:reveal>
				<div class="rounded-2xl bg-brand-50 px-5 py-4 text-center">
					<p class="text-sm font-medium text-ink-muted">
						{t('pay.order')}
						{order.order_number} · {t('pay.totalAmount')}
					</p>
					<p class="mt-1 text-4xl font-extrabold text-brand-600" data-testid="pay-amount">
						{formatMoney(payment.amount)}
					</p>
				</div>

				<div class="mt-5 flex justify-center">
					<div
						class="relative w-64 rounded-3xl border border-line bg-white p-3 shadow-soft sm:w-72"
					>
						<div
							class="flex items-center justify-between rounded-2xl bg-brand-600 px-4 py-2 text-white"
						>
							<span class="text-sm font-extrabold tracking-wide">KHQR</span>
							<span class="rounded-md bg-white/20 px-2 py-0.5 text-[11px] font-bold">DEMO</span>
						</div>
						<div class="relative mt-3 aspect-square">
							{#if qrSvg}
								<div
									class="size-full [&>svg]:size-full"
									role="img"
									aria-label="Demo QR code — not a real payment"
								>
									<!-- eslint-disable-next-line svelte/no-at-html-tags -- SVG generated locally by the qrcode library -->
									{@html qrSvg}
								</div>
							{:else}
								<div class="size-full animate-pulse rounded-xl bg-brand-50"></div>
							{/if}
							<span
								class="pointer-events-none absolute inset-0 grid place-items-center"
								aria-hidden="true"
							>
								<span
									class="-rotate-12 rounded-lg border-2 border-danger/70 bg-white/80 px-3 py-1 text-lg font-black tracking-widest text-danger-ink/80"
								>
									DEMO
								</span>
							</span>
						</div>
						<p class="mt-2 text-center text-[11px] text-ink-muted">{t('pay.demoQrNote')}</p>
					</div>
				</div>

				<p class="mt-5 flex items-center justify-center gap-2 text-center font-semibold">
					<Smartphone class="size-4 text-brand-600" />
					{t('pay.scan', { amount: formatMoney(payment.amount) })}
				</p>

				<div class="mt-4 grid grid-cols-2 gap-3">
					<div class="rounded-2xl border border-line p-3 text-center">
						<p class="text-xs text-ink-muted">{t('pay.status')}</p>
						<div class="mt-1"><StatusBadge status={status ?? 'pending'} kind="payment" /></div>
					</div>
					<div class="rounded-2xl border border-line p-3 text-center">
						<p class="text-xs text-ink-muted">{t('pay.expiresIn')}</p>
						<p
							class="mt-0.5 flex items-center justify-center gap-1 font-mono text-lg font-bold tabular-nums {remaining <
							60_000
								? 'text-danger-ink'
								: 'text-ink'}"
							data-testid="countdown"
						>
							<Timer class="size-4" />{formatCountdown(remaining)}
						</p>
					</div>
				</div>

				{#if error}
					<p class="mt-4 rounded-xl bg-red-50 p-3 text-sm font-medium text-danger-ink" role="alert">
						{error}
					</p>
				{/if}

				{#if demoEnabled}
					<button
						type="button"
						class="btn btn-primary btn-lg mt-5 w-full"
						disabled={confirming}
						onclick={simulate}
						data-testid="simulate-payment"
					>
						{#if confirming}<LoaderCircle class="size-4 animate-spin" />{t(
								'pay.simulating'
							)}{:else}{t('pay.simulate')}{/if}
					</button>
				{:else}
					<p class="mt-5 rounded-xl bg-slate-100 p-3 text-center text-sm text-ink-soft">
						{t('pay.demoDisabled')}
					</p>
				{/if}

				<p class="mt-4 flex items-start gap-2 rounded-2xl bg-brand-50/70 p-3 text-sm text-ink-soft">
					<Info class="mt-0.5 size-4 shrink-0 text-brand-600" />{t('pay.autoConfirm')}
				</p>
			</section>

			<details class="card mt-4 p-5" use:reveal>
				<summary class="cursor-pointer font-bold"
					>{t('checkout.summary')} · {order.items.length}</summary
				>
				<ul class="mt-3 space-y-2 text-sm">
					{#each order.items as item (item.id)}
						<li class="flex justify-between gap-3">
							<span lang={i18n.locale}
								>{i18n.locale === 'km'
									? item.food_name_km_snapshot || item.food_name_snapshot
									: item.food_name_snapshot} × {item.quantity}</span
							>
							<span class="font-semibold tabular-nums">{formatMoney(item.line_total)}</span>
						</li>
					{/each}
				</ul>
			</details>

			<div class="mt-4 text-center">
				<button
					type="button"
					class="btn btn-ghost text-danger-ink"
					onclick={() => (askCancel = true)}>{t('pay.cancelOrder')}</button
				>
			</div>
		{/if}
	{/if}
</div>

<ConfirmDialog
	bind:open={askCancel}
	title={t('pay.cancelOrder')}
	message={t('pay.cancelConfirm')}
	confirmLabel={t('pay.cancelOrder')}
	busy={cancelling}
	onconfirm={cancel}
/>
