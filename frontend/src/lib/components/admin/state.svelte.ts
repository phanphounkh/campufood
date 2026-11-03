import { ordersSummary } from '#lib/services/orders.ts';
import type { OrderStatus } from '#lib/types/api.ts';

type Summary = Record<OrderStatus | 'all', number>;

/** Live order counts shared by the sidebar badge and the orders page tabs. */
class AdminState {
	summary = $state<Summary | null>(null);
	sidebarOpen = $state(false);

	/** Orders that are paid and waiting for the kitchen to accept them. */
	get waiting(): number {
		return this.summary?.confirmed ?? 0;
	}

	async refreshSummary(): Promise<void> {
		try {
			this.summary = await ordersSummary();
		} catch {
			/* the badge is non-critical; keep the previous value */
		}
	}
}

export const adminState = new AdminState();
