<script lang="ts">
	import { fly } from 'svelte/transition';
	import { flip } from 'svelte/animate';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import CircleAlert from '@lucide/svelte/icons/circle-alert';
	import Info from '@lucide/svelte/icons/info';
	import X from '@lucide/svelte/icons/x';
	import { toasts } from '#lib/stores/toast.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';

	const icons = { success: CircleCheck, error: CircleAlert, info: Info };
	const tones = {
		success: 'text-success-ink',
		error: 'text-danger-ink',
		info: 'text-brand-600'
	};
</script>

<div
	class="pointer-events-none fixed inset-x-0 top-3 z-[100] flex flex-col items-center gap-2 px-4 sm:top-auto sm:right-4 sm:bottom-4 sm:left-auto sm:items-end"
	aria-live="polite"
	aria-atomic="false"
>
	{#each toasts.items as item (item.id)}
		{@const Icon = icons[item.kind]}
		<div
			animate:flip={{ duration: 200 }}
			in:fly={{ y: 12, duration: 220 }}
			out:fly={{ x: 40, duration: 180 }}
			class="pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-2xl border border-line bg-white/95 px-4 py-3 text-sm shadow-lift backdrop-blur"
			role={item.kind === 'error' ? 'alert' : 'status'}
		>
			<Icon class="mt-0.5 size-5 shrink-0 {tones[item.kind]}" aria-hidden="true" />
			<p class="flex-1 font-medium text-ink">{item.message}</p>
			<button
				type="button"
				class="-m-1 rounded-lg p-1 text-ink-muted hover:bg-brand-50 hover:text-ink"
				aria-label={t('common.close')}
				onclick={() => toasts.dismiss(item.id)}
			>
				<X class="size-4" />
			</button>
		</div>
	{/each}
</div>
