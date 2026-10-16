import { useState, type FormEvent } from 'react';
import { api, ApiError, tokenStore } from '../api/client';
import styles from './Account.module.css';

interface Props {
  initialEmail: string | null;
  /** Changing an existing password from a normal session asks for the current one */
  askCurrent: boolean;
  submitLabel: string;
  /** Called after saving; the browser is now signed in with a fresh login token */
  onSaved: () => void;
  onUnauthorized: () => void;
}

/** Creates or changes the email and password login. */
export default function LoginForm({
  initialEmail,
  askCurrent,
  submitLabel,
  onSaved,
  onUnauthorized,
}: Props) {
  const [email, setEmail] = useState(initialEmail ?? '');
  const [password, setPassword] = useState('');
  const [current, setCurrent] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.setLogin({
        email: email.trim(),
        password,
        ...(askCurrent ? { current_password: current } : {}),
      });
      // Invite links stop working now; this browser switches to the new login
      tokenStore.set(result.token);
      onSaved();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      else if (err instanceof ApiError && [400, 409, 429].includes(err.status)) setError(err.message);
      else setError('Could not save your login. Try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className={styles.stack} onSubmit={handleSubmit}>
      <label className={styles.label} htmlFor="login-email">
        Email
      </label>
      <input
        id="login-email"
        className={styles.input}
        type="email"
        autoComplete="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      {askCurrent && (
        <>
          <label className={styles.label} htmlFor="login-current">
            Current password
          </label>
          <input
            id="login-current"
            className={styles.input}
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            required
          />
        </>
      )}
      <label className={styles.label} htmlFor="login-password">
        {askCurrent ? 'New password' : 'Password'}
      </label>
      <input
        id="login-password"
        className={styles.input}
        type="password"
        autoComplete="new-password"
        minLength={8}
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <p className={styles.hint}>At least 8 characters.</p>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      <button className={styles.primary} type="submit" disabled={busy}>
        {busy ? 'Saving…' : submitLabel}
      </button>
    </form>
  );
}
