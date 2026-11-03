import { api, type Fetch } from './api';
import type { Category, Food, FoodInput, Page, PublicSettings } from '#lib/types/api.ts';

export interface FoodQuery {
	category?: string;
	search?: string;
	sort?: 'featured' | 'price_asc' | 'price_desc' | 'name' | 'newest';
	featured?: boolean;
	available_only?: boolean;
	include_archived?: boolean;
	page?: number;
	page_size?: number;
}

export const listFoods = (query: FoodQuery = {}, fetch?: Fetch) =>
	api<Page<Food>>('/foods', { query: { page_size: 100, ...query }, fetch });

export const getFood = (id: number, fetch?: Fetch) => api<Food>(`/foods/${id}`, { fetch });

export const createFood = (body: FoodInput) => api<Food>('/foods', { method: 'POST', body });

export const updateFood = (id: number, body: Partial<FoodInput> & { is_archived?: boolean }) =>
	api<Food>(`/foods/${id}`, { method: 'PATCH', body });

export const archiveFood = (id: number) => api<Food>(`/foods/${id}`, { method: 'DELETE' });

export const listCategories = (fetch?: Fetch) => api<Category[]>('/categories', { fetch });

export const createCategory = (body: Pick<Category, 'name_en' | 'name_km'> & Partial<Category>) =>
	api<Category>('/categories', { method: 'POST', body });

export const updateCategory = (id: number, body: Partial<Category>) =>
	api<Category>(`/categories/${id}`, { method: 'PATCH', body });

export const deleteCategory = (id: number) => api<void>(`/categories/${id}`, { method: 'DELETE' });

export const getPublicSettings = (fetch?: Fetch) => api<PublicSettings>('/settings', { fetch });

export async function uploadImage(file: File) {
	const form = new FormData();
	form.append('file', file);
	return api<{ url: string; width: number; height: number; size_bytes: number }>(
		'/admin/uploads/images',
		{ method: 'POST', body: form }
	);
}
