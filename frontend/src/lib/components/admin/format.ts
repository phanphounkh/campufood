import { formatCents, formatMoney } from '#lib/utils/money.ts';

/** Integer cents → "$1,253.75". */
export const usdCents = formatCents;

/** API money string ("1253.75") → "$1,253.75". */
export const usd = formatMoney;
