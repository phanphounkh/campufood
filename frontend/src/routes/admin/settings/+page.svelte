<script lang="ts">
	import { invalidate } from '$app/navigation';
	import Store from '@lucide/svelte/icons/store';
	import Clock from '@lucide/svelte/icons/clock';
	import Wallet from '@lucide/svelte/icons/wallet';
	import Share2 from '@lucide/svelte/icons/share-2';
	import UserPlus from '@lucide/svelte/icons/user-plus';
	import Lock from '@lucide/svelte/icons/lock';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import PageHeader from '#lib/components/admin/PageHeader.svelte';
	import ErrorState from '#lib/components/admin/ErrorState.svelte';
	import Toggle from '#lib/components/admin/Toggle.svelte';
	import { reportError } from '#lib/components/admin/errors.ts';
	import Modal from '#lib/components/ui/Modal.svelte';
	import { ApiError } from '#lib/services/api.ts';
	import { createStaff, updateStaff, updateStoreSettings } from '#lib/services/admin.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import type { Role, StoreSettings, User } from '#lib/types/api.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();
	const isAdmin = $derived(data.user.role === 'admin');

	// ── Store settings ────────────────────────────────────────────
	// The form needs a deeply reactive, editable copy for bind:value; writable $derived is
	// shallow, so re-sync with an effect when fresh data arrives.
	// eslint-disable-next-line svelte/prefer-writable-derived
	let form = $state<StoreSettings | null>(null);
	$effect(() => {
		form = data.settings ? { ...data.settings } : null;
	});
	let errors = $state<Record<string, string>>({});
	let saving = $state(false);

	function validate(s: StoreSettings): Record<string, string> {
		const out: Record<string, string> = {};
		if (!s.store_name.trim()) out.store_name = 'validation.required';
		if (s.closing_time <= s.opening_time) out.closing_time = 'admin.settings.closingAfter';
		for (const key of ['facebook_url', 'telegram_url', 'instagram_url'] as const) {
			if (s[key] && !s[key].startsWith('https://')) out[key] = 'admin.settings.httpsOnly';
		}
		for (const key of [
			'min_prep_minutes',
			'payment_expiry_minutes',
			'low_stock_threshold'
		] as const) {
			if (!Number.isInteger(Number(s[key])) || Number(s[key]) < 0)
				out[key] = 'validation.stockInvalid';
		}
		return out;
	}

	async function save(event: SubmitEvent) {
		event.preventDefault();
		if (!form) return;
		errors = validate(form);
		if (Object.keys(errors).length) return;
		saving = true;
		try {
			const saved = await updateStoreSettings({
				...form,
				min_prep_minutes: Number(form.min_prep_minutes),
				payment_expiry_minutes: Number(form.payment_expiry_minutes),
				low_stock_threshold: Number(form.low_stock_threshold)
			});
			form = { ...saved };
			toast.success(t('admin.settings.saved'));
			invalidate('admin:settings');
		} catch (err) {
			if (err instanceof ApiError && err.status === 422) errors = err.fieldErrors;
			else reportError(err);
		} finally {
			saving = false;
		}
	}

	// ── Team ──────────────────────────────────────────────────────
	let staff = $derived(data.staff ?? []);
	function replaceStaff(user: User) {
		staff = staff.map((s) => (s.id === user.id ? user : s));
	}
	async function changeStaff(member: User, changes: { role?: Role; is_active?: boolean }) {
		try {
			const updated = await updateStaff(member.id, changes);
			replaceStaff(updated);
			toast.success(t('admin.settings.staffUpdated', { name: updated.name }));
		} catch (err) {
			if (err instanceof ApiError && err.code === 'SELF_LOCKOUT')
				toast.error(t('admin.settings.selfLockout'));
			else reportError(err);
			staff = [...staff]; // re-render controls back to the stored values
		}
	}

	let staffOpen = $state(false);
	let staffForm = $state({
		name: '',
		email: '',
		phone: '',
		password: '',
		role: 'staff' as 'staff' | 'admin'
	});
	let staffErrors = $state<Record<string, string>>({});
	let creating = $state(false);

	function openStaff() {
		staffForm = { name: '', email: '', phone: '', password: '', role: 'staff' };
		staffErrors = {};
		staffOpen = true;
	}

	async function addStaff(event: SubmitEvent) {
		event.preventDefault();
		const errs: Record<string, string> = {};
		if (staffForm.name.trim().length < 2) errs.name = 'validation.nameRequired';
		if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(staffForm.email.trim()))
			errs.email = 'validation.emailInvalid';
		if (staffForm.password.length < 10) errs.password = 'admin.settings.passwordShort';
		staffErrors = errs;
		if (Object.keys(errs).length) return;
		creating = true;
		try {
			const user = await createStaff({
				name: staffForm.name.trim(),
				email: staffForm.email.trim(),
				phone: staffForm.phone.trim() || undefined,
				password: staffForm.password,
				role: staffForm.role
			});
			staff = [...staff, user];
			toast.success(t('admin.settings.staffCreated', { name: user.name }));
			staffOpen = false;
		} catch (err) {
			if (err instanceof ApiError && err.code === 'EMAIL_TAKEN')
				staffErrors = { email: 'admin.settings.emailTaken' };
			else if (err instanceof ApiError && err.status === 422) staffErrors = err.fieldErrors;
			else reportError(err);
		} finally {
			creating = false;
		}
	}

	const inputClass = (errs: Record<string, string>, field: string) =>
		`w-full ${errs[field] ? 'border-danger focus:border-danger focus:ring-red-100' : ''}`;
</script>

<svelte:head><title>{t('admin.settings.title')} · {t('admin.title')}</title></svelte:head>

<PageHeader title={t('admin.settings.title')} subtitle={t('admin.settings.subtitle')} />

{#snippet fieldError(errs: Record<string, string>, field: string)}
	{#if errs[field]}<p class="field-error">{t(errs[field])}</p>{/if}
{/snippet}

{#if data.error || !form}
	<ErrorState message={data.error ?? ''} />
{:else}
	{#if !isAdmin}
		<p
			class="mb-4 flex items-center gap-2 rounded-xl border border-line bg-white px-4 py-3 text-sm text-ink-muted"
		>
			<Lock class="size-4" />{t('admin.settings.adminOnly')}
		</p>
	{/if}

	<form class="space-y-6" novalidate onsubmit={save}>
		<fieldset class="card p-5 sm:p-6" disabled={!isAdmin}>
			<legend class="sr-only">{t('admin.settings.store')}</legend>
			<h2 class="flex items-center gap-2 text-base font-bold">
				<Store class="size-5 text-brand-600" />{t('admin.settings.store')}
			</h2>
			<div class="mt-4 grid gap-4 md:grid-cols-2">
				<div>
					<label class="label" for="s-name">{t('admin.settings.storeName')}</label>
					<input
						id="s-name"
						type="text"
						maxlength="80"
						class={inputClass(errors, 'store_name')}
						bind:value={form.store_name}
					/>
					{@render fieldError(errors, 'store_name')}
				</div>
				<div>
					<label class="label" for="s-tagline">{t('admin.settings.tagline')}</label>
					<input
						id="s-tagline"
						type="text"
						maxlength="120"
						class="w-full"
						bind:value={form.store_tagline}
					/>
				</div>
				<div>
					<label class="label" for="s-phone">{t('admin.settings.phone')}</label>
					<input
						id="s-phone"
						type="tel"
						maxlength="40"
						class="w-full"
						bind:value={form.store_phone}
					/>
				</div>
				<div>
					<label class="label" for="s-email">{t('admin.settings.email')}</label>
					<input
						id="s-email"
						type="email"
						maxlength="120"
						class={inputClass(errors, 'store_email')}
						bind:value={form.store_email}
					/>
					{@render fieldError(errors, 'store_email')}
				</div>
				<div class="md:col-span-2">
					<label class="label" for="s-address">{t('admin.settings.address')}</label>
					<input
						id="s-address"
						type="text"
						maxlength="200"
						class="w-full"
						bind:value={form.store_address}
					/>
				</div>
			</div>
		</fieldset>

		<fieldset class="card p-5 sm:p-6" disabled={!isAdmin}>
			<legend class="sr-only">{t('admin.settings.hours')}</legend>
			<h2 class="flex items-center gap-2 text-base font-bold">
				<Clock class="size-5 text-brand-600" />{t('admin.settings.hours')}
			</h2>
			<div class="mt-4 grid gap-4 md:grid-cols-3">
				<div>
					<label class="label" for="s-open">{t('admin.settings.opening')}</label>
					<input
						id="s-open"
						type="time"
						class={inputClass(errors, 'opening_time')}
						bind:value={form.opening_time}
					/>
					{@render fieldError(errors, 'opening_time')}
				</div>
				<div>
					<label class="label" for="s-close">{t('admin.settings.closing')}</label>
					<input
						id="s-close"
						type="time"
						class={inputClass(errors, 'closing_time')}
						bind:value={form.closing_time}
					/>
					{@render fieldError(errors, 'closing_time')}
				</div>
				<div>
					<label class="label" for="s-prep">{t('admin.settings.prep')}</label>
					<input
						id="s-prep"
						type="number"
						min="0"
						max="240"
						class={inputClass(errors, 'min_prep_minutes')}
						bind:value={form.min_prep_minutes}
					/>
					<p class="mt-1 text-xs text-ink-muted">{t('admin.settings.prepHint')}</p>
					{@render fieldError(errors, 'min_prep_minutes')}
				</div>
			</div>
			<div class="mt-4 flex items-start justify-between gap-4 rounded-xl border border-line p-4">
				<div>
					<p class="text-sm font-semibold text-ink">{t('admin.settings.accepting')}</p>
					<p class="text-xs text-ink-muted">{t('admin.settings.acceptingHint')}</p>
				</div>
				<Toggle
					checked={form.accepting_orders}
					disabled={!isAdmin}
					label={t('admin.settings.accepting')}
					onchange={(v) => form && (form.accepting_orders = v)}
				/>
			</div>
		</fieldset>

		<fieldset class="card p-5 sm:p-6" disabled={!isAdmin}>
			<legend class="sr-only">{t('admin.settings.payments')}</legend>
			<h2 class="flex items-center gap-2 text-base font-bold">
				<Wallet class="size-5 text-brand-600" />{t('admin.settings.payments')}
			</h2>
			<div class="mt-4 grid gap-4 md:grid-cols-2">
				<div>
					<label class="label" for="s-expiry">{t('admin.settings.expiry')}</label>
					<input
						id="s-expiry"
						type="number"
						min="2"
						max="120"
						class={inputClass(errors, 'payment_expiry_minutes')}
						bind:value={form.payment_expiry_minutes}
					/>
					<p class="mt-1 text-xs text-ink-muted">{t('admin.settings.expiryHint')}</p>
					{@render fieldError(errors, 'payment_expiry_minutes')}
				</div>
				<div>
					<label class="label" for="s-threshold">{t('admin.settings.threshold')}</label>
					<input
						id="s-threshold"
						type="number"
						min="0"
						class={inputClass(errors, 'low_stock_threshold')}
						bind:value={form.low_stock_threshold}
					/>
					<p class="mt-1 text-xs text-ink-muted">{t('admin.settings.thresholdHint')}</p>
					{@render fieldError(errors, 'low_stock_threshold')}
				</div>
			</div>
		</fieldset>

		<fieldset class="card p-5 sm:p-6" disabled={!isAdmin}>
			<legend class="sr-only">{t('admin.settings.social')}</legend>
			<h2 class="flex items-center gap-2 text-base font-bold">
				<Share2 class="size-5 text-brand-600" />{t('admin.settings.social')}
			</h2>
			<div class="mt-4 grid gap-4 md:grid-cols-3">
				{#each [['facebook_url', 'admin.settings.facebook'], ['telegram_url', 'admin.settings.telegram'], ['instagram_url', 'admin.settings.instagram']] as [key, label] (key)}
					{@const field = key as 'facebook_url' | 'telegram_url' | 'instagram_url'}
					<div>
						<label class="label" for="s-{key}">{t(label)}</label>
						<input
							id="s-{key}"
							type="url"
							placeholder="https://"
							maxlength="200"
							class={inputClass(errors, key)}
							bind:value={form[field]}
						/>
						{@render fieldError(errors, key)}
					</div>
				{/each}
			</div>
		</fieldset>

		{#if isAdmin}
			<div class="flex justify-end">
				<button type="submit" class="btn btn-primary btn-lg" disabled={saving}>
					{#if saving}<LoaderCircle class="size-5 animate-spin" />{t('admin.saving')}{:else}{t(
							'admin.settings.save'
						)}{/if}
				</button>
			</div>
		{/if}
	</form>

	{#if isAdmin}
		<section class="card mt-8 overflow-hidden">
			<div class="flex flex-wrap items-start justify-between gap-3 px-5 py-4 sm:px-6">
				<div>
					<h2 class="text-base font-bold">{t('admin.settings.team')}</h2>
					<p class="mt-0.5 max-w-xl text-sm text-ink-muted">{t('admin.settings.teamSub')}</p>
				</div>
				<button type="button" class="btn btn-secondary" onclick={openStaff}
					><UserPlus class="size-4" />{t('admin.settings.addStaff')}</button
				>
			</div>
			{#if staff.length === 0}
				<p class="border-t border-line px-6 py-8 text-center text-sm text-ink-muted">
					{t('admin.settings.noTeam')}
				</p>
			{:else}
				<div class="overflow-x-auto">
					<table class="w-full min-w-[640px] text-left text-sm">
						<thead
							class="border-y border-line bg-canvas text-xs font-semibold whitespace-nowrap text-ink-muted"
						>
							<tr>
								<th class="px-6 py-3">{t('admin.col.name')}</th>
								<th class="px-3 py-3">{t('admin.col.email')}</th>
								<th class="px-3 py-3">{t('admin.col.role')}</th>
								<th class="px-6 py-3 text-right">{t('admin.col.active')}</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-line">
							{#each staff as member (member.id)}
								{@const me = member.id === data.user.id}
								<tr class={member.is_active ? '' : 'opacity-60'}>
									<td class="px-6 py-3 font-semibold text-ink">
										{member.name}
										{#if me}<span class="chip ml-1 bg-brand-50 text-brand-700"
												>{t('admin.settings.you')}</span
											>{/if}
										{#if !member.is_active}<span class="chip ml-1 bg-slate-100 text-slate-600"
												>{t('admin.settings.inactive')}</span
											>{/if}
									</td>
									<td class="px-3 py-3 text-ink-muted">{member.email}</td>
									<td class="px-3 py-3">
										<select
											class="rounded-xl py-1.5 text-sm"
											value={member.role}
											disabled={me}
											aria-label={t('admin.settings.roleFor', { name: member.name })}
											onchange={(e) => changeStaff(member, { role: e.currentTarget.value as Role })}
										>
											<option value="staff">{t('admin.role.staff')}</option>
											<option value="admin">{t('admin.role.admin')}</option>
										</select>
									</td>
									<td class="px-6 py-3 text-right">
										<Toggle
											size="sm"
											checked={member.is_active}
											disabled={me}
											label={t('admin.settings.activeToggle', { name: member.name })}
											onchange={(v) => changeStaff(member, { is_active: v })}
										/>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</section>

		<Modal bind:open={staffOpen} title={t('admin.settings.addStaff')} size="sm">
			<form id="staff-form" class="space-y-4" novalidate onsubmit={addStaff}>
				<div>
					<label class="label" for="st-name">{t('admin.settings.staffName')}</label>
					<input
						id="st-name"
						type="text"
						maxlength="80"
						class={inputClass(staffErrors, 'name')}
						bind:value={staffForm.name}
					/>
					{@render fieldError(staffErrors, 'name')}
				</div>
				<div>
					<label class="label" for="st-email">{t('admin.settings.staffEmail')}</label>
					<input
						id="st-email"
						type="email"
						autocomplete="off"
						class={inputClass(staffErrors, 'email')}
						bind:value={staffForm.email}
					/>
					{@render fieldError(staffErrors, 'email')}
				</div>
				<div class="grid gap-4 sm:grid-cols-2">
					<div>
						<label class="label" for="st-phone">{t('admin.settings.staffPhone')}</label>
						<input
							id="st-phone"
							type="tel"
							class={inputClass(staffErrors, 'phone')}
							bind:value={staffForm.phone}
						/>
						{@render fieldError(staffErrors, 'phone')}
					</div>
					<div>
						<label class="label" for="st-role">{t('admin.settings.staffRole')}</label>
						<select id="st-role" class="w-full rounded-xl" bind:value={staffForm.role}>
							<option value="staff">{t('admin.role.staff')}</option>
							<option value="admin">{t('admin.role.admin')}</option>
						</select>
					</div>
				</div>
				<div>
					<label class="label" for="st-password">{t('admin.settings.staffPassword')}</label>
					<input
						id="st-password"
						type="password"
						autocomplete="new-password"
						class={inputClass(staffErrors, 'password')}
						bind:value={staffForm.password}
					/>
					<p class="mt-1 text-xs text-ink-muted">{t('admin.settings.staffPasswordHint')}</p>
					{@render fieldError(staffErrors, 'password')}
				</div>
			</form>
			{#snippet footer()}
				<button type="button" class="btn btn-secondary" onclick={() => (staffOpen = false)}
					>{t('common.cancel')}</button
				>
				<button type="submit" form="staff-form" class="btn btn-primary" disabled={creating}>
					{#if creating}<LoaderCircle class="size-4 animate-spin" />{/if}{t(
						'admin.settings.addStaff'
					)}
				</button>
			{/snippet}
		</Modal>
	{/if}
{/if}
