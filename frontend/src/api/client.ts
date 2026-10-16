import type {
  AddonLink,
  Collection,
  LoginResult,
  Me,
  SearchResult,
  StremioConnectResult,
  Title,
  TitleType,
} from './types';

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

/**
 * Signs in from an invite link (…/#invite=<token>): saves the token and
 * removes it from the address bar, so it isn't left in the history or
 * copied along with the address. Runs once, before the app renders.
 */
let openedInvite = false;

/** Whether this visit started from an invite link (to explain a used-up link). */
export const openedFromInvite = () => openedInvite;

export function takeInviteToken(): void {
  const match = window.location.hash.match(/^#invite=([\w-]+)$/);
  if (!match) return;
  openedInvite = true;
  tokenStore.set(match[1]);
  const { pathname, search } = window.location;
  window.history.replaceState(null, '', pathname + search);
}

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
  // Account
  me: (token?: string) => request<Me>('/api/me', { token }),
  login: (email: string, password: string) =>
    request<LoginResult>('/api/login', { method: 'POST', body: { email, password } }),
  logout: (token?: string) => request<void>('/api/logout', { method: 'POST', token }),
  setLogin: (body: { email: string; password: string; current_password?: string }) =>
    request<LoginResult & { email: string }>('/api/me/login', { method: 'POST', body }),
  connectStremio: (
    credentials: { email: string; password: string } | { auth_key: string },
  ) =>
    request<StremioConnectResult>('/api/stremio/connect', {
      method: 'POST',
      body: credentials,
    }),
  disconnectStremio: () => request<void>('/api/stremio/connect', { method: 'DELETE' }),
  addonLink: () => request<AddonLink>('/api/me/addon-link', { method: 'POST' }),

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
  /** An empty or null note clears it. */
  setNote: (id: number, note: string | null) =>
    request<Title>(`/api/titles/${id}`, { method: 'PATCH', body: { note: note ?? '' } }),
  deleteTitle: (id: number) => request<void>(`/api/titles/${id}`, { method: 'DELETE' }),

  // Search
  search: (q: string, type: TitleType = 'movie') =>
    request<SearchResult[]>(
      `/api/search?${new URLSearchParams({ q, type })}`,
    ),
};