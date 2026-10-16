import { useEffect, useRef } from 'react';
import type { Me } from '../api/types';
import LoginForm from './LoginForm';
import styles from './Account.module.css';

interface Props {
  open: boolean;
  me: Me;
  onClose: () => void;
  onSaved: () => void;
  onUnauthorized: () => void;
}

/** Set up or change the email and password login. */
export default function AccountDialog({ open, me, onClose, onSaved, onUnauthorized }: Props) {
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
      aria-labelledby="account-title"
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
    >
      <h2 id="account-title" className={styles.heading}>
        {me.has_password ? 'Change your login' : 'Set up email login'}
      </h2>
      <p className={styles.note}>
        {me.has_password
          ? `You sign in as ${me.email}.`
          : 'Sign in on any device with an email and password, instead of a token.'}
      </p>
      {/* Remounted on each open, so the fields start empty */}
      {open && (
        <LoginForm
          initialEmail={me.email}
          askCurrent={me.has_password}
          submitLabel="Save"
          onSaved={onSaved}
          onUnauthorized={onUnauthorized}
        />
      )}
      <button type="button" className={styles.continue} onClick={onClose}>
        Close
      </button>
    </dialog>
  );
}
