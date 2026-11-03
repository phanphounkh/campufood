<script lang="ts">
	import type { OrderStatus, PaymentStatus } from '#lib/types/api.ts';
	import { t } from '#lib/i18n/index.svelte.ts';

	let {
		status,
		kind = 'order',
		size = 'sm'
	}: {
		status: OrderStatus | PaymentStatus;
		kind?: 'order' | 'payment';
		size?: 'sm' | 'md';
	} = $props();

	const styles: Record<string, string> = {
		pending_payment: 'bg-amber-50 text-amber-800 ring-amber-200',
		pending: 'bg-amber-50 text-amber-800 ring-amber-200',
		confirmed: 'bg-brand-50 text-brand-700 ring-brand-200',
		preparing: 'bg-sky-50 text-sky-800 ring-sky-200',
		ready: 'bg-emerald-50 text-emerald-800 ring-emerald-200',
		completed: 'bg-green-50 text-green-800 ring-green-200',
		paid: 'bg-green-50 text-green-800 ring-green-200',
		cancelled: 'bg-slate-100 text-slate-700 ring-slate-200',
		expired: 'bg-slate-100 text-slate-700 ring-slate-200',
		failed: 'bg-red-50 text-red-700 ring-red-200',
		refunded: 'bg-rose-50 text-rose-700 ring-rose-200'
	};
	const dots: Record<string, string> = {
		pending_payment: 'bg-amber-500',
		pending: 'bg-amber-500',
		confirmed: 'bg-brand-600',
		preparing: 'bg-sky-500 animate-pulse',
		ready: 'bg-emerald-500 animate-pulse',
		completed: 'bg-green-600',
		paid: 'bg-green-600',
		cancelled: 'bg-slate-400',
		expired: 'bg-slate-400',
		failed: 'bg-red-500',
		refunded: 'bg-rose-500'
	};
</script>

<span
	class="inline-flex items-center gap-1.5 rounded-full font-semibold whitespace-nowrap ring-1 ring-inset
		{size === 'md' ? 'px-3 py-1 text-sm' : 'px-2.5 py-0.5 text-xs'} {styles[status] ??
		styles.cancelled}"
>
	<span class="size-1.5 rounded-full {dots[status] ?? 'bg-slate-400'}" aria-hidden="true"></span>
	{t(`${kind === 'order' ? 'status' : 'payment'}.${status}`)}
</span>
