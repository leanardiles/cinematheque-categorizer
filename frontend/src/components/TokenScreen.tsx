import { useState, type FormEvent } from 'react';
import { api, ApiError, tokenStore } from '../api/client';
import styles from './TokenScreen.module.css';

interface Props {
  onAuthenticated: () => void;
  /** Shown above the form, for example when an invite link was already used */
  notice?: string | null;
}

type Method = 'password' | 'token';

export default function TokenScreen({ onAuthenticated, notice }: Props) {
  const [method, setMethod] = useState<Method>('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  async function signInWithPassword() {
    try {
      const result = await api.login(email.trim(), password);
      tokenStore.set(result.token);
      onAuthenticated();
    } catch (err) {
      setError(
        err instanceof ApiError && (err.status === 401 || err.status === 429)
          ? err.message
          : 'Could not reach the server. Try again in a moment.',
      );
    }
  }

  async function signInWithToken() {
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
          ? 'That link or token was not accepted.'
          : 'Could not reach the server. Try again in a moment.',
      );
    }
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setChecking(true);
    setError(null);
    await (method === 'password' ? signInWithPassword() : signInWithToken());
    setChecking(false);
  }

  return (
    <main className={styles.screen}>
      <form className={styles.card} onSubmit={handleSubmit}>
        <h1 className={styles.title}>Cinémathèque</h1>
        <p className={styles.subtitle}>Salle de projection</p>
        <p className={styles.note}>
          Organize your Stremio library into collections. By invitation.{' '}
          <a href="https://github.com/leanardiles/cinematheque-categorizer">
            View the source on GitHub
          </a>
          .
        </p>
        {notice && <p className={styles.notice}>{notice}</p>}

        {method === 'password' ? (
          <>
            <label className={styles.label} htmlFor="sign-in-email">
              Email
            </label>
            <input
              id="sign-in-email"
              className={styles.input}
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <label className={styles.label} htmlFor="sign-in-password">
              Password
            </label>
            <input
              id="sign-in-password"
              className={styles.input}
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </>
        ) : (
          <>
            <label className={styles.label} htmlFor="api-token">
              Invite link or access token
            </label>
            <input
              id="api-token"
              className={styles.input}
              type="password"
              autoComplete="off"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              required
            />
          </>
        )}
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <button className={styles.button} type="submit" disabled={checking}>
          {checking ? 'Checking…' : 'Sign in'}
        </button>
        <button
          type="button"
          className={styles.switch}
          onClick={() => {
            setMethod(method === 'password' ? 'token' : 'password');
            setError(null);
          }}
        >
          {method === 'password'
            ? 'Use an invite link or access token instead'
            : 'Sign in with email and password instead'}
        </button>
        {method === 'password' && (
          <p className={styles.hint}>Forgot your password? Ask for a new invite link.</p>
        )}
      </form>
    </main>
  );
}
