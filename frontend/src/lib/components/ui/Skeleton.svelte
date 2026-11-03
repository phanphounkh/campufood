<script lang="ts">
	let { class: className = '' }: { class?: string } = $props();
</script>

<div class="animate-pulse rounded-xl bg-brand-50/80 {className}" aria-hidden="true"></div>
