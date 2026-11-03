<script lang="ts">
	import ChevronLeft from '@lucide/svelte/icons/chevron-left';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import type { ResolvedPathname } from '$app/types';
	import { t } from '#lib/i18n/index.svelte.ts';

	let {
		page,
		pageSize,
		total,
		href
	}: { page: number; pageSize: number; total: number; href: (page: number) => ResolvedPathname } =
		$props();

	const pages = $derived(Math.max(1, Math.ceil(total / pageSize)));
	const from = $derived(total === 0 ? 0 : (page - 1) * pageSize + 1);
	const to = $derived(Math.min(total, page * pageSize));
</script>

{#if total > 0}
	<nav
		class="flex flex-wrap items-center justify-between gap-3 border-t border-line px-4 py-3 text-sm"
		aria-label={t('admin.pagination')}
	>
		<p class="text-ink-muted">{t('admin.showing', { from, to, total })}</p>
		{#if pages > 1}
			<div class="flex items-center gap-1">
				<a
					href={href(page - 1)}
					class="btn btn-secondary btn-sm {page <= 1 ? 'pointer-events-none opacity-40' : ''}"
					aria-disabled={page <= 1}
					tabindex={page <= 1 ? -1 : undefined}
				>
					<ChevronLeft class="size-4" />{t('admin.prev')}
				</a>
				<span class="px-2 font-semibold text-ink tabular-nums">{page} / {pages}</span>
				<a
					href={href(page + 1)}
					class="btn btn-secondary btn-sm {page >= pages ? 'pointer-events-none opacity-40' : ''}"
					aria-disabled={page >= pages}
					tabindex={page >= pages ? -1 : undefined}
				>
					{t('admin.next')}<ChevronRight class="size-4" />
				</a>
			</div>
		{/if}
	</nav>
{/if}
