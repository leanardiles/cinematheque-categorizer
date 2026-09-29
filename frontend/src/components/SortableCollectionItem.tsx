import type { KeyboardEventHandler, PointerEventHandler } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import type { Collection } from '../api/types';
import styles from './Sidebar.module.css';

interface Props {
  collection: Collection;
  selected: boolean;
  onSelect: () => void;
}

/**
 * A collection in the sidebar that can be dragged to a new position.
 * Mouse and touch: drag the whole item (a short move starts the drag, so a
 * plain click still opens the collection). Keyboard: focus the grip handle,
 * press Space to pick it up, arrow keys to move, Space to drop, Escape to cancel.
 */
export default function SortableCollectionItem({ collection, selected, onSelect }: Props) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: collection.id });

  // dnd-kit types its listeners loosely; name the two handlers used below
  const onPointerDown = listeners?.onPointerDown as PointerEventHandler | undefined;
  const onKeyDown = listeners?.onKeyDown as KeyboardEventHandler | undefined;

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={styles.row}
      data-dragging={isDragging || undefined}
      // Pointer dragging from anywhere on the row
      onPointerDown={onPointerDown}
    >
      <button
        ref={setActivatorNodeRef}
        type="button"
        className={styles.handle}
        aria-label={`Reorder ${collection.name}`}
        {...attributes}
        // Keyboard dragging only from the handle, so Enter and Space on the
        // collection itself keep opening it
        onKeyDown={onKeyDown}
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <circle cx="9" cy="6" r="1.6" />
          <circle cx="15" cy="6" r="1.6" />
          <circle cx="9" cy="12" r="1.6" />
          <circle cx="15" cy="12" r="1.6" />
          <circle cx="9" cy="18" r="1.6" />
          <circle cx="15" cy="18" r="1.6" />
        </svg>
      </button>
      <button
        type="button"
        className={styles.item}
        aria-current={selected ? 'page' : undefined}
        onClick={onSelect}
      >
        {collection.name}
        <span className={styles.count}>{collection.title_count}</span>
      </button>
    </div>
  );
}
