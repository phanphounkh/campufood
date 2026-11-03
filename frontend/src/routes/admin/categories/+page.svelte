<script lang="ts">
	import { invalidate } from '$app/navigation';
	import Plus from '@lucide/svelte/icons/plus';
	import Pencil from '@lucide/svelte/icons/pencil';
	import Trash from '@lucide/svelte/icons/trash';
	import Tags from '@lucide/svelte/icons/tags';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import PageHeader from '#lib/components/admin/PageHeader.svelte';
	import ErrorState from '#lib/components/admin/ErrorState.svelte';
	import { reportError } from '#lib/components/admin/errors.ts';
	import ConfirmDialog from '#lib/components/ui/ConfirmDialog.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import Modal from '#lib/components/ui/Modal.svelte';
	import { ApiError } from '#lib/services/api.ts';
	import { createCategory, deleteCategory, updateCategory } from '#lib/services/catalog.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import { categorySchema, fieldErrors } from '#lib/utils/validation.ts';
	import type { Category } from '#lib/types/api.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const isAdmin = $derived(data.user.role === 'admin');

	// ── Form ──────────────────────────────────────────────────────
	let formOpen = $state(false);
	let editing = $state<Category | null>(null);
	let form = $state({ name_en: '', name_km: '', slug: '', sort_order: 0 as number | string });
	let errors = $state<Record<string, string>>({});
	let saving = $state(false);

	function openForm(category: Category | null) {
		editing = category;
		errors = {};
		const nextOrder = Math.max(0, ...(data.categories ?? []).map((c) => c.sort_order)) + 1;
		form = category
			? {
					name_en: category.name_en,
					name_km: category.name_km,
					slug: category.slug,
					sort_order: category.sort_order
				}
			: { name_en: '', name_km: '', slug: '', sort_order: nextOrder };
		formOpen = true;
	}

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		const parsed = categorySchema.safeParse(form);
		if (!parsed.success) {
			errors = fieldErrors(parsed.error);
			return;
		}
		errors = {};
		saving = true;
		const { slug, ...rest } = parsed.data;
		try {
			if (editing) {
				await updateCategory(editing.id, { ...rest, ...(slug ? { slug } : {}) });
				toast.success(t('admin.categories.updated'));
			} else {
				await createCategory({ ...rest, ...(slug ? { slug } : {}) });
				toast.success(t('admin.categories.created'));
			}
			formOpen = false;
			await invalidate('admin:categories');
		} catch (err) {
			if (err instanceof ApiError && err.status === 409)
				errors = { slug: t('admin.categories.duplicate') };
			else if (err instanceof ApiError && err.status === 422) errors = err.fieldErrors;
			else reportError(err);
		} finally {
			saving = false;
		}
	}

	// ── Delete ────────────────────────────────────────────────────
	let deleteTarget = $state<Category | null>(null);
	let deleteOpen = $state(false);
	let deleting = $state(false);
	async function confirmDelete() {
		if (!deleteTarget) return;
		deleting = true;
		try {
			await deleteCategory(deleteTarget.id);
			toast.success(t('admin.categories.deleted'));
			deleteOpen = false;
			await invalidate('admin:categories');
		} catch (err) {
			deleteOpen = false;
			if (err instanceof ApiError && err.code === 'CATEGORY_IN_USE')
				toast.error(t('admin.categories.inUse'));
			else reportError(err);
		} finally {
			deleting = false;
		}
	}

	const inputClass = (field: string) =>
		`w-full ${errors[field] ? 'border-danger focus:border-danger focus:ring-red-100' : ''}`;
</script>

<svelte:head><title>{t('admin.categories.title')} · {t('admin.title')}</title></svelte:head>

<PageHeader title={t('admin.categories.title')} subtitle={t('admin.categories.subtitle')}>
	{#snippet actions()}
		{#if isAdmin}
			<button type="button" class="btn btn-primary" onclick={() => openForm(null)}>
				<Plus class="size-4" />{t('admin.categories.add')}
			</button>
		{/if}
	{/snippet}
</PageHeader>

{#if data.error || !data.categories}
	<ErrorState message={data.error ?? ''} />
{:else if data.categories.length === 0}
	<div class="card"><EmptyState icon={Tags} title={t('admin.categories.empty')} /></div>
{:else}
	<div class="card overflow-hidden">
		<div class="overflow-x-auto">
			<table class="w-full min-w-[640px] text-left text-sm">
				<thead class="bg-canvas text-xs font-semibold whitespace-nowrap text-ink-muted">
					<tr>
						<th class="px-4 py-3">{t('admin.col.sortOrder')}</th>
						<th class="px-3 py-3">{t('admin.col.name')}</th>
						<th class="px-3 py-3">{t('admin.col.slug')}</th>
						<th class="px-3 py-3 text-right">{t('admin.col.foods')}</th>
						<th class="px-4 py-3 text-right">{t('admin.col.actions')}</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-line">
					{#each data.categories as category (category.id)}
						<tr class="hover:bg-canvas/60">
							<td class="px-4 py-3 text-ink-muted tabular-nums">{category.sort_order}</td>
							<td class="px-3 py-3">
								<p class="font-semibold text-ink">{category.name_en}</p>
								<p class="text-xs text-ink-muted" lang="km">{category.name_km}</p>
							</td>
							<td class="px-3 py-3"
								><code class="rounded bg-canvas px-1.5 py-0.5 text-xs">{category.slug}</code></td
							>
							<td class="px-3 py-3 text-right font-semibold tabular-nums">{category.food_count}</td>
							<td class="px-4 py-3">
								{#if isAdmin}
									<div class="flex justify-end gap-1">
										<button
											type="button"
											class="icon-btn size-8"
											title={t('admin.edit')}
											aria-label={`${t('admin.edit')} ${category.name_en}`}
											onclick={() => openForm(category)}
										>
											<Pencil class="size-4" />
										</button>
										<button
											type="button"
											class="icon-btn size-8 hover:bg-red-50 hover:text-danger-ink"
											title={t('admin.delete')}
											aria-label={t('admin.categories.deleteNamed', { name: category.name_en })}
											onclick={() => {
												deleteTarget = category;
												deleteOpen = true;
											}}
										>
											<Trash class="size-4" />
										</button>
									</div>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
{/if}

{#if isAdmin}
	<Modal
		bind:open={formOpen}
		title={editing ? t('admin.categories.editTitle') : t('admin.categories.newTitle')}
	>
		<form id="category-form" class="space-y-4" novalidate onsubmit={submit}>
			<div>
				<label class="label" for="cat-name_en">{t('admin.categories.nameEn')}</label>
				<input
					id="cat-name_en"
					type="text"
					maxlength="80"
					class={inputClass('name_en')}
					bind:value={form.name_en}
					aria-invalid={!!errors.name_en}
				/>
				{#if errors.name_en}<p class="field-error">{t(errors.name_en)}</p>{/if}
			</div>
			<div>
				<label class="label" for="cat-name_km">{t('admin.categories.nameKm')}</label>
				<input
					id="cat-name_km"
					type="text"
					lang="km"
					maxlength="80"
					class={inputClass('name_km')}
					bind:value={form.name_km}
					aria-invalid={!!errors.name_km}
				/>
				{#if errors.name_km}<p class="field-error">{t(errors.name_km)}</p>{/if}
			</div>
			<div class="grid gap-4 sm:grid-cols-2">
				<div>
					<label class="label" for="cat-slug">{t('admin.categories.slug')}</label>
					<input
						id="cat-slug"
						type="text"
						maxlength="80"
						class={inputClass('slug')}
						placeholder="snacks"
						bind:value={form.slug}
						aria-invalid={!!errors.slug}
					/>
					{#if errors.slug}<p class="field-error">{t(errors.slug)}</p>
					{:else}<p class="mt-1 text-xs text-ink-muted">{t('admin.categories.slugHint')}</p>{/if}
				</div>
				<div>
					<label class="label" for="cat-sort">{t('admin.categories.sortOrder')}</label>
					<input
						id="cat-sort"
						type="number"
						min="0"
						max="1000"
						class={inputClass('sort_order')}
						bind:value={form.sort_order}
					/>
					<p class="mt-1 text-xs text-ink-muted">{t('admin.categories.sortHint')}</p>
				</div>
			</div>
		</form>
		{#snippet footer()}
			<button type="button" class="btn btn-secondary" onclick={() => (formOpen = false)}
				>{t('common.cancel')}</button
			>
			<button type="submit" form="category-form" class="btn btn-primary" disabled={saving}>
				{#if saving}<LoaderCircle class="size-4 animate-spin" />{/if}{t('admin.save')}
			</button>
		{/snippet}
	</Modal>

	<ConfirmDialog
		bind:open={deleteOpen}
		title={t('admin.categories.deleteTitle', { name: deleteTarget?.name_en ?? '' })}
		message={deleteTarget && deleteTarget.food_count > 0
			? t('admin.categories.inUse')
			: t('admin.categories.deleteText')}
		confirmLabel={t('admin.delete')}
		busy={deleting}
		onconfirm={confirmDelete}
	/>
{/if}
