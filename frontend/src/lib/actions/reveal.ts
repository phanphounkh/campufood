import type { Action } from 'svelte/action';

/**
 * Scroll reveal: `<div use:reveal>` fades the element in as it scrolls into view.
 *
 * - Content already on screen when the server-rendered page hydrates is left alone, so the
 *   first paint never flashes. Anything mounted later (client navigation, filtered lists,
 *   data that arrives after load) animates even if it is already in view.
 * - Elements that enter the viewport together (a row of cards) are staggered left to right.
 * - Reveals once. Skipped entirely for `prefers-reduced-motion` and without IntersectionObserver.
 * - Uses the Web Animations API on `transform`/`opacity` only for the duration of the reveal,
 *   so the element's own transitions and Tailwind `translate`/`scale` utilities are untouched.
 */

export type RevealFrom = 'up' | 'down' | 'left' | 'right' | 'zoom' | 'fade';

export interface RevealOptions {
	/** Where the element comes from. Default `up`. */
	from?: RevealFrom;
	/** Extra delay in ms, added to the automatic stagger. */
	delay?: number;
	/** Animation length in ms. Default 700. */
	duration?: number;
}

const STAGGER = 80;
const MAX_STAGGER_STEPS = 8;
const EASING = 'cubic-bezier(0.22, 1, 0.36, 1)';
const OFFSETS: Record<RevealFrom, string> = {
	up: 'translate3d(0, 28px, 0)',
	down: 'translate3d(0, -28px, 0)',
	left: 'translate3d(-32px, 0, 0)',
	right: 'translate3d(32px, 0, 0)',
	zoom: 'scale(0.94)',
	fade: 'none'
};
/** Attribute that hides an element until it is revealed (see app.css). */
const PENDING = 'data-reveal-pending';

let hydrated = false;

/** Call once the initial hydration has finished (the root layout does this). */
export function markHydrated(): void {
	hydrated = true;
}

const options = new WeakMap<Element, RevealOptions>();
let observer: IntersectionObserver | null = null;

function play(el: HTMLElement, order: number): void {
	const { from = 'up', delay = 0, duration = 700 } = options.get(el) ?? {};
	el.removeAttribute(PENDING);
	// Single keyframe at offset 0: the animation ends on the element's own computed style.
	el.animate([{ opacity: 0, transform: OFFSETS[from], offset: 0 }], {
		duration,
		delay: delay + Math.min(order, MAX_STAGGER_STEPS) * STAGGER,
		easing: EASING,
		fill: 'backwards'
	});
}

function getObserver(): IntersectionObserver {
	observer ??= new IntersectionObserver(
		(entries) => {
			const entering = entries
				.filter((e) => e.isIntersecting)
				.map((e) => ({ el: e.target as HTMLElement, rect: e.boundingClientRect }))
				// Reading order: rows top to bottom (16px tolerance), then left to right.
				.sort((a, b) =>
					Math.abs(a.rect.top - b.rect.top) > 16
						? a.rect.top - b.rect.top
						: a.rect.left - b.rect.left
				);
			entering.forEach(({ el }, i) => {
				observer?.unobserve(el);
				play(el, i);
			});
		},
		{ rootMargin: '0px 0px -40px 0px' }
	);
	return observer;
}

function inViewport(el: Element): boolean {
	const rect = el.getBoundingClientRect();
	return rect.top < window.innerHeight && rect.bottom > 0;
}

export const reveal: Action<HTMLElement, RevealOptions | undefined> = (node, params) => {
	if (
		typeof IntersectionObserver === 'undefined' ||
		typeof node.animate !== 'function' ||
		matchMedia('(prefers-reduced-motion: reduce)').matches ||
		(!hydrated && inViewport(node))
	) {
		return;
	}

	options.set(node, params ?? {});
	node.setAttribute(PENDING, '');
	getObserver().observe(node);

	return {
		update(next) {
			options.set(node, next ?? {});
		},
		destroy() {
			observer?.unobserve(node);
			options.delete(node);
		}
	};
};
