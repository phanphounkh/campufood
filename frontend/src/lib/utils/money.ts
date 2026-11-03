/**
 * Money helpers. Amounts are handled as integer cents in the browser and exchanged with the
 * API as exact 2-decimal strings ("1.50"). No floating point arithmetic touches a price.
 * The server always recomputes totals; these are for display only.
 */

const MONEY_RE = /^(-)?(\d+)(?:\.(\d{1,2}))?$/;

export function toCents(value: string | number): number {
	const text = typeof value === 'number' ? value.toFixed(2) : value.trim();
	const match = MONEY_RE.exec(text);
	if (!match) throw new Error(`Invalid money value: ${value}`);
	const [, sign, whole, frac = ''] = match;
	const cents = Number(whole) * 100 + Number(frac.padEnd(2, '0'));
	return sign ? -cents : cents;
}

export function centsToString(cents: number): string {
	const sign = cents < 0 ? '-' : '';
	const abs = Math.abs(Math.round(cents));
	return `${sign}${Math.floor(abs / 100)}.${String(abs % 100).padStart(2, '0')}`;
}

/** 375 → "$3.75", 125375 → "$1,253.75". */
export function formatCents(cents: number): string {
	const [whole, frac] = centsToString(Math.abs(cents)).split('.');
	const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
	return `${cents < 0 ? '-' : ''}$${grouped}.${frac}`;
}

export function formatMoney(value: string | number): string {
	return formatCents(toCents(value));
}

export function lineTotalCents(unitPrice: string, quantity: number): number {
	return toCents(unitPrice) * quantity;
}

/** "1.5", "01.50", "2" → "1.50" / "2.00"; null if not a valid positive amount. */
export function normalizePrice(input: string): string | null {
	const text = input.trim().replace(/^\$/, '');
	if (!/^\d{1,4}(\.\d{1,2})?$/.test(text)) return null;
	const cents = toCents(text);
	return cents > 0 ? centsToString(cents) : null;
}
