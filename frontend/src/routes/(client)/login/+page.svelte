<script lang="ts">
	import { goto, invalidateAll } from '$app/navigation';
	import { page } from '$app/state';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import AuthCard from '#lib/components/layout/AuthCard.svelte';
	import { login } from '#lib/services/auth.ts';
	import { toast } from '#lib/stores/toast.svelte.ts';
	import { loginSchema, fieldErrors } from '#lib/utils/validation.ts';
	import { safeNext } from '#lib/utils/redirect.ts';
	import { t } from '#lib/i18n/index.svelte.ts';

	let email = $state('');
	let password = $state('');
	let errors = $state<Record<string, string>>({});
	let formError = $state('');
	let busy = $state(false);

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		formError = '';
		const parsed = loginSchema.safeParse({ email, password });
		if (!parsed.success) {
			errors = fieldErrors(parsed.error);
			return;
		}
		errors = {};
		busy = true;
		try {
			const session = await login(parsed.data.email, parsed.data.password);
			toast.success(t('auth.welcome', { name: session.user.name }));
			const fallback = session.user.role === 'customer' ? '/orders' : '/admin';
			await invalidateAll();
			await goto(safeNext(page.url.searchParams.get('next'), fallback));
		} catch (err) {
			formError = err instanceof Error ? err.message : t('common.errorTitle');
		} finally {
			busy = false;
		}
	}
</script>

<svelte:head><title>{t('nav.login')} · CampusEats</title></svelte:head>

<AuthCard title={t('auth.loginTitle')} subtitle={t('auth.loginSubtitle')}>
	<form class="space-y-4" novalidate onsubmit={submit}>
		<div>
			<label class="label" for="email">{t('auth.email')}</label>
			<input
				id="email"
				type="email"
				autocomplete="email"
				bind:value={email}
				class="w-full"
				aria-invalid={!!errors.email}
			/>
			{#if errors.email}<p class="field-error">{t(errors.email)}</p>{/if}
		</div>
		<div>
			<label class="label" for="password">{t('auth.password')}</label>
			<input
				id="password"
				type="password"
				autocomplete="current-password"
				bind:value={password}
				class="w-full"
				aria-invalid={!!errors.password}
			/>
			{#if errors.password}<p class="field-error">{t(errors.password)}</p>{/if}
		</div>
		{#if formError}<p class="rounded-xl bg-red-50 p-3 text-sm font-medium text-danger-ink" role="alert">
				{formError}
			</p>{/if}
		<button type="submit" class="btn btn-primary btn-lg w-full" disabled={busy}>
			{#if busy}<LoaderCircle class="size-4 animate-spin" />{/if}{t('auth.submitLogin')}
		</button>
	</form>
	<p class="mt-6 text-center text-sm text-ink-muted">
		{t('auth.noAccount')}
		<a href="/register" class="font-semibold text-brand-700 hover:underline">{t('nav.register')}</a>
	</p>
</AuthCard>
