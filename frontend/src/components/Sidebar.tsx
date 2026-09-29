import { useState, type FormEvent } from 'react';
import {
  closestCenter,
  DndContext,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import { restrictToParentElement, restrictToVerticalAxis } from '@dnd-kit/modifiers';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import type { Collection } from '../api/types';
import SortableCollectionItem from './SortableCollectionItem';
import styles from './Sidebar.module.css';

export type View = { kind: 'all' } | { kind: 'collection'; id: number };

interface Props {
  collections: Collection[];
  libraryCount: number | null;
  view: View;
  onSelect: (view: View) => void;
  /** Returns an error message, or null when the collection was created. */
  onCreateCollection: (name: string) => Promise<string | null>;
  /** Called with every collection ID in the new order after a drag. */
  onReorderCollections: (ids: number[]) => void;
  onSignOut: () => void;
}

export default function Sidebar({
  collections,
  libraryCount,
  view,
  onSelect,
  onCreateCollection,
  onReorderCollections,
  onSignOut,
}: Props) {
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const sensors = useSensors(
    // A 6px move starts a drag, so a plain click still selects the collection
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  function handleDragEnd({ active, over }: DragEndEvent) {
    if (!over || active.id === over.id) return;
    const ids = collections.map((c) => c.id);
    const from = ids.indexOf(Number(active.id));
    const to = ids.indexOf(Number(over.id));
    if (from === -1 || to === -1) return;
    onReorderCollections(arrayMove(ids, from, to));
  }

  function closeForm() {
    setCreating(false);
    setName('');
    setError(null);
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    const message = await onCreateCollection(name.trim());
    setSaving(false);
    if (message) setError(message);
    else closeForm();
  }

  return (
    <nav className={styles.sidebar} aria-label="Main">
      <div className={styles.brand}>
        <div className={styles.logo}>Cinémathèque</div>
        <div className={styles.tagline}>Salle de projection</div>
      </div>

      <div className={styles.section}>
        <button
          type="button"
          className={styles.item}
          aria-current={view.kind === 'all' ? 'page' : undefined}
          onClick={() => onSelect({ kind: 'all' })}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <rect x="3" y="3" width="7" height="9" />
            <rect x="14" y="3" width="7" height="9" />
            <rect x="3" y="15" width="7" height="6" />
            <rect x="14" y="15" width="7" height="6" />
          </svg>
          All
          {libraryCount !== null && <span className={styles.count}>{libraryCount}</span>}
        </button>
      </div>

      <div className={styles.section}>
        <div className={styles.headingRow}>
          <span className={styles.heading}>Collections</span>
          <button
            type="button"
            className={styles.addButton}
            onClick={() => (creating ? closeForm() : setCreating(true))}
            aria-label="New collection"
            aria-expanded={creating}
            title="New collection"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>

        {creating && (
          <form className={styles.form} onSubmit={handleCreate}>
            <label className={styles.srOnly} htmlFor="new-collection">
              New collection name
            </label>
            <input
              id="new-collection"
              className={styles.input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') closeForm();
              }}
              placeholder="Collection name"
              maxLength={100}
              autoFocus
            />
            {error && (
              <p className={styles.error} role="alert">
                {error}
              </p>
            )}
            <div className={styles.formActions}>
              <button type="button" className={styles.secondary} onClick={closeForm}>
                Cancel
              </button>
              <button type="submit" className={styles.primary} disabled={saving || !name.trim()}>
                {saving ? 'Adding…' : 'Add'}
              </button>
            </div>
          </form>
        )}

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          modifiers={[restrictToVerticalAxis, restrictToParentElement]}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={collections.map((c) => c.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className={styles.list}>
              {collections.map((collection) => (
                <SortableCollectionItem
                  key={collection.id}
                  collection={collection}
                  selected={view.kind === 'collection' && view.id === collection.id}
                  onSelect={() => onSelect({ kind: 'collection', id: collection.id })}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      </div>

      <div className={styles.footer}>
        <button type="button" className={styles.signOut} onClick={onSignOut}>
          Sign out
        </button>
        <p className={styles.attribution}>
          This product uses the TMDB API but is not endorsed or certified by TMDB.
        </p>
      </div>
    </nav>
  );
}