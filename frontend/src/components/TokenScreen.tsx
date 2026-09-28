import { useState, type FormEvent } from 'react';
import { api, ApiError, tokenStore } from '../api/client';
import styles from './TokenScreen.module.css';

interface Props {
  onAuthenticated: () => void;
}

export default function TokenScreen({ onAuthenticated }: Props) {
  const [token, setToken] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setChecking(true);
    setError(null);
    try {
      await api.me(token.trim());
      tokenStore.set(token.trim());
      onAuthenticated();
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 401
          ? 'That token was not accepted.'
          : 'Could not reach the server. Is the backend running?',
      );
    } finally {
      setChecking(false);
    }
  }

  return (
    <main className={styles.screen}>
      <form className={styles.card} onSubmit={handleSubmit}>
        <h1 className={styles.title}>Cinémathèque</h1>
        <p className={styles.subtitle}>Salle de projection</p>

        <label className={styles.label} htmlFor="api-token">
          API token
        </label>
        <input
          id="api-token"
          className={styles.input}
          type="password"
          autoComplete="current-password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          required
        />
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <button className={styles.button} type="submit" disabled={checking || !token.trim()}>
          {checking ? 'Checking…' : 'Enter'}
        </button>
      </form>
    </main>
  );
}