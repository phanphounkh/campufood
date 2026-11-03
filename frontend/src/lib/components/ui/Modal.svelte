<script lang="ts">
	import type { Snippet } from 'svelte';
	import X from '@lucide/svelte/icons/x';
	import { t } from '#lib/i18n/index.svelte.ts';

	/**
	 * Accessible modal built on the native <dialog> element: focus trapping, Escape to close
	 * and inert background come from the browser.
	 */
	let {
		open = $bindable(false),
		title,
		description,
		size = 'md',
		variant = 'center',
		onclose,
		children,
		footer
	}: {
		open?: boolean;
		title: string;
		description?: string;
		size?: 'sm' | 'md' | 'lg' | 'xl';
		variant?: 'center' | 'drawer';
		onclose?: () => void;
		children: Snippet;
		footer?: Snippet;
	} = $props();

	let dialog: HTMLDialogElement | undefined = $state();
	const widths = { sm: 'max-w-md', md: 'max-w-lg', lg: 'max-w-2xl', xl: 'max-w-4xl' };

	$effect(() => {
		if (!dialog) return;
		if (open && !dialog.open) dialog.showModal();
		if (!open && dialog.open) dialog.close();
	});

	function handleClose() {
		open = false;
		onclose?.();
	}

	function onBackdropClick(event: MouseEvent) {
		if (event.target === dialog) handleClose();
	}
</script>

<dialog
	bind:this={dialog}
	onclose={handleClose}
	onclick={onBackdropClick}
	aria-labelledby="modal-title"
	class="m-0 max-h-none max-w-none bg-transparent p-0 backdrop:bg-ink/40 backdrop:backdrop-blur-sm open:flex
		{variant === 'drawer'
		? 'ml-auto h-dvh w-full sm:w-[28rem]'
		: 'h-dvh w-full items-end justify-center sm:items-center sm:p-4'}"
>
	{#if open}
		<div
			class="flex w-full flex-col bg-white shadow-2xl
				{variant === 'drawer'
				? 'h-full animate-slide-in-right'
				: `max-h-[92dvh] animate-fade-up rounded-t-3xl sm:rounded-3xl ${widths[size]}`}"
		>
			<header class="flex items-start justify-between gap-4 border-b border-line px-5 py-4 sm:px-6">
				<div>
					<h2 id="modal-title" class="text-lg font-bold text-ink">{title}</h2>
					{#if description}
						<p class="mt-0.5 text-sm text-ink-muted">{description}</p>
					{/if}
				</div>
				<button
					type="button"
					class="icon-btn -mr-2 size-9"
					aria-label={t('common.close')}
					onclick={handleClose}
				>
					<X class="size-5" />
				</button>
			</header>
			<div class="flex-1 overflow-y-auto px-5 py-5 sm:px-6">
				{@render children()}
			</div>
			{#if footer}
				<footer class="flex flex-wrap justify-end gap-2 border-t border-line px-5 py-4 sm:px-6">
					{@render footer()}
				</footer>
			{/if}
		</div>
	{/if}
</dialog>
