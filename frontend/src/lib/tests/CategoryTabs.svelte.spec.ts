import { describe, expect, it, vi } from 'vitest';
import { render } from 'vitest-browser-svelte';
import CategoryTabs from '#lib/components/food/CategoryTabs.svelte';
import { i18n } from '#lib/i18n/index.svelte.ts';
import type { Category } from '#lib/types/api.ts';

const categories: Category[] = [
	{
		id: 1,
		slug: 'rice',
		name_en: 'Rice',
		name_km: 'បាយ',
		sort_order: 1,
		created_at: '',
		food_count: 5
	},
	{
		id: 2,
		slug: 'drinks',
		name_en: 'Drinks',
		name_km: 'ភេសជ្ជៈ',
		sort_order: 2,
		created_at: '',
		food_count: 4
	},
	{
		id: 3,
		slug: 'empty',
		name_en: 'Empty',
		name_km: 'ទទេ',
		sort_order: 3,
		created_at: '',
		food_count: 0
	}
];

describe('CategoryTabs', () => {
	it('shows All plus non-empty categories and reports the selection', async () => {
		i18n.locale = 'en';
		const onchange = vi.fn();
		const screen = render(CategoryTabs, { categories, onchange });
		await expect
			.element(screen.getByRole('button', { name: 'All' }))
			.toHaveAttribute('aria-pressed', 'true');
		expect(screen.getByRole('button', { name: 'Empty' }).query()).toBeNull();
		await screen.getByRole('button', { name: 'Drinks' }).click();
		expect(onchange).toHaveBeenCalledWith('drinks');
		await expect
			.element(screen.getByRole('button', { name: 'Drinks' }))
			.toHaveAttribute('aria-pressed', 'true');
	});

	it('translates category names', async () => {
		i18n.locale = 'km';
		const screen = render(CategoryTabs, { categories });
		await expect.element(screen.getByRole('button', { name: 'ទាំងអស់' })).toBeInTheDocument();
		await expect.element(screen.getByRole('button', { name: 'ភេសជ្ជៈ' })).toBeInTheDocument();
	});
});
