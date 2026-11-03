<script lang="ts">
	import Modal from '#lib/components/ui/Modal.svelte';
	import CartPanel from './CartPanel.svelte';
	import { cart } from '#lib/stores/cart.svelte.ts';
	import { t } from '#lib/i18n/index.svelte.ts';
</script>

<Modal bind:open={cart.drawerOpen} title={t('cart.title')} variant="drawer">
	<div class="-mx-5 -my-5 h-[calc(100%+2.5rem)] sm:-mx-6">
		<CartPanel bordered={false} heading={false} onnavigate={() => (cart.drawerOpen = false)} />
	</div>
</Modal>
