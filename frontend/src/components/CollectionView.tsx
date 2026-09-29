import { useEffect, useState, type FormEvent } from 'react';
import { api, ApiError } from '../api/client';
import type { Collection, Title } from '../api/types';
import ConfirmDialog from './ConfirmDialog';
import FilmStrip from './FilmStrip';
import PosterCard from './PosterCard';
import styles from './View.module.css';

interface Props {
  collection: Collection;
  onChanged: () => void;
  onDeleted: () => void;
  onUnauthorized: () => void;
}

export default function CollectionView({
  collection,
  onChanged,
  onDeleted,
  onUnauthorized,
}: Props) {
  const [titles, setTitles] = useState<Title[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingRemoval, setPendingRemoval] = useState<Title | null>(null);
  const [renaming, setRenaming] = useState(false);
  const [newName, setNewName] = useState(collection.name);
  const [renameError, setRenameError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

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

  function startRename() {
    setNewName(collection.name);
    setRenameError(null);
    setRenaming(true);
  }

  async function handleRename(event: FormEvent) {
    event.preventDefault();
    const name = newName.trim();
    if (!name || name === collection.name) {
      setRenaming(false);
      return;
    }
    setSaving(true);
    try {
      await api.updateCollection(collection.id, { name });
      setRenaming(false);
      onChanged();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      else if (err instanceof ApiError && err.status === 409)
        setRenameError('A collection with this name already exists.');
      else setRenameError('Could not rename the collection.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setError(null);
    try {
      await api.deleteCollection(collection.id);
      onDeleted();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      else setError('Could not delete the collection.');
    }
  }

  const count = titles?.length ?? collection.title_count;
  const filmsLeft =
    count === 0
      ? 'It has no films.'
      : `The ${count === 1 ? 'film' : `${count} films`} in it stay in All and in any other collections.`;

  return (
    <section className={styles.view} aria-labelledby="view-title">
      <header className={styles.headerRow}>
        <div className={styles.header}>
          {renaming ? (
            <form className={styles.renameForm} onSubmit={handleRename}>
              <label className={styles.srOnly} htmlFor="rename-collection">
                Collection name
              </label>
              <input
                id="rename-collection"
                className={styles.renameInput}
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') setRenaming(false);
                }}
                maxLength={100}
                autoFocus
              />
              <div className={styles.actions}>
                <button type="button" className={styles.secondary} onClick={() => setRenaming(false)}>
                  Cancel
                </button>
                <button
                  type="submit"
                  className={styles.primary}
                  disabled={saving || !newName.trim()}
                >
                  {saving ? 'Saving…' : 'Save'}
                </button>
              </div>
              {renameError && (
                <p className={styles.error} role="alert">
                  {renameError}
                </p>
              )}
            </form>
          ) : (
            <h1 id="view-title" className={styles.title}>
              {collection.name}
            </h1>
          )}
          <p className={styles.meta}>
            {count} {count === 1 ? 'film' : 'films'} · shown in Stremio as{' '}
            <span className={styles.accent}>{collection.name} Cinematheque</span>
          </p>
        </div>

        {!renaming && (
          <div className={styles.actions}>
            <button type="button" className={styles.secondary} onClick={startRename}>
              Rename
            </button>
            <button type="button" className={styles.danger} onClick={() => setConfirmDelete(true)}>
              Delete
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
        <p className={styles.status}>No films in this collection yet.</p>
      )}

      {titles && titles.length > 0 && (
        <FilmStrip>
          {titles.map((title) => (
            <li key={title.id}>
              <PosterCard
                title={title}
                removeLabel={`Remove ${title.name} from ${collection.name}`}
                onRemove={() => setPendingRemoval(title)}
              />
            </li>
          ))}
        </FilmStrip>
      )}

      <ConfirmDialog
        open={pendingRemoval !== null}
        title="Remove from collection?"
        message={
          pendingRemoval
            ? `${pendingRemoval.name} will be removed from ${collection.name}. It stays in All and in any other collections.`
            : ''
        }
        confirmLabel="Remove"
        onConfirm={() => {
          if (pendingRemoval) handleRemove(pendingRemoval);
          setPendingRemoval(null);
        }}
        onCancel={() => setPendingRemoval(null)}
      />

      <ConfirmDialog
        open={confirmDelete}
        title="Delete collection?"
        message={`${collection.name} will be deleted, and its row will disappear from Stremio. ${filmsLeft}`}
        confirmLabel="Delete collection"
        onConfirm={() => {
          setConfirmDelete(false);
          handleDelete();
        }}
        onCancel={() => setConfirmDelete(false)}
      />
    </section>
  );
}