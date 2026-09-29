import { useEffect, useState } from 'react';
import { api, ApiError } from '../api/client';
import type { Collection, Title } from '../api/types';
import CollectionMenu from './CollectionMenu';
import ConfirmDialog from './ConfirmDialog';
import FilmStrip from './FilmStrip';
import PosterCard from './PosterCard';
import { matchesQuery } from '../lib/search';
import styles from './View.module.css';

interface Props {
  collections: Collection[];
  /** When set, shows only films matching this search, across the whole library. */
  query?: string;
  onChanged: () => void;
  onUnauthorized: () => void;
}

type Filter = 'all' | 'unsorted';

/** Films synced from Stremio are removed there, not here (see ROADMAP, Milestone 5). */
function canDelete(title: Title): boolean {
  return !title.sources.includes('stremio');
}

export default function LibraryView({
  collections,
  query = '',
  onChanged,
  onUnauthorized,
}: Props) {
  const [titles, setTitles] = useState<Title[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Title | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  // Films filed while viewing Unsorted stay visible until the filter changes,
  // so a poster doesn't vanish while its menu is still open
  const [justFiled, setJustFiled] = useState<Set<number>>(new Set());

  useEffect(() => {
    let cancelled = false;
    api
      .listTitles()
      .then((data) => {
        if (!cancelled) setTitles(data);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) onUnauthorized();
        else setError('Could not load your library.');
      });
    return () => {
      cancelled = true;
    };
  }, [onUnauthorized]);

  function changeFilter(next: Filter) {
    setFilter(next);
    setJustFiled(new Set());
  }

  function setCollectionIds(titleId: number, collectionIds: number[]) {
    setTitles((current) =>
      current
        ? current.map((t) => (t.id === titleId ? { ...t, collection_ids: collectionIds } : t))
        : current,
    );
  }

  async function toggleCollection(title: Title, collectionId: number) {
    const before = title.collection_ids;
    const inCollection = before.includes(collectionId);
    const after = inCollection
      ? before.filter((id) => id !== collectionId)
      : [...before, collectionId];

    // Update the screen right away, and undo it if the request fails
    setCollectionIds(title.id, after);
    if (filter === 'unsorted') setJustFiled((current) => new Set(current).add(title.id));
    setError(null);
    try {
      if (inCollection) await api.removeFromCollection(collectionId, title.id);
      else await api.addToCollection(collectionId, title.id);
      onChanged();
    } catch (err) {
      setCollectionIds(title.id, before);
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      else setError(`Could not update the collections for ${title.name}.`);
    }
  }

  async function handleDelete(title: Title) {
    if (!titles) return;
    const previous = titles;
    setTitles(titles.filter((t) => t.id !== title.id));
    setError(null);
    try {
      await api.deleteTitle(title.id);
      onChanged();
    } catch (err) {
      setTitles(previous);
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      else setError(`Could not delete ${title.name}.`);
    }
  }

  function collectionNames(title: Title): string[] {
    // In sidebar order, so the note reads the same way as the menu
    return collections
      .filter((c) => title.collection_ids.includes(c.id))
      .map((c) => c.name);
  }

  function deleteMessage(title: Title): string {
    const names = collectionNames(title);
    const also = names.length > 0 ? ` and removed from ${names.join(', ')}` : '';
    return `${title.name} will be deleted from your library${also}.`;
  }

  const unsortedCount = titles?.filter((t) => t.collection_ids.length === 0).length ?? 0;
  const searching = query.trim() !== '';
  const visible = !titles
    ? titles
    : searching
      ? titles.filter((t) => matchesQuery(t, query))
      : filter === 'unsorted'
        ? titles.filter((t) => t.collection_ids.length === 0 || justFiled.has(t.id))
        : titles;

  const meta = !titles || !visible
    ? ' '
    : searching
      ? `${visible.length} ${visible.length === 1 ? 'film matches' : 'films match'} “${query.trim()}”`
      : filter === 'all'
        ? `${titles.length} ${titles.length === 1 ? 'film' : 'films'} in your library`
        : `${unsortedCount} ${unsortedCount === 1 ? 'film' : 'films'} not in a collection yet`;

  return (
    <section className={styles.view} aria-labelledby="view-title">
      <header className={styles.header}>
        <h1 id="view-title" className={styles.title}>
          {searching ? 'Search' : 'All'}
        </h1>
        <p className={styles.meta}>{meta}</p>
        {!searching && (
          <div className={styles.segmented} role="group" aria-label="Show">
            <button
              type="button"
              className={styles.segment}
              aria-pressed={filter === 'all'}
              onClick={() => changeFilter('all')}
            >
              All films
            </button>
            <button
              type="button"
              className={styles.segment}
              aria-pressed={filter === 'unsorted'}
              onClick={() => changeFilter('unsorted')}
            >
              Unsorted
              {titles && <span className={styles.segmentCount}>{unsortedCount}</span>}
            </button>
          </div>
        )}
      </header>

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      {titles === null && !error && <p className={styles.status}>Loading…</p>}
      {titles && titles.length === 0 && (
        <p className={styles.status}>Your library is empty.</p>
      )}
      {titles && titles.length > 0 && visible && visible.length === 0 && (
        <p className={styles.status}>
          {searching
            ? 'No films in your library match this search.'
            : 'Every film is in at least one collection.'}
        </p>
      )}

      {visible && visible.length > 0 && (
        <FilmStrip>
          {visible.map((title) => {
            const names = collectionNames(title);
            return (
              <li key={title.id}>
                <PosterCard
                  title={title}
                  removeLabel={`Delete ${title.name} from your library`}
                  onRemove={canDelete(title) ? () => setPendingDelete(title) : undefined}
                  note={names.length > 0 ? names.join(' · ') : undefined}
                  menu={
                    <CollectionMenu
                      titleName={title.name}
                      collections={collections}
                      selectedIds={title.collection_ids}
                      onToggle={(collectionId) => toggleCollection(title, collectionId)}
                    />
                  }
                />
              </li>
            );
          })}
        </FilmStrip>
      )}

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete from library?"
        message={pendingDelete ? deleteMessage(pendingDelete) : ''}
        confirmLabel="Delete"
        onConfirm={() => {
          if (pendingDelete) handleDelete(pendingDelete);
          setPendingDelete(null);
        }}
        onCancel={() => setPendingDelete(null)}
      />
    </section>
  );
}
