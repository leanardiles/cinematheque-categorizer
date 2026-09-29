import type { Title } from '../api/types';

/** "custom" is a collection's own order (the order Stremio shows in its row). */
export type SortKey = 'custom' | 'added' | 'title' | 'year';

export interface SortOption {
  value: SortKey;
  label: string;
}

/** Sort options for All, Unsorted and Search. */
export const LIBRARY_SORT_OPTIONS: SortOption[] = [
  { value: 'added', label: 'Last added' },
  { value: 'title', label: 'Title (A–Z)' },
  { value: 'year', label: 'Year (newest first)' },
];

/** Sort options for a collection: its own order first. */
export const COLLECTION_SORT_OPTIONS: SortOption[] = [
  { value: 'custom', label: 'Collection order' },
  ...LIBRARY_SORT_OPTIONS,
];

// Compares letters regardless of accents and case: "Ángel" sorts with "Angel"
const collator = new Intl.Collator(undefined, { sensitivity: 'base', numeric: true });

function byTitle(a: Title, b: Title): number {
  return collator.compare(a.name, b.name);
}

/** Returns a new sorted array; the input is left unchanged. */
export function sortTitles(titles: Title[], key: SortKey): Title[] {
  const sorted = [...titles];
  switch (key) {
    case 'custom':
      return sorted; // already in the order the API returned
    case 'added':
      return sorted.sort(
        (a, b) => Date.parse(b.added_at) - Date.parse(a.added_at) || byTitle(a, b),
      );
    case 'title':
      return sorted.sort(byTitle);
    case 'year':
      // Films without a year go last
      return sorted.sort((a, b) => (b.year ?? -Infinity) - (a.year ?? -Infinity) || byTitle(a, b));
  }
}

/** The last sort chosen in this browser for these options, or the first option. */
export function loadSortKey(storageKey: string, options: SortOption[]): SortKey {
  try {
    const saved = localStorage.getItem(storageKey);
    const match = options.find((option) => option.value === saved);
    if (match) return match.value;
  } catch {
    // Storage unavailable (private mode, blocked): use the default
  }
  return options[0].value;
}

export function saveSortKey(storageKey: string, key: SortKey): void {
  try {
    localStorage.setItem(storageKey, key);
  } catch {
    // Not critical: the choice just won't be remembered
  }
}
