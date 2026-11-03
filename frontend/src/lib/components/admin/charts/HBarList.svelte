<script lang="ts">
	/**
	 * Horizontal bars for a handful of categories. Every bar carries its value at the tip, so the
	 * values are always visible (no hover needed). One hue: the bars compare magnitudes only.
	 */
	let {
		title,
		subtitle,
		rows
	}: {
		title: string;
		subtitle?: string;
		rows: { label: string; value: number; display?: string }[];
	} = $props();

	const max = $derived(Math.max(1, ...rows.map((r) => r.value)));
</script>

<figure class="m-0">
	<figcaption class="mb-4">
		<h3 class="text-base font-bold text-ink">{title}</h3>
		{#if subtitle}<p class="text-xs text-ink-muted">{subtitle}</p>{/if}
	</figcaption>
	<ul class="space-y-3">
		{#each rows as row (row.label)}
			<li class="grid grid-cols-[minmax(0,8.5rem)_1fr] items-center gap-3 text-sm">
				<span class="truncate text-ink-soft" title={row.label}>{row.label}</span>
				<span class="flex min-w-0 items-center gap-2">
					{#if row.value > 0}
						<span
							class="h-3 shrink-0 rounded-r-[4px] bg-brand-600"
							style="width: max(3px, calc((100% - 3rem) * {row.value / max}))"
						></span>
					{:else}
						<span class="h-3 w-px shrink-0 bg-line"></span>
					{/if}
					<span class="font-semibold text-ink tabular-nums">{row.display ?? row.value}</span>
				</span>
			</li>
		{/each}
	</ul>
</figure>
