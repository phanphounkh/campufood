export type ToastKind = 'success' | 'error' | 'info';

export interface Toast {
	id: number;
	kind: ToastKind;
	message: string;
}

class ToastStore {
	items = $state<Toast[]>([]);
	#next = 1;

	push(kind: ToastKind, message: string, timeout = kind === 'error' ? 6000 : 3200): number {
		const id = this.#next++;
		// Collapse identical consecutive toasts (e.g. adding the same dish repeatedly).
		this.items = [...this.items.filter((t) => t.message !== message), { id, kind, message }].slice(
			-4
		);
		if (timeout > 0) setTimeout(() => this.dismiss(id), timeout);
		return id;
	}

	dismiss(id: number): void {
		this.items = this.items.filter((t) => t.id !== id);
	}
}

export const toasts = new ToastStore();

export const toast = {
	success: (message: string) => toasts.push('success', message),
	error: (message: string) => toasts.push('error', message),
	info: (message: string) => toasts.push('info', message)
};
