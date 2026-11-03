<script lang="ts">
	import FoodImage from '#lib/components/ui/FoodImage.svelte';
	import { drag } from '#lib/stores/dnd.svelte.ts';
	import { i18n } from '#lib/i18n/index.svelte.ts';
	import { formatMoney } from '#lib/utils/money.ts';
</script>

{#if drag.food}
	<div
		class="pointer-events-none fixed top-0 left-0 z-[90] w-52 rounded-2xl border border-brand-200 bg-white p-2 shadow-2xl"
		style="transform: translate3d({drag.x}px, {drag.y}px, 0) translate(-50%, -60%) rotate({drag.activeZone
			? 0
			: -4}deg) scale({drag.activeZone ? 0.9 : 1});"
		aria-hidden="true"
	>
		<FoodImage
			src={drag.food.image_url}
			alt=""
			class="aspect-[4/3] w-full rounded-xl"
			loading="eager"
		/>
		<div class="flex items-center justify-between px-1 pt-2 pb-0.5">
			<span class="truncate text-sm font-bold">{i18n.pick(drag.food, 'name')}</span>
			<span class="text-sm font-extrabold text-brand-600">{formatMoney(drag.food.price)}</span>
		</div>
	</div>
{/if}

<!-- Screen reader announcement of drag state -->
<div class="sr-only" aria-live="assertive">
	{#if drag.food}{i18n.pick(drag.food, 'name')}{/if}
</div>

<style>
	:global(html.is-dragging),
	:global(html.is-dragging *) {
		cursor: grabbing !important;
		user-select: none !important;
	}
</style>
