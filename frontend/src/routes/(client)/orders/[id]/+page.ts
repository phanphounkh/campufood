import { loadOrderForGuest } from '#lib/services/orderAccess.ts';
import type { PageLoad } from './$types';

export const ssr = false;

export const load: PageLoad = ({ params, fetch }) => loadOrderForGuest(params.id, fetch);
