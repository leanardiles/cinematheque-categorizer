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
    // Accept a whole invite link as well as a bare token
    const value = token.trim();
    const cleaned = value.includes('#invite=') ? value.split('#invite=')[1] : value;
    try {
      await api.me(cleaned);
      tokenStore.set(cleaned);
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
        <p className={styles.note}>
          Private management app for a personal Stremio addon.{' '}
          <a href="https://github.com/leanardiles/cinematheque-categorizer">
            View the source on GitHub
          </a>
          . Invited? Open the link you were sent, or paste it here.
        </p>

        <label className={styles.label} htmlFor="api-token">
          Access token
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