<script lang="ts">
	import ChartFrame from './ChartFrame.svelte';
	import Tooltip from './Tooltip.svelte';
	import { labelIndices, niceTicks, type ChartPoint } from './scale.ts';

	/** Single-series line + area chart with a snapping crosshair. */
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

	const pad = { top: 14, right: 14, bottom: 28, left: 52 };
	const plotW = $derived(Math.max(0, width - pad.left - pad.right));
	const plotH = $derived(height - pad.top - pad.bottom);
	const baseline = $derived(pad.top + plotH);
	const max = $derived(Math.max(0, ...points.map((p) => p.value)));
	const ticks = $derived(niceTicks(max, 4, minStep));
	const top = $derived(ticks[ticks.length - 1] || 1);
	const isEmpty = $derived(max === 0);

	const x = (i: number) =>
		pad.left + (points.length <= 1 ? plotW / 2 : (i * plotW) / (points.length - 1));
	const y = (v: number) => pad.top + plotH - (v / top) * plotH;

	const linePath = $derived(
		points.map((p, i) => `${i ? 'L' : 'M'}${x(i)},${y(p.value)}`).join(' ')
	);
	const areaPath = $derived(
		points.length ? `${linePath} L${x(points.length - 1)},${baseline} L${x(0)},${baseline} Z` : ''
	);
	const shown = $derived(labelIndices(points.length, plotW));

	function onpointermove(event: PointerEvent) {
		const rect = (event.currentTarget as SVGRectElement).getBoundingClientRect();
		const px = event.clientX - rect.left;
		const step = points.length > 1 ? plotW / (points.length - 1) : plotW;
		active = Math.min(points.length - 1, Math.max(0, Math.round(px / (step || 1))));
	}
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
					{#if shown.has(i)}
						<text
							x={x(i)}
							y={height - 8}
							text-anchor={i === 0 && points.length > 1
								? 'start'
								: i === points.length - 1 && points.length > 1
									? 'end'
									: 'middle'}
							class="fill-ink-muted text-[11px]"
						>
							{point.label}
						</text>
					{/if}
				{/each}
				<path d={areaPath} class="fill-brand-600" fill-opacity="0.1" />
				<path
					d={linePath}
					fill="none"
					class="stroke-brand-600"
					stroke-width="2"
					stroke-linejoin="round"
					stroke-linecap="round"
				/>
				{#if points.length}
					<circle
						cx={x(points.length - 1)}
						cy={y(points[points.length - 1].value)}
						r="4"
						class="fill-brand-600 stroke-white"
						stroke-width="2"
					/>
				{/if}
				{#if active !== null && points[active]}
					<line
						x1={x(active)}
						x2={x(active)}
						y1={pad.top}
						y2={baseline}
						class="stroke-ink-muted"
						stroke-opacity="0.35"
						stroke-width="1"
					/>
					<circle
						cx={x(active)}
						cy={y(points[active].value)}
						r="5"
						class="fill-brand-600 stroke-white"
						stroke-width="2"
					/>
				{/if}
				<rect
					x={pad.left - 8}
					y={pad.top}
					width={plotW + 16}
					height={plotH}
					fill="transparent"
					role="presentation"
					{onpointermove}
					onpointerleave={() => (active = null)}
				/>
			</svg>
			{#if isEmpty && emptyText}
				<p
					class="pointer-events-none absolute inset-x-0 top-1/3 text-center text-sm font-medium text-ink-muted"
				>
					{emptyText}
				</p>
			{/if}
			{#if active !== null && points[active]}
				<Tooltip
					x={x(active)}
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
