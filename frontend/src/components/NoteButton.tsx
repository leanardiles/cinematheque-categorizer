import { useEffect, useRef, useState } from 'react';
import { NOTE_MAX } from '../api/types';
import styles from './NoteButton.module.css';

interface Props {
  titleName: string;
  note: string | null;
  /** Saves the note (null clears it); resolves to an error message, or null */
  onSave: (note: string | null) => Promise<string | null>;
}

/**
 * The note icon on a poster. Gold and always visible when the film has a
 * note (hovering shows it); otherwise faint, on hover. Clicking opens a small
 * editor above the icon.
 */
export default function NoteButton({ titleName, note, onSave }: Props) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  // Close when clicking anywhere outside the editor
  useEffect(() => {
    if (!open) return;
    function handlePointerDown(event: PointerEvent) {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener('pointerdown', handlePointerDown);
    return () => document.removeEventListener('pointerdown', handlePointerDown);
  }, [open]);

  function openEditor() {
    setDraft(note ?? '');
    setError(null);
    setOpen(true);
  }

  async function save(value: string | null) {
    setSaving(true);
    const message = await onSave(value && value.trim() ? value.trim() : null);
    setSaving(false);
    if (message) setError(message);
    else setOpen(false);
  }

  return (
    <div ref={rootRef} className={styles.root}>
      <button
        type="button"
        className={styles.button}
        data-has-note={note ? '' : undefined}
        aria-expanded={open}
        aria-label={note ? `Note on ${titleName}: ${note}. Edit the note` : `Add a note to ${titleName}`}
        title={note ?? 'Add a note'}
        onClick={() => (open ? setOpen(false) : openEditor())}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M5 4h14a1 1 0 0 1 1 1v10l-5 5H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1z" />
          <path d="M15 20v-4a1 1 0 0 1 1-1h4" />
          <path d="M8 9h8M8 13h5" />
        </svg>
      </button>

      {open && (
        <form
          className={styles.editor}
          role="dialog"
          aria-label={`Note on ${titleName}`}
          onSubmit={(e) => {
            e.preventDefault();
            save(draft);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Escape') {
              e.stopPropagation();
              setOpen(false);
            }
          }}
        >
          <textarea
            className={styles.textarea}
            value={draft}
            maxLength={NOTE_MAX}
            rows={3}
            placeholder="Who recommended it, why it matters…"
            aria-label="Note"
            autoFocus
            onChange={(e) => setDraft(e.target.value.replace(/\n/g, ' '))}
            onKeyDown={(e) => {
              // Enter saves; notes are a single line (Shift+Enter is ignored too)
              if (e.key === 'Enter') {
                e.preventDefault();
                if (!e.shiftKey) save(draft);
              }
            }}
          />
          <div className={styles.footer}>
            <span className={styles.count} aria-live="polite">
              {draft.length}/{NOTE_MAX}
            </span>
            {note && (
              <button
                type="button"
                className={styles.clear}
                onClick={() => save(null)}
                disabled={saving}
              >
                Delete
              </button>
            )}
            <button type="submit" className={styles.save} disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
          {error && (
            <p className={styles.error} role="alert">
              {error}
            </p>
          )}
        </form>
      )}
    </div>
  );
}
