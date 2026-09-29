import { useEffect, useState } from 'react';
import { api, ApiError } from '../api/client';
import type { Collection, Title } from '../api/types';
import ConfirmDialog from './ConfirmDialog';
import FilmStrip from './FilmStrip';
import PosterCard from './PosterCard';
import styles from './View.module.css';

interface Props {
  collections: Collection[];
  onChanged: () => void;
  onUnauthorized: () => void;
}

/** Films synced from Stremio are removed there, not here (see ROADMAP, Milestone 5). */
function canDelete(title: Title): boolean {
  return !title.sources.includes('stremio');
}

export default function LibraryView({ collections, onChanged, onUnauthorized }: Props) {
  const [titles, setTitles] = useState<Title[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<Title | null>(null);

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
    return title.collection_ids
      .map((id) => collections.find((c) => c.id === id)?.name)
      .filter((name): name is string => Boolean(name));
  }

  function deleteMessage(title: Title): string {
    const names = collectionNames(title);
    const also = names.length > 0 ? ` and removed from ${names.join(', ')}` : '';
    return `${title.name} will be deleted from your library${also}.`;
  }

  const count = titles?.length ?? 0;

  return (
    <section className={styles.view} aria-labelledby="view-title">
      <header className={styles.header}>
        <h1 id="view-title" className={styles.title}>
          All
        </h1>
        <p className={styles.meta}>
          {titles ? `${count} ${count === 1 ? 'film' : 'films'} in your library` : ' '}
        </p>
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

      {titles && titles.length > 0 && (
        <FilmStrip>
          {titles.map((title) => (
            <li key={title.id}>
              <PosterCard
                title={title}
                removeLabel={`Delete ${title.name} from your library`}
                onRemove={canDelete(title) ? () => setPendingDelete(title) : undefined}
              />
            </li>
          ))}
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