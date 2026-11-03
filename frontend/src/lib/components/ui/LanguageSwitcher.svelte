<script lang="ts">
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { LOCALES, type Locale } from '#lib/i18n/locales.ts';

	let { tone = 'light' }: { tone?: 'light' | 'dark' } = $props();

	const labels: Record<Locale, string> = { en: 'EN', km: 'KH' };
	const names: Record<Locale, string> = { en: 'English', km: 'ភាសាខ្មែរ' };
</script>

<div
	role="group"
	aria-label={t('lang.switch')}
	class="inline-flex items-center rounded-xl p-1 text-xs font-bold {tone === 'dark'
		? 'bg-white/10'
		: 'border border-line bg-white'}"
>
	{#each LOCALES as locale (locale)}
		{@const active = i18n.locale === locale}
		<button
			type="button"
			class="rounded-lg px-2.5 py-1.5 transition {active
				? 'bg-brand-600 text-white shadow-sm'
				: tone === 'dark'
					? 'text-white/70 hover:text-white'
					: 'text-ink-muted hover:text-brand-700'}"
			aria-pressed={active}
			title={names[locale]}
			lang={locale}
			onclick={() => i18n.setLocale(locale)}
		>
			{labels[locale]}
		</button>
	{/each}
</div>
