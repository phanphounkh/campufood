/**
 * Pointer-based drag and drop that works with mouse, touch and pen.
 *
 * Why not HTML5 drag-and-drop or a sortable-list library? Food is *copied* into the cart (the
 * menu never changes), it must work on touch screens, and it needs a custom preview. Dragging
 * is an enhancement only: every card also has an "Add to cart" button, and the drag handle is
 * a real button that adds the dish when activated with Enter/Space.
 */
import type { Food } from '#lib/types/api.ts';

const DRAG_THRESHOLD = 6;

class DragState {
	food = $state<Food | null>(null);
	x = $state(0);
	y = $state(0);
	activeZone = $state<HTMLElement | null>(null);
	zones = new Set<HTMLElement>();
	/** Set by the last drop so the receiving zone can animate. */
	lastDropAt = $state(0);

	get dragging(): boolean {
		return this.food !== null;
	}
}

export const drag = new DragState();

function zoneAt(x: number, y: number): HTMLElement | null {
	for (const zone of drag.zones) {
		if (!zone.isConnected || zone.offsetParent === null) continue; // hidden zones
		const r = zone.getBoundingClientRect();
		if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) return zone;
	}
	return null;
}

export interface DraggableParams {
	food: Food;
	disabled?: boolean;
	onDrop: (food: Food) => void;
}

/**
 * `use:draggableFood={{ food, onDrop }}` on a food card. With a mouse the whole card can be
 * dragged; with touch or a pen only `[data-drag-handle]` starts a drag, so scrolling still works.
 */
export function draggableFood(node: HTMLElement, initial: DraggableParams) {
	let params = initial;
	let startX = 0;
	let startY = 0;
	let pointerId: number | null = null;
	let active = false;

	function cleanup() {
		window.removeEventListener('pointermove', onMove);
		window.removeEventListener('pointerup', onUp);
		window.removeEventListener('pointercancel', onCancel);
		window.removeEventListener('keydown', onKey);
		document.documentElement.classList.remove('is-dragging');
		pointerId = null;
		active = false;
		drag.food = null;
		drag.activeZone = null;
	}

	function onDown(event: PointerEvent) {
		if (params.disabled || event.button !== 0) return;
		const target = event.target as HTMLElement;
		const onHandle = !!target.closest('[data-drag-handle]');
		if (event.pointerType !== 'mouse' && !onHandle) return;
		if (!onHandle && target.closest('button:not([data-drag-ok]), a, input, select, textarea'))
			return;
		if (onHandle) event.preventDefault();
		pointerId = event.pointerId;
		startX = event.clientX;
		startY = event.clientY;
		window.addEventListener('pointermove', onMove);
		window.addEventListener('pointerup', onUp);
		window.addEventListener('pointercancel', onCancel);
	}

	function onMove(event: PointerEvent) {
		if (event.pointerId !== pointerId) return;
		if (!active) {
			if (Math.hypot(event.clientX - startX, event.clientY - startY) < DRAG_THRESHOLD) return;
			active = true;
			drag.food = params.food;
			document.documentElement.classList.add('is-dragging');
			window.addEventListener('keydown', onKey);
		}
		event.preventDefault();
		drag.x = event.clientX;
		drag.y = event.clientY;
		drag.activeZone = zoneAt(event.clientX, event.clientY);
	}

	function onUp(event: PointerEvent) {
		if (event.pointerId !== pointerId) return;
		if (active) {
			const zone = zoneAt(event.clientX, event.clientY);
			if (zone) {
				params.onDrop(params.food);
				drag.lastDropAt = Date.now();
			}
			// Swallow the click that follows a drag so the card doesn't open its details.
			window.addEventListener('click', swallowClick, { capture: true, once: true });
			setTimeout(() => window.removeEventListener('click', swallowClick, { capture: true }), 0);
		}
		cleanup();
	}

	function onCancel(event: PointerEvent) {
		if (event.pointerId === pointerId) cleanup();
	}

	function onKey(event: KeyboardEvent) {
		if (event.key === 'Escape') cleanup();
	}

	function swallowClick(event: MouseEvent) {
		event.stopPropagation();
		event.preventDefault();
	}

	node.addEventListener('pointerdown', onDown);
	return {
		update(next: DraggableParams) {
			params = next;
		},
		destroy() {
			node.removeEventListener('pointerdown', onDown);
			if (pointerId !== null) cleanup();
		}
	};
}

/** `use:dropZone` marks an element (e.g. the cart) as a place food can be dropped. */
export function dropZone(node: HTMLElement) {
	drag.zones.add(node);
	return {
		destroy() {
			drag.zones.delete(node);
		}
	};
}
