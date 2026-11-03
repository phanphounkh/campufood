<script lang="ts">
	import Minus from '@lucide/svelte/icons/minus';
	import Plus from '@lucide/svelte/icons/plus';
	import { t } from '#lib/i18n/index.svelte.ts';

	let {
		value,
		max,
		name,
		size = 'md',
		ondecrement,
		onincrement
	}: {
		value: number;
		max: number;
		name: string;
		size?: 'sm' | 'md';
		ondecrement: () => void;
		onincrement: () => void;
	} = $props();

	const btn = $derived(size === 'sm' ? 'size-7' : 'size-8');
</script>

<div class="inline-flex items-center rounded-xl border border-line bg-white p-0.5">
	<button
		type="button"
		class="grid {btn} place-items-center rounded-lg text-ink-soft transition hover:bg-brand-50 hover:text-brand-700"
		aria-label={t('cart.decrease', { name })}
		onclick={ondecrement}
	>
		<Minus class="size-3.5" />
	</button>
	<output class="w-7 text-center text-sm font-bold text-ink tabular-nums" aria-live="polite"
		>{value}</output
	>
	<button
		type="button"
		class="grid {btn} place-items-center rounded-lg text-ink-soft transition hover:bg-brand-50 hover:text-brand-700 disabled:opacity-40"
		aria-label={t('cart.increase', { name })}
		disabled={value >= max}
		onclick={onincrement}
	>
		<Plus class="size-3.5" />
	</button>
</div>
