<script lang="ts">
	/** Accessible on/off switch (a checkbox with role="switch"). */
	let {
		checked,
		label,
		disabled = false,
		size = 'md',
		onchange
	}: {
		checked: boolean;
		label: string;
		disabled?: boolean;
		size?: 'sm' | 'md';
		onchange: (value: boolean) => void;
	} = $props();
</script>

<label
	class="relative inline-flex shrink-0 cursor-pointer items-center {disabled
		? 'cursor-not-allowed opacity-50'
		: ''}"
>
	<input
		type="checkbox"
		role="switch"
		class="peer sr-only"
		{checked}
		{disabled}
		aria-label={label}
		onchange={(e) => onchange(e.currentTarget.checked)}
	/>
	<span
		class="rounded-full bg-slate-300 transition peer-checked:bg-brand-600 peer-focus-visible:ring-4 peer-focus-visible:ring-brand-200
			{size === 'sm' ? 'h-5 w-9' : 'h-6 w-11'}"
	></span>
	<span
		class="absolute top-0.5 left-0.5 rounded-full bg-white shadow transition
			{size === 'sm' ? 'size-4 peer-checked:translate-x-4' : 'size-5 peer-checked:translate-x-5'}"
	></span>
</label>
