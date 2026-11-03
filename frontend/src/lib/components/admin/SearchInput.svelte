<script lang="ts">
	import Search from '@lucide/svelte/icons/search';
	import X from '@lucide/svelte/icons/x';
	import { t } from '#lib/i18n/index.svelte.ts';

	/** Search box that reports its value after the user pauses typing. */
	let {
		value = '',
		placeholder,
		delay = 300,
		class: className = '',
		onsearch
	}: {
		value?: string;
		placeholder: string;
		delay?: number;
		class?: string;
		onsearch: (value: string) => void;
	} = $props();

	// svelte-ignore state_referenced_locally
	let text = $state(value);
	let timer: ReturnType<typeof setTimeout> | undefined;

	function schedule() {
		clearTimeout(timer);
		timer = setTimeout(() => onsearch(text.trim()), delay);
	}

	function clear() {
		text = '';
		clearTimeout(timer);
		onsearch('');
	}
</script>

<div class="relative {className}">
	<Search
		class="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-ink-muted"
		aria-hidden="true"
	/>
	<input
		type="search"
		class="w-full py-2 pr-9 pl-9 text-sm"
		{placeholder}
		aria-label={placeholder}
		bind:value={text}
		oninput={schedule}
		onkeydown={(e) => {
			if (e.key === 'Enter') {
				clearTimeout(timer);
				onsearch(text.trim());
			}
		}}
	/>
	{#if text}
		<button
			type="button"
			class="absolute top-1/2 right-2 grid size-6 -translate-y-1/2 place-items-center rounded-md text-ink-muted hover:bg-brand-50 hover:text-ink"
			aria-label={t('admin.searchClear')}
			onclick={clear}
		>
			<X class="size-3.5" />
		</button>
	{/if}
</div>
