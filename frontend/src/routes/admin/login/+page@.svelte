<script lang="ts">
	import { resolve } from '$app/paths';
	import { goto } from '$app/navigation';
	import Eye from '@lucide/svelte/icons/eye';
	import EyeOff from '@lucide/svelte/icons/eye-off';
	import ShieldCheck from '@lucide/svelte/icons/shield-check';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import Logo from '#lib/components/ui/Logo.svelte';
	import LanguageSwitcher from '#lib/components/ui/LanguageSwitcher.svelte';
	import { login } from '#lib/services/auth.ts';
	import { ApiError } from '#lib/services/api.ts';
	import { fieldErrors, loginSchema } from '#lib/utils/validation.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	let email = $state('');
	let password = $state('');
	let showPassword = $state(false);
	let submitting = $state(false);
	let errors = $state<Record<string, string>>({});
	// svelte-ignore state_referenced_locally
	let formError = $state(data.forbidden ? t('admin.login.forbidden') : '');

	async function submit(event: SubmitEvent) {
		event.preventDefault();
		formError = '';
		const parsed = loginSchema.safeParse({ email, password });
		if (!parsed.success) {
			errors = fieldErrors(parsed.error);
			return;
		}
		errors = {};
		submitting = true;
		try {
			await login(parsed.data.email, parsed.data.password, true);
			await goto(data.next, { refreshAll: true });
		} catch (err) {
			if (err instanceof ApiError && err.status === 401) formError = t('admin.login.invalid');
			else if (err instanceof ApiError && err.status === 403)
				formError = t('admin.login.forbidden');
			else if (err instanceof ApiError && err.status === 429)
				formError = t('admin.login.rateLimited');
			else formError = err instanceof Error ? err.message : t('admin.loadError');
			submitting = false;
		}
	}
</script>

<svelte:head><title>{t('admin.login.title')} · CampusEats</title></svelte:head>

<main class="relative grid min-h-dvh place-items-center overflow-hidden bg-navy px-4 py-10">
	<div
		class="pointer-events-none absolute -top-40 -left-32 size-[28rem] rounded-full bg-brand-600/30 blur-3xl"
		aria-hidden="true"
	></div>
	<div
		class="pointer-events-none absolute -right-24 -bottom-40 size-[26rem] rounded-full bg-brand-400/20 blur-3xl"
		aria-hidden="true"
	></div>

	<div class="relative w-full max-w-md">
		<div class="mb-6 flex items-center justify-between">
			<Logo variant="dark" subtitle={t('admin.subtitle')} />
			<LanguageSwitcher tone="dark" />
		</div>

		<div class="rounded-3xl bg-white p-7 shadow-2xl sm:p-8">
			<div class="grid size-12 place-items-center rounded-2xl bg-brand-50 text-brand-600">
				<ShieldCheck class="size-6" />
			</div>
			<h1 class="mt-5 text-2xl font-extrabold tracking-tight">{t('admin.login.title')}</h1>
			<p class="mt-1 text-sm text-ink-muted">{t('admin.login.subtitle')}</p>

			{#if formError}
				<div
					class="mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
					role="alert"
				>
					{formError}
				</div>
			{/if}

			<form class="mt-6 space-y-4" novalidate onsubmit={submit}>
				<div>
					<label class="label" for="email">{t('admin.login.email')}</label>
					<input
						id="email"
						type="email"
						class="w-full"
						autocomplete="username"
						bind:value={email}
						aria-invalid={!!errors.email}
						aria-describedby={errors.email ? 'email-error' : undefined}
					/>
					{#if errors.email}<p id="email-error" class="field-error">{t(errors.email)}</p>{/if}
				</div>
				<div>
					<label class="label" for="password">{t('admin.login.password')}</label>
					<div class="relative">
						<input
							id="password"
							type={showPassword ? 'text' : 'password'}
							class="w-full pr-11"
							autocomplete="current-password"
							bind:value={password}
							aria-invalid={!!errors.password}
							aria-describedby={errors.password ? 'password-error' : undefined}
						/>
						<button
							type="button"
							class="absolute top-1/2 right-1.5 grid size-8 -translate-y-1/2 place-items-center rounded-lg text-ink-muted hover:bg-brand-50 hover:text-ink"
							aria-label={showPassword
								? t('admin.login.hidePassword')
								: t('admin.login.showPassword')}
							onclick={() => (showPassword = !showPassword)}
						>
							{#if showPassword}<EyeOff class="size-4" />{:else}<Eye class="size-4" />{/if}
						</button>
					</div>
					{#if errors.password}
						<p id="password-error" class="field-error">{t(errors.password)}</p>
					{/if}
				</div>
				<button type="submit" class="btn btn-primary btn-lg w-full" disabled={submitting}>
					{#if submitting}
						<LoaderCircle class="size-5 animate-spin" />{t('admin.login.submitting')}
					{:else}
						{t('admin.login.submit')}
					{/if}
				</button>
			</form>
			<p class="mt-6 text-xs text-ink-muted">{t('admin.login.secure')}</p>
		</div>

		<a
			href={resolve('/(client)')}
			class="mx-auto mt-6 flex w-fit items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-white/70 hover:text-white"
		>
			<ArrowLeft class="size-4" />{t('admin.login.back')}
		</a>
	</div>
</main>
