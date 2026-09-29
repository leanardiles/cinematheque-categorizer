import type { Title } from '../api/types';

/** Lowercase and strip accents, so "Amélie" and "amelie" compare as equal. */
export function normalize(text: string): string {
  return text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase();
}

/**
 * True when every word of the query appears in the film's display name,
 * original title or English title. "nine queens" finds Nueve reinas;
 * "cienaga" finds La Ciénaga.
 */
export function matchesQuery(title: Title, query: string): boolean {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  if (words.length === 0) return true;
  const haystack = normalize(
    [title.name, title.original_title, title.english_name].filter(Boolean).join(' '),
  );
  return words.every((word) => haystack.includes(word));
}
