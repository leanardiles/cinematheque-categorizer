import { useEffect, useState } from 'react';
import { api, ApiError } from '../api/client';
import type { Collection, Title } from '../api/types';
import ConfirmDialog from './ConfirmDialog';
import PosterCard from './PosterCard';
import styles from './CollectionView.module.css';

interface Props {
  collection: Collection;
  onChanged: () => void;
  onUnauthorized: () => void;
}

const SPROCKETS = Array.from({ length: 28 }, (_, i) => i);

function Sprockets() {
  return (
    <div className={styles.sprockets} aria-hidden="true">
      {SPROCKETS.map((i) => (
        <span key={i} />
      ))}
    </div>
  );
}

export default function CollectionView({ collection, onChanged, onUnauthorized }: Props) {
  const [titles, setTitles] = useState<Title[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingRemoval, setPendingRemoval] = useState<Title | null>(null);

  useEffect(() => {
    // Ignore responses that arrive after switching to another collection
    // (App remounts this component per collection via key, so state starts fresh)
    let cancelled = false;
    api
      .listCollectionTitles(collection.id)
      .then((data) => {
        if (!cancelled) setTitles(data);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 401) onUnauthorized();
        else setError('Could not load this collection.');
      });
    return () => {
      cancelled = true;
    };
  }, [collection.id, onUnauthorized]);

  async function handleRemove(title: Title) {
    if (!titles) return;
    const previous = titles;
    // Update the screen right away, and undo it if the request fails
    setTitles(titles.filter((t) => t.id !== title.id));
    setError(null);
    try {
      await api.removeFromCollection(collection.id, title.id);
      onChanged();
    } catch (err) {
      setTitles(previous);
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      else setError(`Could not remove ${title.name}.`);
    }
  }

  const count = titles?.length ?? collection.title_count;

  return (
    <section className={styles.view} aria-labelledby="collection-title">
      <header className={styles.header}>
        <h1 id="collection-title" className={styles.title}>
          {collection.name}
        </h1>
        <p className={styles.meta}>
          {count} {count === 1 ? 'film' : 'films'} · shown in Stremio as{' '}
          <span className={styles.accent}>{collection.name} Cinematheque</span>
        </p>
      </header>

      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}

      {titles === null && !error && <p className={styles.status}>Loading…</p>}

      {titles && titles.length === 0 && (
        <p className={styles.status}>No films in this collection yet.</p>
      )}

      {titles && titles.length > 0 && (
        <div className={styles.strip}>
          <Sprockets />
          <ul className={styles.grid}>
            {titles.map((title) => (
              <li key={title.id}>
                <PosterCard
                  title={title}
                  collectionName={collection.name}
                  onRemove={() => setPendingRemoval(title)}
                />
              </li>
            ))}
          </ul>
          <Sprockets />
        </div>
      )}

      <ConfirmDialog
        open={pendingRemoval !== null}
        title="Remove from collection?"
        message={
          pendingRemoval
            ? `${pendingRemoval.name} will be removed from ${collection.name}. It stays in your library and in any other collections.`
            : ''
        }
        confirmLabel="Remove"
        onConfirm={() => {
          if (pendingRemoval) handleRemove(pendingRemoval);
          setPendingRemoval(null);
        }}
        onCancel={() => setPendingRemoval(null)}
      />
    </section>
  );
}