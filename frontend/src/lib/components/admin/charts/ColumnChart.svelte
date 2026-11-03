<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import Tooltip from './Tooltip.svelte';
	import { columnPath, labelIndices, niceTicks, type ChartPoint } from './scale.ts';

	/** Single-series column chart; each column (its whole band) is the hover target. */
	let {
		title,
		subtitle,
		points,
		formatValue,
		formatAxis,
		emptyText,
		height = 240,
		minStep = 1
	}: {
		title: string;
		subtitle?: string;
		points: ChartPoint[];
		formatValue: (v: number) => string;
		formatAxis: (v: number) => string;
		emptyText?: string;
		height?: number;
		minStep?: number;
	} = $props();

	let width = $state(0);
	let active = $state<number | null>(null);

	const pad = { top: 22, right: 8, bottom: 28, left: 52 };
	const plotW = $derived(Math.max(0, width - pad.left - pad.right));
	const plotH = $derived(height - pad.top - pad.bottom);
	const baseline = $derived(pad.top + plotH);
	const max = $derived(Math.max(0, ...points.map((p) => p.value)));
	const ticks = $derived(niceTicks(max, 4, minStep));
	const top = $derived(ticks[ticks.length - 1] || 1);
	const band = $derived(points.length ? plotW / points.length : 0);
	const barW = $derived(Math.max(2, Math.min(24, band * 0.68)));
	const maxIndex = $derived(max > 0 ? points.findIndex((p) => p.value === max) : -1);
	const shown = $derived(labelIndices(points.length, plotW, 52));

	const y = (v: number) => pad.top + plotH - (v / top) * plotH;
	const cx = (i: number) => pad.left + band * i + band / 2;
</script>

<ChartFrame {title} {subtitle} {points} {formatValue} bind:active>
	<div class="relative" bind:clientWidth={width} style="height: {height}px">
		{#if width > 0}
			<svg {width} {height} class="block overflow-visible" aria-hidden="true">
				{#each ticks as tick (tick)}
					<line
						x1={pad.left}
						x2={width - pad.right}
						y1={y(tick)}
						y2={y(tick)}
						class="stroke-line"
						stroke-width="1"
					/>
					<text
						x={pad.left - 8}
						y={y(tick)}
						dy="0.32em"
						text-anchor="end"
						class="fill-ink-muted text-[11px] tabular-nums"
					>
						{formatAxis(tick)}
					</text>
				{/each}
				{#each points as point, i (i)}
					<path
						d={columnPath(cx(i) - barW / 2, y(point.value), barW, baseline)}
						class="transition-colors {active === i ? 'fill-brand-800' : 'fill-brand-600'}"
					/>
					{#if shown.has(i)}
						<text x={cx(i)} y={height - 8} text-anchor="middle" class="fill-ink-muted text-[11px]"
							>{point.label}</text
						>
					{/if}
					{#if i === maxIndex && active === null}
						<text
							x={cx(i)}
							y={y(point.value) - 6}
							text-anchor="middle"
							class="fill-ink text-[11px] font-semibold tabular-nums"
						>
							{formatValue(point.value)}
						</text>
					{/if}
					<rect
						x={pad.left + band * i}
						y={pad.top}
						width={band}
						height={plotH}
						fill="transparent"
						role="presentation"
						onpointerenter={() => (active = i)}
						onpointerleave={() => (active = null)}
					/>
				{/each}
			</svg>
			{#if max === 0 && emptyText}
				<p
					class="pointer-events-none absolute inset-x-0 top-1/3 text-center text-sm font-medium text-ink-muted"
				>
					{emptyText}
				</p>
			{/if}
			{#if active !== null && points[active]}
				<Tooltip
					x={cx(active)}
					y={y(points[active].value)}
					{width}
					value={formatValue(points[active].value)}
					label={points[active].fullLabel}
					detail={points[active].detail}
				/>
			{/if}
		{/if}
	</div>
</ChartFrame>
