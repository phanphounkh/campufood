<script lang="ts">
	import { adminHref } from '#lib/components/admin/links.ts';
	import { invalidate } from '$app/navigation';
	import { page } from '$app/state';
	import Boxes from '@lucide/svelte/icons/boxes';
	import TriangleAlert from '@lucide/svelte/icons/triangle-alert';
	import Ban from '@lucide/svelte/icons/ban';
	import Hourglass from '@lucide/svelte/icons/hourglass';
	import PackagePlus from '@lucide/svelte/icons/package-plus';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import PageHeader from '#lib/components/admin/PageHeader.svelte';
	import KpiCard from '#lib/components/admin/KpiCard.svelte';
	import ErrorState from '#lib/components/admin/ErrorState.svelte';
	import SearchInput from '#lib/components/admin/SearchInput.svelte';
	import Toggle from '#lib/components/admin/Toggle.svelte';
	import Pagination from '#lib/components/admin/Pagination.svelte';
	import { reportError } from '#lib/components/admin/errors.ts';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import FoodImage from '#lib/components/ui/FoodImage.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import { ApiError } from '#lib/services/api.ts';
	import { updateInventory } from '#lib/services/admin.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { i18n, t } from '#lib/i18n/index.svelte.ts';
	import { formatDateTime } from '#lib/utils/format.ts';
	import type { InventoryItem } from '#lib/types/api.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let items = $derived(data.items ?? []);
	let search = $state('');
	// svelte-ignore state_referenced_locally
	let lowOnly = $state(data.lowOnly);

	const visible = $derived(
		items.filter(
			(i) =>
				(!lowOnly || i.low_stock) &&
				(!search ||
					i.name_en.toLowerCase().includes(search.toLowerCase()) ||
					i.name_km.includes(search))
		)
	);
	const lowCount = $derived(items.filter((i) => i.low_stock).length);
	const outCount = $derived(items.filter((i) => i.stock_quantity === 0).length);
	const reserved = $derived(items.reduce((sum, i) => sum + i.reserved_quantity, 0));

	function replace(updated: InventoryItem) {
		items = items.map((i) =>
			i.food_id === updated.food_id ? { ...updated, reserved_quantity: i.reserved_quantity } : i
		);
	}

	async function setAvailable(item: InventoryItem, value: boolean) {
		try {
			replace(
				await updateInventory(item.food_id, {
					mode: 'adjust',
					quantity: 0,
					reason: 'manual_adjustment',
					is_available: value
				})
			);
			toast.success(
				t(value ? 'admin.inventory.availableOn' : 'admin.inventory.availableOff', {
					name: item.name_en
				})
			);
		} catch (err) {
			reportError(err);
		}
	}

	// ── Restock modal ─────────────────────────────────────────────
	let target = $state<InventoryItem | null>(null);
	let open = $state(false);
	let mode = $state<'adjust' | 'set'>('adjust');
	let quantity = $state<number | string>(10);
	let reason = $state<'restock' | 'manual_adjustment'>('restock');
	let note = $state('');
	let error = $state('');
	let saving = $state(false);

	function openRestock(item: InventoryItem) {
		target = item;
		mode = 'adjust';
		quantity = 10;
		reason = 'restock';
		note = '';
		error = '';
		open = true;
	}

	const qty = $derived(Number(quantity));
	const validQty = $derived(Number.isInteger(qty) && String(quantity).trim() !== '');
	const newStock = $derived(
		target && validQty ? (mode === 'set' ? qty : target.stock_quantity + qty) : null
	);

	async function save(event: SubmitEvent) {
		event.preventDefault();
		if (!target) return;
		if (!validQty) return void (error = t('admin.inventory.invalidQuantity'));
		if (newStock !== null && newStock < 0) return void (error = t('admin.inventory.negative'));
		saving = true;
		try {
			const updated = await updateInventory(target.food_id, {
				mode,
				quantity: qty,
				reason,
				note: note.trim() || undefined
			});
			replace(updated);
			toast.success(t('admin.inventory.updated', { name: updated.name_en }));
			open = false;
			invalidate('admin:inventory');
		} catch (err) {
			if (err instanceof ApiError && err.status < 500 && err.status !== 401) error = err.message;
			else reportError(err);
		} finally {
			saving = false;
		}
	}

	function movementsHref(p: number) {
		return adminHref('/admin/inventory', {
			low: page.url.searchParams.get('low'),
			mpage: p > 1 ? p : null
		});
	}
</script>

<svelte:head><title>{t('admin.inventory.title')} · {t('admin.title')}</title></svelte:head>

<PageHeader title={t('admin.inventory.title')} subtitle={t('admin.inventory.subtitle')} />

{#if data.error || !data.items}
	<ErrorState message={data.error ?? ''} />
{:else}
	<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
		<KpiCard label={t('admin.inventory.totalItems')} value={String(items.length)} icon={Boxes} />
		<KpiCard
			label={t('admin.inventory.lowStock')}
			value={String(lowCount)}
			icon={TriangleAlert}
			tone="amber"
			hint={data.threshold !== null
				? t('admin.inventory.threshold', { count: data.threshold })
				: undefined}
		/>
		<KpiCard label={t('admin.inventory.soldOut')} value={String(outCount)} icon={Ban} tone="rose" />
		<KpiCard
			label={t('admin.inventory.reserved')}
			value={String(reserved)}
			icon={Hourglass}
			tone="sky"
			hint={t('admin.inventory.reservedHint')}
		/>
	</div>

	<div class="card mt-6 overflow-hidden">
		<div class="flex flex-col gap-3 border-b border-line p-4 sm:flex-row sm:items-center">
			<SearchInput
				class="w-full sm:w-72"
				placeholder={t('admin.inventory.search')}
				delay={150}
				onsearch={(v) => (search = v)}
			/>
			<label class="flex items-center gap-2 text-sm font-medium text-ink-soft">
				<input type="checkbox" bind:checked={lowOnly} />
				{t('admin.inventory.lowOnly')}
			</label>
		</div>

		{#if visible.length === 0}
			<EmptyState icon={Boxes} title={t('admin.inventory.empty')} compact />
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full min-w-[820px] text-left text-sm">
					<thead class="bg-canvas text-xs font-semibold whitespace-nowrap text-ink-muted">
						<tr>
							<th class="px-4 py-3">{t('admin.col.food')}</th>
							<th class="px-3 py-3">{t('admin.col.category')}</th>
							<th class="px-3 py-3 text-right">{t('admin.col.stock')}</th>
							<th class="px-3 py-3 text-right">{t('admin.col.reserved')}</th>
							<th class="px-3 py-3 text-center">{t('admin.col.available')}</th>
							<th class="px-4 py-3 text-right">{t('admin.col.actions')}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-line">
						{#each visible as item (item.food_id)}
							<tr class="hover:bg-canvas/60">
								<td class="px-4 py-2.5">
									<div class="flex items-center gap-3">
										<FoodImage src={item.image_url} alt="" class="size-10 shrink-0 rounded-lg" />
										<div>
											<p class="font-semibold text-ink">{item.name_en}</p>
											<p class="text-xs text-ink-muted" lang="km">{item.name_km}</p>
										</div>
									</div>
								</td>
								<td class="px-3 py-2.5 text-ink-soft">{item.category_name_en}</td>
								<td class="px-3 py-2.5 text-right">
									<span class="inline-flex items-center gap-2">
										{#if item.stock_quantity === 0}
											<span class="chip bg-red-50 text-red-700">{t('admin.inventory.out')}</span>
										{:else if item.low_stock}
											<span class="chip bg-amber-50 text-amber-800">{t('admin.inventory.low')}</span
											>
										{/if}
										<span
											class="text-base font-bold tabular-nums {item.stock_quantity === 0
												? 'text-danger-ink'
												: item.low_stock
													? 'text-amber-700'
													: 'text-ink'}"
										>
											{item.stock_quantity}
										</span>
									</span>
								</td>
								<td class="px-3 py-2.5 text-right text-ink-muted tabular-nums"
									>{item.reserved_quantity || '—'}</td
								>
								<td class="px-3 py-2.5 text-center">
									<Toggle
										size="sm"
										checked={item.is_available}
										label={t('admin.inventory.toggleAvailable', { name: item.name_en })}
										onchange={(v) => setAvailable(item, v)}
									/>
								</td>
								<td class="px-4 py-2.5 text-right">
									<button
										type="button"
										class="btn btn-soft btn-sm"
										onclick={() => openRestock(item)}
										aria-label={t('admin.inventory.restockNamed', { name: item.name_en })}
									>
										<PackagePlus class="size-4" />{t('admin.inventory.restock')}
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>

	<section class="card mt-6 overflow-hidden">
		<h2 class="px-5 py-4 text-base font-bold text-ink">{t('admin.inventory.movements')}</h2>
		{#if !data.movements || data.movements.items.length === 0}
			<p class="border-t border-line px-5 py-8 text-center text-sm text-ink-muted">
				{t('admin.inventory.movementsEmpty')}
			</p>
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full min-w-[720px] text-left text-sm">
					<thead
						class="border-t border-line bg-canvas text-xs font-semibold whitespace-nowrap text-ink-muted"
					>
						<tr>
							<th class="px-5 py-3">{t('admin.col.time')}</th>
							<th class="px-3 py-3">{t('admin.col.food')}</th>
							<th class="px-3 py-3 text-right">{t('admin.col.change')}</th>
							<th class="px-3 py-3">{t('admin.col.reason')}</th>
							<th class="px-5 py-3">{t('admin.col.note')}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-line">
						{#each data.movements.items as m (m.id)}
							<tr>
								<td class="px-5 py-2.5 whitespace-nowrap text-ink-muted"
									>{formatDateTime(m.created_at, i18n.locale)}</td
								>
								<td class="px-3 py-2.5 font-semibold text-ink">{m.food_name_en}</td>
								<td
									class="px-3 py-2.5 text-right font-bold tabular-nums {m.quantity_change > 0
										? 'text-green-700'
										: 'text-red-700'}"
								>
									{m.quantity_change > 0 ? '+' : '−'}{Math.abs(m.quantity_change)}
								</td>
								<td class="px-3 py-2.5 text-ink-soft">
									{t(`admin.reason.${m.reason}`)}
									{#if m.order_number}
										<a
											href={adminHref('/admin/orders', { open: m.order_id })}
											class="ml-1 font-semibold text-brand-700 hover:underline">{m.order_number}</a
										>
									{/if}
								</td>
								<td class="px-5 py-2.5 text-ink-muted">{m.note ?? ''}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			<Pagination
				page={data.movementPage}
				pageSize={data.movements.page_size}
				total={data.movements.total}
				href={movementsHref}
			/>
		{/if}
	</section>
{/if}

<Modal
	bind:open
	title={t('admin.inventory.restockTitle')}
	description={target
		? `${target.name_en} · ${t('admin.inventory.current', { count: target.stock_quantity })}`
		: undefined}
	size="sm"
>
	<form id="restock-form" class="space-y-4" novalidate onsubmit={save}>
		<div
			class="grid grid-cols-2 gap-1 rounded-xl bg-canvas p-1"
			role="radiogroup"
			aria-label={t('admin.inventory.quantity')}
		>
			{#each [['adjust', 'admin.inventory.modeAdjust'], ['set', 'admin.inventory.modeSet']] as [value, key] (value)}
				<button
					type="button"
					role="radio"
					aria-checked={mode === value}
					class="rounded-lg px-3 py-2 text-sm font-semibold transition {mode === value
						? 'bg-white text-brand-700 shadow-sm'
						: 'text-ink-muted hover:text-ink'}"
					onclick={() => {
						mode = value as 'adjust' | 'set';
						if (mode === 'set' && target) quantity = target.stock_quantity;
						reason = mode === 'set' ? 'manual_adjustment' : 'restock';
						error = '';
					}}
				>
					{t(key)}
				</button>
			{/each}
		</div>
		<div>
			<label class="label" for="restock-qty">{t('admin.inventory.quantity')}</label>
			<input
				id="restock-qty"
				type="number"
				step="1"
				min={mode === 'set' ? 0 : undefined}
				class="w-full text-lg font-bold tabular-nums"
				bind:value={quantity}
				aria-invalid={!!error}
				aria-describedby="restock-hint"
			/>
			<p id="restock-hint" class="mt-1 text-xs text-ink-muted">
				{mode === 'adjust'
					? t('admin.inventory.quantityAdjustHint')
					: t('admin.inventory.quantitySetHint')}
			</p>
		</div>
		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label class="label" for="restock-reason">{t('admin.inventory.reason')}</label>
				<select id="restock-reason" class="w-full rounded-xl" bind:value={reason}>
					<option value="restock">{t('admin.reason.restock')}</option>
					<option value="manual_adjustment">{t('admin.reason.manual_adjustment')}</option>
				</select>
			</div>
			<div>
				<label class="label" for="restock-note">{t('admin.inventory.note')}</label>
				<input
					id="restock-note"
					type="text"
					maxlength="300"
					class="w-full"
					placeholder={t('admin.inventory.notePlaceholder')}
					bind:value={note}
				/>
			</div>
		</div>
		{#if newStock !== null}
			<p
				class="rounded-xl px-4 py-3 text-sm font-semibold {newStock < 0
					? 'bg-red-50 text-red-700'
					: 'bg-brand-50 text-brand-800'}"
			>
				{t('admin.inventory.newStock', { count: newStock })}
			</p>
		{/if}
		{#if error}<p class="field-error" role="alert">{error}</p>{/if}
	</form>
	{#snippet footer()}
		<button type="button" class="btn btn-secondary" onclick={() => (open = false)}
			>{t('common.cancel')}</button
		>
		<button type="submit" form="restock-form" class="btn btn-primary" disabled={saving}>
			{#if saving}<LoaderCircle class="size-4 animate-spin" />{/if}{t('admin.inventory.save')}
		</button>
	{/snippet}
</Modal>
