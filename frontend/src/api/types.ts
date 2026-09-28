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
}

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
}