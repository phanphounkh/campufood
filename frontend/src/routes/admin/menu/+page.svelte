<script lang="ts">
	import { adminHref } from '#lib/components/admin/links.ts';
	import { goto, invalidate } from '$app/navigation';
	import Plus from '@lucide/svelte/icons/plus';
	import Pencil from '@lucide/svelte/icons/pencil';
	import Archive from '@lucide/svelte/icons/archive';
	import Undo2 from '@lucide/svelte/icons/undo-2';
	import Star from '@lucide/svelte/icons/star';
	import Utensils from '@lucide/svelte/icons/utensils';
	import Lock from '@lucide/svelte/icons/lock';
	import PageHeader from '#lib/components/admin/PageHeader.svelte';
	import ErrorState from '#lib/components/admin/ErrorState.svelte';
	import SearchInput from '#lib/components/admin/SearchInput.svelte';
	import Toggle from '#lib/components/admin/Toggle.svelte';
	import FoodForm from '#lib/components/admin/FoodForm.svelte';
	import { reportError } from '#lib/components/admin/errors.ts';
	import ConfirmDialog from '#lib/components/ui/ConfirmDialog.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import FoodImage from '#lib/components/ui/FoodImage.svelte';
	import { archiveFood, updateFood } from '#lib/services/catalog.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import { usd } from '#lib/components/admin/format.ts';
	import type { Food } from '#lib/types/api.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const isAdmin = $derived(data.user.role === 'admin');
	// Writable derived: local edits show instantly, a reload resets to server data.
	let foods = $derived(data.foods ?? []);
	let search = $state('');
	let category = $state('all');

	const visible = $derived(
		foods.filter((f) => {
			if (category !== 'all' && String(f.category_id) !== category) return false;
			if (!search) return true;
			const q = search.toLowerCase();
			return f.name_en.toLowerCase().includes(q) || f.name_km.includes(search);
		})
	);

	function replace(updated: Food) {
		foods = foods.map((f) => (f.id === updated.id ? updated : f));
	}

	type Status = { key: string; class: string };
	function statusOf(food: Food): Status {
		if (food.is_archived)
			return {
				key: 'admin.menu.statusArchived',
				class: 'bg-slate-100 text-slate-600 ring-slate-200'
			};
		if (!food.is_available)
			return {
				key: 'admin.menu.statusHidden',
				class: 'bg-slate-100 text-slate-700 ring-slate-200'
			};
		if (food.stock_quantity <= 0)
			return { key: 'admin.menu.statusSoldOut', class: 'bg-red-50 text-red-700 ring-red-200' };
		return { key: 'admin.menu.statusActive', class: 'bg-green-50 text-green-700 ring-green-200' };
	}

	async function toggle(food: Food, field: 'is_available' | 'is_featured', value: boolean) {
		const previous = food;
		replace({ ...food, [field]: value });
		try {
			replace(await updateFood(food.id, { [field]: value }));
		} catch (err) {
			replace(previous);
			reportError(err);
		}
	}

	// ── Create / edit ─────────────────────────────────────────────
	let formOpen = $state(false);
	let editing = $state<Food | null>(null);
	function openForm(food: Food | null) {
		editing = food;
		formOpen = true;
	}
	function onsaved(saved: Food) {
		if (foods.some((f) => f.id === saved.id)) replace(saved);
		invalidate('admin:menu');
	}

	// ── Archive / restore ─────────────────────────────────────────
	let archiveTarget = $state<Food | null>(null);
	let archiveOpen = $state(false);
	let archiving = $state(false);
	async function confirmArchive() {
		if (!archiveTarget) return;
		archiving = true;
		try {
			const archived = await archiveFood(archiveTarget.id);
			toast.success(t('admin.menu.archived', { name: archived.name_en }));
			archiveOpen = false;
			if (data.archived) replace(archived);
			else foods = foods.filter((f) => f.id !== archived.id);
		} catch (err) {
			reportError(err);
		} finally {
			archiving = false;
		}
	}
	async function restore(food: Food) {
		try {
			const restored = await updateFood(food.id, { is_archived: false });
			replace(restored);
			toast.success(t('admin.menu.restored', { name: restored.name_en }));
		} catch (err) {
			reportError(err);
		}
	}
</script>

<svelte:head><title>{t('admin.menu.title')} · {t('admin.title')}</title></svelte:head>

<PageHeader title={t('admin.menu.title')} subtitle={t('admin.menu.subtitle')}>
	{#snippet actions()}
		{#if isAdmin}
			<button type="button" class="btn btn-primary" onclick={() => openForm(null)}>
				<Plus class="size-4" />{t('admin.menu.add')}
			</button>
		{/if}
	{/snippet}
</PageHeader>

{#if !isAdmin}
	<p
		class="mb-4 flex items-center gap-2 rounded-xl border border-line bg-white px-4 py-3 text-sm text-ink-muted"
	>
		<Lock class="size-4" />{t('admin.menu.adminOnly')}
	</p>
{/if}

<div class="card overflow-hidden">
	<div class="flex flex-col gap-3 border-b border-line p-4 sm:flex-row sm:items-center">
		<SearchInput
			class="w-full sm:w-72"
			placeholder={t('admin.menu.search')}
			onsearch={(v) => (search = v)}
			delay={150}
		/>
		<select
			class="w-full rounded-xl py-2 text-sm sm:w-56"
			bind:value={category}
			aria-label={t('admin.col.category')}
		>
			<option value="all">{t('admin.menu.allCategories')}</option>
			{#each data.categories as c (c.id)}
				<option value={String(c.id)}>{c.name_en}</option>
			{/each}
		</select>
		<label class="flex items-center gap-2 text-sm font-medium text-ink-soft sm:ml-auto">
			<input
				type="checkbox"
				checked={data.archived}
				onchange={(e) =>
					goto(adminHref('/admin/menu', { archived: e.currentTarget.checked ? 1 : null }), {
						replace: true,
						reset: false
					})}
			/>
			{t('admin.menu.showArchived')}
		</label>
	</div>

	{#if data.error || !data.foods}
		<div class="p-4"><ErrorState message={data.error ?? ''} /></div>
	{:else if visible.length === 0}
		<EmptyState icon={Utensils} title={t('admin.menu.empty')} text={t('admin.menu.emptyHint')} />
	{:else}
		<div class="overflow-x-auto">
			<table class="w-full min-w-[980px] text-left text-sm">
				<thead class="bg-canvas text-xs font-semibold whitespace-nowrap text-ink-muted">
					<tr>
						<th class="px-4 py-3">{t('admin.col.image')}</th>
						<th class="px-3 py-3">{t('admin.col.name')}</th>
						<th class="px-3 py-3">{t('admin.col.category')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.price')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.stock')}</th>
						<th class="px-3 py-3">{t('admin.col.status')}</th>
						<th class="px-3 py-3 text-center">{t('admin.col.featured')}</th>
						<th class="px-3 py-3 text-center">{t('admin.col.available')}</th>
						<th class="px-4 py-3 text-right">{t('admin.col.actions')}</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-line">
					{#each visible as food (food.id)}
						{@const status = statusOf(food)}
						<tr class="transition hover:bg-canvas/60 {food.is_archived ? 'opacity-60' : ''}">
							<td class="px-4 py-2.5">
								<FoodImage src={food.image_url} alt="" class="h-11 w-14 rounded-lg" />
							</td>
							<td class="px-3 py-2.5">
								<p class="font-semibold text-ink">{food.name_en}</p>
								<p class="text-xs text-ink-muted" lang="km">{food.name_km}</p>
							</td>
							<td class="px-3 py-2.5 text-ink-soft">{food.category.name_en}</td>
							<td class="px-3 py-2.5 text-right font-semibold tabular-nums">{usd(food.price)}</td>
							<td
								class="px-3 py-2.5 text-right tabular-nums {food.stock_quantity === 0
									? 'font-bold text-danger-ink'
									: ''}"
							>
								{food.stock_quantity}
							</td>
							<td class="px-3 py-2.5">
								<span class="chip ring-1 ring-inset {status.class}">{t(status.key)}</span>
							</td>
							<td class="px-3 py-2.5 text-center">
								<button
									type="button"
									class="inline-grid size-8 place-items-center rounded-lg transition hover:bg-amber-50 disabled:opacity-40"
									aria-pressed={food.is_featured}
									aria-label={t('admin.menu.toggleFeatured', { name: food.name_en })}
									disabled={!isAdmin || food.is_archived}
									onclick={() => toggle(food, 'is_featured', !food.is_featured)}
								>
									<Star
										class="size-[18px] {food.is_featured
											? 'fill-amber-400 text-amber-500'
											: 'text-slate-300'}"
									/>
								</button>
							</td>
							<td class="px-3 py-2.5 text-center">
								<Toggle
									size="sm"
									checked={food.is_available}
									disabled={!isAdmin || food.is_archived}
									label={t('admin.menu.toggleAvailable', { name: food.name_en })}
									onchange={(v) => toggle(food, 'is_available', v)}
								/>
							</td>
							<td class="px-4 py-2.5">
								{#if isAdmin}
									<div class="flex items-center justify-end gap-1">
										{#if food.is_archived}
											<button
												type="button"
												class="btn btn-soft btn-sm"
												onclick={() => restore(food)}
											>
												<Undo2 class="size-3.5" />{t('admin.menu.restore')}
											</button>
										{:else}
											<button
												type="button"
												class="icon-btn size-8"
												aria-label={t('admin.menu.editFood', { name: food.name_en })}
												title={t('admin.edit')}
												onclick={() => openForm(food)}
											>
												<Pencil class="size-4" />
											</button>
											<button
												type="button"
												class="icon-btn size-8 hover:bg-red-50 hover:text-danger-ink"
												aria-label={t('admin.menu.archiveNamed', { name: food.name_en })}
												title={t('admin.menu.archive')}
												onclick={() => {
													archiveTarget = food;
													archiveOpen = true;
												}}
											>
												<Archive class="size-4" />
											</button>
										{/if}
									</div>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="border-t border-line px-4 py-3 text-sm text-ink-muted">
			{t('admin.menu.count', { count: visible.length })}
		</p>
	{/if}
</div>

{#if isAdmin}
	<FoodForm bind:open={formOpen} food={editing} categories={data.categories} {onsaved} />
	<ConfirmDialog
		bind:open={archiveOpen}
		title={t('admin.menu.archiveTitle', { name: archiveTarget?.name_en ?? '' })}
		message={t('admin.menu.archiveText')}
		confirmLabel={t('admin.menu.archive')}
		busy={archiving}
		onconfirm={confirmArchive}
	/>
{/if}
