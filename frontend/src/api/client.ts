import type { Collection, Me, SearchResult, Title, TitleType } from './types';

const API_URL = import.meta.env.VITE_API_URL.replace(/\/$/, '');
const TOKEN_KEY = 'cinematheque.apiToken';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const tokenStore = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; token?: string } = {},
): Promise<T> {
  const token = options.token ?? tokenStore.get();
  const response = await fetch(`${API_URL}${path}`, {
    method: options.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (!response.ok) {
    let message = response.statusText;
    try {
      const data = await response.json();
      if (typeof data.detail === 'string') message = data.detail;
    } catch {
      // No JSON body; keep the status text
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const api = {
  // Auth
  me: (token?: string) => request<Me>('/api/me', { token }),

  // Collections
  listCollections: () => request<Collection[]>('/api/collections'),
  createCollection: (name: string, description?: string) =>
    request<Collection>('/api/collections', {
      method: 'POST',
      body: { name, description: description ?? null },
    }),
  updateCollection: (id: number, changes: { name?: string; description?: string | null }) =>
    request<Collection>(`/api/collections/${id}`, { method: 'PATCH', body: changes }),
  deleteCollection: (id: number) =>
    request<void>(`/api/collections/${id}`, { method: 'DELETE' }),
  reorderCollections: (ids: number[]) =>
    request<Collection[]>('/api/collections/order', { method: 'PUT', body: { ids } }),

  // Collection contents
  listCollectionTitles: (collectionId: number) =>
    request<Title[]>(`/api/collections/${collectionId}/titles`),
  addToCollection: (collectionId: number, titleId: number) =>
    request<Title[]>(`/api/collections/${collectionId}/titles`, {
      method: 'POST',
      body: { title_id: titleId },
    }),
  removeFromCollection: (collectionId: number, titleId: number) =>
    request<void>(`/api/collections/${collectionId}/titles/${titleId}`, { method: 'DELETE' }),
  reorderCollectionTitles: (collectionId: number, ids: number[]) =>
    request<Title[]>(`/api/collections/${collectionId}/titles/order`, {
      method: 'PUT',
      body: { ids },
    }),

  // Library
  listTitles: (params: { q?: string; unsorted?: boolean } = {}) => {
    const query = new URLSearchParams();
    if (params.q) query.set('q', params.q);
    if (params.unsorted) query.set('unsorted', 'true');
    const suffix = query.toString() ? `?${query}` : '';
    return request<Title[]>(`/api/titles${suffix}`);
  },
  addTitle: (
    body:
      | { imdb_id: string; collection_ids?: number[] }
      | { tmdb_id: number; type: TitleType; collection_ids?: number[] },
  ) => request<Title>('/api/titles', { method: 'POST', body }),
  renameTitle: (id: number, name: string) =>
    request<Title>(`/api/titles/${id}`, { method: 'PATCH', body: { name } }),
  deleteTitle: (id: number) => request<void>(`/api/titles/${id}`, { method: 'DELETE' }),

  // Search
  search: (q: string, type: TitleType = 'movie') =>
    request<SearchResult[]>(
      `/api/search?${new URLSearchParams({ q, type })}`,
    ),
};