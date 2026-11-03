<script lang="ts">
	import { t } from '#lib/i18n/index.svelte.ts';

	let {
		subtitle,
		variant = 'light',
		href = '/'
	}: { subtitle?: string; variant?: 'light' | 'dark'; href?: string | null } = $props();
</script>

{#snippet content()}
	<span
		class="grid size-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-[0_6px_16px_-6px_rgb(100_37_216/0.7)]"
		aria-hidden="true"
	>
		<svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2.2">
			<path d="M7 3v8a2 2 0 0 0 2 2h0a2 2 0 0 0 2-2V3M9 13v8" stroke-linecap="round" />
			<path
				d="M17 21V3c-2 1.5-3 4-3 7 0 2 1 3 3 3"
				stroke-linecap="round"
				stroke-linejoin="round"
			/>
		</svg>
	</span>
	<span class="flex flex-col leading-none">
		<span
			class="text-lg font-extrabold tracking-tight {variant === 'dark' ? 'text-white' : 'text-ink'}"
			>Campus<span class={variant === 'dark' ? 'text-brand-300' : 'text-brand-600'}>Eats</span
			></span
		>
		<span
			class="mt-1 text-[11px] font-medium {variant === 'dark' ? 'text-white/60' : 'text-ink-muted'}"
			>{subtitle ?? t('brand.tagline')}</span
		>
	</span>
{/snippet}

{#if href}
	<a {href} class="flex items-center gap-2.5 rounded-xl" aria-label="CampusEats">
		{@render content()}
	</a>
{:else}
	<div class="flex items-center gap-2.5">{@render content()}</div>
{/if}
