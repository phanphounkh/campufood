<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import AuthCard from '#lib/components/layout/AuthCard.svelte';
	import { register } from '#lib/services/auth.ts';
	import { ApiError } from '#lib/services/api.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { registerSchema, fieldErrors } from '#lib/utils/validation.ts';
	import { t } from '#lib/i18n/index.svelte.ts';

	let form = $state({ name: '', email: '', phone: '', password: '' });
	let errors = $state<Record<string, string>>({});
	let formError = $state('');
	let busy = $state(false);

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		formError = '';
		const parsed = registerSchema.safeParse(form);
		if (!parsed.success) {
			errors = fieldErrors(parsed.error);
			return;
		}
		errors = {};
		busy = true;
		try {
			const session = await register({ ...parsed.data, phone: parsed.data.phone || undefined });
			toast.success(t('auth.welcome', { name: session.user.name }));
			await invalidateAll();
			await goto('/menu');
		} catch (err) {
			if (err instanceof ApiError && err.code === 'VALIDATION_ERROR') errors = err.fieldErrors;
			formError = err instanceof Error ? err.message : t('common.errorTitle');
		} finally {
			busy = false;
		}
	}

	const fields = [
		{ name: 'name', type: 'text', label: 'auth.name', autocomplete: 'name' },
		{ name: 'email', type: 'email', label: 'auth.email', autocomplete: 'email' },
		{ name: 'phone', type: 'tel', label: 'auth.phone', autocomplete: 'tel' },
		{ name: 'password', type: 'password', label: 'auth.password', autocomplete: 'new-password' }
	] as const;
</script>

<svelte:head><title>{t('nav.register')} · CampusEats</title></svelte:head>

<AuthCard title={t('auth.registerTitle')} subtitle={t('auth.registerSubtitle')}>
	<form class="space-y-4" novalidate onsubmit={submit}>
		{#each fields as field (field.name)}
			<div>
				<label class="label" for={field.name}>
					{t(field.label)}
					{#if field.name === 'phone'}<span class="font-normal text-ink-muted"
							>({t('common.optional')})</span
						>{/if}
				</label>
				<input
					id={field.name}
					type={field.type}
					autocomplete={field.autocomplete}
					bind:value={form[field.name]}
					class="w-full"
					aria-invalid={!!errors[field.name]}
				/>
				{#if errors[field.name]}<p class="field-error">{t(errors[field.name])}</p>{/if}
			</div>
		{/each}
		{#if formError}<p class="rounded-xl bg-red-50 p-3 text-sm font-medium text-danger-ink" role="alert">
				{formError}
			</p>{/if}
		<button type="submit" class="btn btn-primary btn-lg w-full" disabled={busy}>
			{#if busy}<LoaderCircle class="size-4 animate-spin" />{/if}{t('auth.submitRegister')}
		</button>
	</form>
	<p class="mt-6 text-center text-sm text-ink-muted">
		{t('auth.haveAccount')}
		<a href="/login" class="font-semibold text-brand-700 hover:underline">{t('nav.login')}</a>
	</p>
</AuthCard>
