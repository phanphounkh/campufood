<script lang="ts">
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import { refreshAll } from '$app/navigation';
	import { t } from '#lib/i18n/index.svelte.ts';

	let { message, onretry }: { message: string; onretry?: () => void | Promise<void> } = $props();
	let busy = $state(false);

	async function retry() {
		busy = true;
		try {
			await (onretry ? onretry() : refreshAll());
		} finally {
			busy = false;
		}
	}
</script>

<div class="card flex flex-col items-center px-6 py-12 text-center" role="alert">
	<div class="grid size-14 place-items-center rounded-2xl bg-red-50 text-danger-ink">
		<TriangleAlert class="size-7" />
	</div>
	<h2 class="mt-4 text-base font-bold text-ink">{t('admin.loadError')}</h2>
	<p class="mt-1 max-w-sm text-sm text-ink-muted">{message}</p>
	<button type="button" class="btn btn-secondary mt-5" onclick={retry} disabled={busy}>
		<RefreshCw class="size-4 {busy ? 'animate-spin' : ''}" />
		{t('admin.retry')}
	</button>
</div>
