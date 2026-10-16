import { useEffect, useRef } from 'react';
import AddonInstall from './AddonInstall';
import styles from './Account.module.css';

interface Props {
  open: boolean;
  onClose: () => void;
  onUnauthorized: () => void;
}

export default function AddonDialog({ open, onClose, onUnauthorized }: Props) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      className={styles.dialog}
      aria-labelledby="addon-title"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <h2 id="addon-title" className={styles.heading}>
        Install in Stremio
      </h2>
      <p className={styles.note}>
        Each time you get the addon, a new private address is created. Addresses you installed
        before keep working.
      </p>
      {/* Remounted on each open, so a closed dialog doesn't keep an old address */}
      {open && <AddonInstall onUnauthorized={onUnauthorized} />}
      <button type="button" className={styles.continue} onClick={onClose}>
        Close
      </button>
    </dialog>
  );
}
