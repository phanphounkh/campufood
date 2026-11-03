<script lang="ts">
	import type { Snippet } from 'svelte';
	import { t } from '#lib/i18n/index.svelte.ts';
	import type { ChartPoint } from './scale.ts';

	/**
	 * Shared shell for single-series charts: title, keyboard navigation, a live region that
	 * announces the focused value, and a screen-reader data table (the "table view").
	 */
	let {
		title,
		subtitle,
		points,
		formatValue,
		active = $bindable(null),
		children
	}: {
		title: string;
		subtitle?: string;
		points: ChartPoint[];
		formatValue: (v: number) => string;
		active?: number | null;
		children: Snippet;
	} = $props();

	const id = `chart-${Math.random().toString(36).slice(2, 9)}`;

	function onkeydown(event: KeyboardEvent) {
		if (!points.length) return;
		const last = points.length - 1;
		const current = active ?? last;
		const moves: Record<string, number> = {
			ArrowLeft: Math.max(0, current - 1),
			ArrowRight: Math.min(last, current + 1),
			Home: 0,
			End: last
		};
		if (event.key === 'Escape') {
			active = null;
		} else if (event.key in moves) {
			event.preventDefault();
			active = moves[event.key];
		}
	}
</script>

<figure class="m-0">
	<figcaption class="mb-4">
		<h3 id="{id}-title" class="text-base font-bold text-ink">{title}</h3>
		{#if subtitle}<p class="text-xs text-ink-muted">{subtitle}</p>{/if}
	</figcaption>
	<!-- Focusable so keyboard users can step through values with the arrow keys; the live region
	     below announces each one. -->
	<!-- svelte-ignore a11y_no_noninteractive_tabindex, a11y_no_noninteractive_element_interactions -->
	<div
		role="group"
		tabindex="0"
		aria-labelledby="{id}-title"
		aria-describedby="{id}-hint"
		class="relative rounded-xl outline-none focus-visible:ring-4 focus-visible:ring-brand-100"
		{onkeydown}
		onfocus={() => {
			if (active === null && points.length) active = points.length - 1;
		}}
		onblur={() => (active = null)}
	>
		{@render children()}
	</div>
	<p id="{id}-hint" class="sr-only">{t('admin.chart.keyboardHint')}</p>
	<p class="sr-only" aria-live="polite">
		{#if active !== null && points[active]}
			{points[active].fullLabel}: {formatValue(points[active].value)}
			{points[active].detail ?? ''}
		{/if}
	</p>
	<table class="sr-only">
		<caption>{t('admin.chart.table', { title })}</caption>
		<tbody>
			{#each points as point, i (i)}
				<tr>
					<th scope="row">{point.fullLabel}</th>
					<td>{formatValue(point.value)}</td>
					{#if point.detail}<td>{point.detail}</td>{/if}
				</tr>
			{/each}
		</tbody>
	</table>
</figure>
