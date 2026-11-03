<script lang="ts">
	import type { Snippet } from 'svelte';
	import Modal from './Modal.svelte';
	import { t } from '#lib/i18n/index.svelte.ts';

	let {
		open = $bindable(false),
		title,
		message,
		confirmLabel,
		tone = 'danger',
		busy = false,
		onconfirm,
		children
	}: {
		open?: boolean;
		title: string;
		message?: string;
		confirmLabel: string;
		tone?: 'danger' | 'primary';
		busy?: boolean;
		onconfirm: () => void | Promise<void>;
		children?: Snippet;
	} = $props();
</script>

<Modal bind:open {title} size="sm">
	{#if message}<p class="text-sm text-ink-soft">{message}</p>{/if}
	{@render children?.()}
	{#snippet footer()}
		<button type="button" class="btn btn-secondary" onclick={() => (open = false)}>
			{t('common.cancel')}
		</button>
		<button
			type="button"
			class="btn {tone === 'danger' ? 'btn-danger' : 'btn-primary'}"
			disabled={busy}
			onclick={onconfirm}
		>
			{confirmLabel}
		</button>
	{/snippet}
</Modal>
