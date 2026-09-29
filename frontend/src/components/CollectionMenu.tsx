import { useEffect, useId, useRef, useState } from 'react';
import type { Collection } from '../api/types';
import styles from './CollectionMenu.module.css';

interface Props {
  titleName: string;
  collections: Collection[];
  selectedIds: number[];
  onToggle: (collectionId: number) => void;
}

/**
 * A button that opens a small menu of collections with checkboxes.
 * Ticking adds the film to a collection, unticking removes it; the menu stays
 * open so several collections can be changed in one go.
 * Closes with Escape, a click outside, or the button itself.
 */
export default function CollectionMenu({ titleName, collections, selectedIds, onToggle }: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const firstCheckboxRef = useRef<HTMLInputElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;
    firstCheckboxRef.current?.focus();

    function handlePointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, [open]);

  function close() {
    setOpen(false);
    buttonRef.current?.focus();
  }

  return (
    <div className={styles.root} ref={rootRef}>
      <button
        ref={buttonRef}
        type="button"
        className={styles.button}
        aria-label={`Collections for ${titleName}`}
        aria-expanded={open}
        aria-controls={menuId}
        title="Add to collection"
        onClick={() => setOpen((value) => !value)}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M6 3h12v18l-6-4-6 4z" />
          <path d="M12 7v6M9 10h6" />
        </svg>
      </button>

      {open && (
        <div
          id={menuId}
          className={styles.menu}
          role="group"
          aria-label={`Collections for ${titleName}`}
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              event.stopPropagation();
              close();
            }
          }}
        >
          <div className={styles.heading}>Add to collection</div>
          {collections.length === 0 ? (
            <p className={styles.empty}>No collections yet. Create one with + in the sidebar.</p>
          ) : (
            <ul className={styles.list}>
              {collections.map((collection, index) => (
                <li key={collection.id}>
                  <label className={styles.option}>
                    <input
                      ref={index === 0 ? firstCheckboxRef : undefined}
                      type="checkbox"
                      className={styles.checkbox}
                      checked={selectedIds.includes(collection.id)}
                      onChange={() => onToggle(collection.id)}
                    />
                    {collection.name}
                  </label>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
