export type TitleType = 'movie' | 'series';

export interface Collection {
  id: number;
  name: string;
  description: string | null;
  position: number;
  title_count: number;
}

export interface Title {
  id: number;
  imdb_id: string;
  type: TitleType;
  name: string;
  original_title: string | null;
  english_name: string | null;
  original_language: string | null;
  year: number | null;
  poster: string | null;
  collection_ids: number[];
  sources: string[];
  /** ISO date: when the film was saved to the library */
  added_at: string;
  /** The user's own note, up to 120 characters */
  note: string | null;
}

export const NOTE_MAX = 120;

export interface SearchResult {
  tmdb_id: number;
  type: TitleType;
  name: string;
  original_title: string;
  english_name: string | null;
  original_language: string | null;
  year: number | null;
  poster: string | null;
  in_library: boolean;
  title_id: number | null;
}

export interface Me {
  id: number;
  name: string;
  /** The login email, once a password login exists */
  email: string | null;
  has_password: boolean;
  /** Signed in with an invite link: time to create (or reset) the login */
  via_invite: boolean;
  stremio_connected: boolean;
}

export interface LoginResult {
  token: string;
}

export interface SyncReport {
  added: number;
  linked: number;
  removed: number;
  /** New films left for the scheduled sync */
  remaining: number;
}

export interface StremioConnectResult {
  connected: boolean;
  /** Null when the first import failed; the scheduled sync catches up */
  sync: SyncReport | null;
}

export interface AddonLink {
  manifest_url: string;
  /** stremio:// link that opens the install dialog in the Stremio app */
  app_install_url: string;
  /** Opens the install dialog in Stremio Web */
  web_install_url: string;
}