<script lang="ts">
	import ImagePlus from '@lucide/svelte/icons/image-plus';
	import Trash from '@lucide/svelte/icons/trash';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import Modal from '#lib/components/ui/Modal.svelte';
	import FoodImage from '#lib/components/ui/FoodImage.svelte';
	import { ApiError } from '#lib/services/api.ts';
	import { createFood, updateFood, uploadImage } from '#lib/services/catalog.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import { fieldErrors, foodSchema, validateImageFile } from '#lib/utils/validation.ts';
	import type { Category, Food, FoodInput } from '#lib/types/api.ts';
	import Toggle from './Toggle.svelte';
	import { reportError } from './errors.ts';

	let {
		open = $bindable(false),
		food,
		categories,
		onsaved
	}: {
		open?: boolean;
		food: Food | null;
		categories: Category[];
		onsaved: (food: Food) => void;
	} = $props();

	const empty = {
		name_en: '',
		name_km: '',
		description_en: '',
		description_km: '',
		category_id: '',
		price: '',
		stock_quantity: '0' as string | number,
		image_url: null as string | null,
		is_available: true,
		is_featured: false
	};

	let form = $state({ ...empty });
	let errors = $state<Record<string, string>>({});
	let formError = $state('');
	let saving = $state(false);
	let uploading = $state(false);
	let fileInput: HTMLInputElement | undefined = $state();

	// Reset the form each time the modal opens.
	$effect(() => {
		if (!open) return;
		errors = {};
		formError = '';
		form = food
			? {
					name_en: food.name_en,
					name_km: food.name_km,
					description_en: food.description_en,
					description_km: food.description_km,
					category_id: String(food.category_id),
					price: food.price,
					stock_quantity: food.stock_quantity as string | number,
					image_url: food.image_url,
					is_available: food.is_available,
					is_featured: food.is_featured
				}
			: { ...empty, category_id: categories[0] ? String(categories[0].id) : '' };
	});

	async function onFile(event: Event) {
		const input = event.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		input.value = '';
		if (!file) return;
		const problem = validateImageFile(file);
		if (problem) {
			errors = { ...errors, image_url: problem };
			return;
		}
		uploading = true;
		try {
			const result = await uploadImage(file);
			form.image_url = result.url;
			errors = { ...errors, image_url: '' };
			toast.success(t('admin.food.uploaded'));
		} catch (err) {
			errors = { ...errors, image_url: err instanceof Error ? err.message : 'Upload failed' };
		} finally {
			uploading = false;
		}
	}

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		formError = '';
		const parsed = foodSchema.safeParse(form);
		if (!parsed.success) {
			errors = fieldErrors(parsed.error);
			formError = t('admin.food.fixErrors');
			return;
		}
		errors = {};
		saving = true;
		try {
			const body: FoodInput = parsed.data;
			const saved = food ? await updateFood(food.id, body) : await createFood(body);
			toast.success(t(food ? 'admin.menu.updated' : 'admin.menu.created', { name: saved.name_en }));
			open = false;
			onsaved(saved);
		} catch (err) {
			if (err instanceof ApiError && err.status === 422) {
				errors = err.fieldErrors;
				formError = t('admin.food.fixErrors');
			} else if (err instanceof ApiError && err.code === 'INVALID_CATEGORY') {
				errors = { category_id: err.message };
			} else reportError(err);
		} finally {
			saving = false;
		}
	}

	const inputClass = (field: string) =>
		`w-full rounded-xl ${errors[field] ? 'border-danger focus:border-danger focus:ring-red-100' : ''}`;
</script>

{#snippet error(field: string)}
	{#if errors[field]}<p id="food-{field}-error" class="field-error">{t(errors[field])}</p>{/if}
{/snippet}

<Modal
	bind:open
	size="lg"
	title={food ? t('admin.food.editTitle') : t('admin.food.newTitle')}
	description={t('admin.food.formSub')}
>
	<form id="food-form" class="space-y-5" novalidate onsubmit={submit}>
		{#if formError}
			<p class="rounded-xl bg-red-50 px-4 py-2.5 text-sm font-medium text-red-700" role="alert">
				{formError}
			</p>
		{/if}

		<!-- Photo -->
		<div>
			<span class="label">{t('admin.food.image')}</span>
			<div class="flex flex-col gap-4 sm:flex-row sm:items-center">
				<div class="relative">
					<FoodImage
						src={form.image_url}
						alt={form.name_en}
						class="h-28 w-40 rounded-2xl border border-line"
						loading="eager"
					/>
					{#if uploading}
						<div class="absolute inset-0 grid place-items-center rounded-2xl bg-white/70">
							<LoaderCircle class="size-6 animate-spin text-brand-600" />
						</div>
					{/if}
				</div>
				<div class="space-y-2">
					<div class="flex flex-wrap gap-2">
						<button
							type="button"
							class="btn btn-secondary btn-sm"
							disabled={uploading}
							onclick={() => fileInput?.click()}
						>
							<ImagePlus class="size-4" />
							{uploading
								? t('admin.food.uploading')
								: form.image_url
									? t('admin.food.replace')
									: t('admin.food.upload')}
						</button>
						{#if form.image_url}
							<button
								type="button"
								class="btn btn-ghost btn-sm text-danger-ink"
								onclick={() => (form.image_url = null)}
							>
								<Trash class="size-4" />{t('admin.food.removeImage')}
							</button>
						{/if}
					</div>
					<p class="text-xs text-ink-muted">{t('admin.food.imageHint')}</p>
					{@render error('image_url')}
				</div>
				<input
					bind:this={fileInput}
					type="file"
					accept="image/jpeg,image/png,image/webp"
					class="sr-only"
					tabindex="-1"
					aria-label={t('admin.food.upload')}
					onchange={onFile}
				/>
			</div>
		</div>

		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label class="label" for="food-name_en">{t('admin.food.nameEn')}</label>
				<input
					id="food-name_en"
					type="text"
					maxlength="120"
					class={inputClass('name_en')}
					bind:value={form.name_en}
					aria-invalid={!!errors.name_en}
					aria-describedby={errors.name_en ? 'food-name_en-error' : undefined}
				/>
				{@render error('name_en')}
			</div>
			<div>
				<label class="label" for="food-name_km">{t('admin.food.nameKm')}</label>
				<input
					id="food-name_km"
					type="text"
					lang="km"
					maxlength="120"
					class={inputClass('name_km')}
					bind:value={form.name_km}
					aria-invalid={!!errors.name_km}
					aria-describedby={errors.name_km ? 'food-name_km-error' : undefined}
				/>
				{@render error('name_km')}
			</div>
			<div>
				<label class="label" for="food-description_en">{t('admin.food.descEn')}</label>
				<textarea
					id="food-description_en"
					rows="3"
					maxlength="500"
					class={inputClass('description_en')}
					bind:value={form.description_en}
					aria-invalid={!!errors.description_en}></textarea>
				{@render error('description_en')}
			</div>
			<div>
				<label class="label" for="food-description_km">{t('admin.food.descKm')}</label>
				<textarea
					id="food-description_km"
					rows="3"
					lang="km"
					maxlength="500"
					class={inputClass('description_km')}
					bind:value={form.description_km}
					aria-invalid={!!errors.description_km}></textarea>
				{@render error('description_km')}
			</div>
		</div>

		<div class="grid gap-4 sm:grid-cols-3">
			<div>
				<label class="label" for="food-category_id">{t('admin.food.category')}</label>
				<select
					id="food-category_id"
					class={inputClass('category_id')}
					bind:value={form.category_id}
					aria-invalid={!!errors.category_id}
					aria-describedby={errors.category_id ? 'food-category_id-error' : undefined}
				>
					<option value="" disabled>{t('admin.food.chooseCategory')}</option>
					{#each categories as category (category.id)}
						<option value={String(category.id)}>{category.name_en} · {category.name_km}</option>
					{/each}
				</select>
				{@render error('category_id')}
			</div>
			<div>
				<label class="label" for="food-price">{t('admin.food.price')}</label>
				<div class="relative">
					<span
						class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-sm text-ink-muted"
						>$</span
					>
					<input
						id="food-price"
						type="text"
						inputmode="decimal"
						placeholder="1.50"
						class="{inputClass('price')} pl-7 tabular-nums"
						bind:value={form.price}
						aria-invalid={!!errors.price}
						aria-describedby={errors.price ? 'food-price-error' : undefined}
					/>
				</div>
				{@render error('price')}
			</div>
			<div>
				<label class="label" for="food-stock_quantity">{t('admin.food.stock')}</label>
				<input
					id="food-stock_quantity"
					type="number"
					min="0"
					step="1"
					inputmode="numeric"
					class="{inputClass('stock_quantity')} tabular-nums"
					bind:value={form.stock_quantity}
					aria-invalid={!!errors.stock_quantity}
					aria-describedby={errors.stock_quantity ? 'food-stock_quantity-error' : undefined}
				/>
				{@render error('stock_quantity')}
			</div>
		</div>

		<div class="grid gap-3 sm:grid-cols-2">
			<div class="flex items-start justify-between gap-4 rounded-xl border border-line p-4">
				<div>
					<p class="text-sm font-semibold text-ink">{t('admin.food.available')}</p>
					<p class="text-xs text-ink-muted">{t('admin.food.availableHint')}</p>
				</div>
				<Toggle
					checked={form.is_available}
					label={t('admin.food.available')}
					onchange={(v) => (form.is_available = v)}
				/>
			</div>
			<div class="flex items-start justify-between gap-4 rounded-xl border border-line p-4">
				<div>
					<p class="text-sm font-semibold text-ink">{t('admin.food.featured')}</p>
					<p class="text-xs text-ink-muted">{t('admin.food.featuredHint')}</p>
				</div>
				<Toggle
					checked={form.is_featured}
					label={t('admin.food.featured')}
					onchange={(v) => (form.is_featured = v)}
				/>
			</div>
		</div>
	</form>

	{#snippet footer()}
		<button type="button" class="btn btn-secondary" onclick={() => (open = false)}
			>{t('common.cancel')}</button
		>
		<button type="submit" form="food-form" class="btn btn-primary" disabled={saving || uploading}>
			{#if saving}<LoaderCircle class="size-4 animate-spin" />{t('admin.saving')}
			{:else}{food ? t('admin.save') : t('admin.food.create')}{/if}
		</button>
	{/snippet}
</Modal>
