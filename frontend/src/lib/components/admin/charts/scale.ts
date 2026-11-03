/** Small helpers for hand-written SVG charts. Values are integers (cents or counts). */

export interface ChartPoint {
	/** Short axis label, e.g. "09:00" or "Nov 3". */
	label: string;
	/** Longer label for tooltips and the data table, e.g. "Mon, Nov 3". */
	fullLabel: string;
	/** Integer value (cents for money, a count otherwise). */
	value: number;
	/** Optional secondary line in the tooltip, e.g. "12 orders". */
	detail?: string;
}

function niceStep(raw: number): number {
	if (raw <= 0) return 1;
	const magnitude = 10 ** Math.floor(Math.log10(raw));
	const norm = raw / magnitude;
	const nice = norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 2.5 ? 2.5 : norm <= 5 ? 5 : 10;
	return nice * magnitude;
}

/** Round tick values from 0 to a "nice" maximum covering `max`. */
export function niceTicks(max: number, count = 4, minStep = 1): number[] {
	const step = Math.max(minStep, niceStep(max / count));
	const top = Math.max(step, Math.ceil(max / step) * step);
	const ticks: number[] = [];
	for (let v = 0; v <= top + step / 1000; v += step) ticks.push(Math.round(v));
	return ticks;
}

/** "$1,250" / "$2.50" — compact money for axis ticks (input in cents). */
export function axisMoney(cents: number): string {
	const dollars = Math.floor(cents / 100);
	const rest = cents % 100;
	const whole =
		dollars >= 10_000 ? `${Math.round(dollars / 1000)}K` : dollars.toLocaleString('en-US');
	return rest ? `$${whole}.${String(rest).padStart(2, '0')}` : `$${whole}`;
}

/** Indices of x labels that fit without colliding (always the first and the last). */
export function labelIndices(count: number, plotWidth: number, minGap = 64): Set<number> {
	if (count <= 0) return new Set();
	const fit = Math.max(2, Math.floor(plotWidth / minGap));
	const every = Math.max(1, Math.ceil(count / fit));
	const last = count - 1;
	const out = new Set<number>();
	for (let i = 0; i < count; i += every) {
		// Keep a full step of room before the final label so the two never touch.
		if (i === 0 || last - i >= every) out.add(i);
	}
	out.add(last);
	return out;
}

/** Column path: 4px rounded data-end (top), square at the baseline. */
export function columnPath(x: number, y: number, width: number, baseline: number): string {
	const height = baseline - y;
	if (height <= 0) return '';
	const r = Math.min(4, width / 2, height);
	return [
		`M${x},${baseline}`,
		`L${x},${y + r}`,
		`Q${x},${y} ${x + r},${y}`,
		`L${x + width - r},${y}`,
		`Q${x + width},${y} ${x + width},${y + r}`,
		`L${x + width},${baseline}`,
		'Z'
	].join(' ');
}
