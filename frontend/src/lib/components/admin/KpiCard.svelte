<script lang="ts">
	import type { Component, Snippet } from 'svelte';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import TrendingDown from '@lucide/svelte/icons/trending-down';
	import Minus from '@lucide/svelte/icons/minus';
	import { t } from '#lib/i18n/index.svelte.ts';

	/** Stat tile: label · value · optional signed delta vs a named period. */
	let {
		label,
		value,
		icon: Icon,
		changePct,
		comparison,
		hint,
		tone = 'brand',
		children
	}: {
		label: string;
		value: string;
		icon: Component<{ class?: string }>;
		changePct?: number | null;
		comparison?: string;
		hint?: string;
		tone?: 'brand' | 'amber' | 'green' | 'sky' | 'rose';
		children?: Snippet;
	} = $props();

	const tones = {
		brand: 'bg-brand-50 text-brand-600',
		amber: 'bg-amber-50 text-amber-600',
		green: 'bg-green-50 text-green-600',
		sky: 'bg-sky-50 text-sky-600',
		rose: 'bg-rose-50 text-rose-600'
	};
	const showDelta = $derived(changePct !== undefined);
</script>

<div class="card flex flex-col p-5">
	<div class="flex items-start justify-between gap-3">
		<p class="text-sm font-semibold text-ink-muted">{label}</p>
		<span
			class="grid size-9 shrink-0 place-items-center rounded-xl {tones[tone]}"
			aria-hidden="true"
		>
			<Icon class="size-[18px]" />
		</span>
	</div>
	<p class="mt-2 text-[1.75rem] leading-tight font-extrabold tracking-tight text-ink">{value}</p>
	{#if showDelta}
		<p class="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs">
			{#if changePct === null || changePct === undefined}
				<span class="text-ink-muted">{t('admin.kpi.noPrevious')}</span>
			{:else if changePct > 0}
				<span
					class="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 font-bold text-green-700"
				>
					<TrendingUp class="size-3.5" />{t('admin.kpi.up', { pct: changePct })}
				</span>
				<span class="text-ink-muted">{comparison}</span>
			{:else if changePct < 0}
				<span
					class="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 font-bold text-red-700"
				>
					<TrendingDown class="size-3.5" />{t('admin.kpi.down', { pct: Math.abs(changePct) })}
				</span>
				<span class="text-ink-muted">{comparison}</span>
			{:else}
				<span
					class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 font-bold text-slate-600"
				>
					<Minus class="size-3.5" />{t('admin.kpi.flat')}
				</span>
				<span class="text-ink-muted">{comparison}</span>
			{/if}
		</p>
	{/if}
	{#if hint}<p class="mt-1.5 text-xs text-ink-muted">{hint}</p>{/if}
	{@render children?.()}
</div>
