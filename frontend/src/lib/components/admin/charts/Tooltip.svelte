<script lang="ts">
	/** Chart tooltip: value first (strong), label second. Positioned in container pixels. */
	let {
		x,
		y,
		width,
		value,
		label,
		detail
	}: { x: number; y: number; width: number; value: string; label: string; detail?: string } =
		$props();

	const half = 80;
	const left = $derived(Math.min(Math.max(x, half), Math.max(half, width - half)));
</script>

<div
	class="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-xl border border-line bg-white px-3 py-2 text-left shadow-lift"
	style="left: {left}px; top: {Math.max(y - 12, 0)}px"
	aria-hidden="true"
>
	<p class="flex items-center gap-2 text-sm font-bold whitespace-nowrap text-ink tabular-nums">
		<span class="h-0.5 w-3 rounded-full bg-brand-600"></span>{value}
	</p>
	<p class="mt-0.5 text-xs whitespace-nowrap text-ink-muted">{label}</p>
	{#if detail}<p class="text-xs whitespace-nowrap text-ink-muted">{detail}</p>{/if}
</div>
