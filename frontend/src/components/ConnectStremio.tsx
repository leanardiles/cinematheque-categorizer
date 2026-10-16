import { useState, type FormEvent } from 'react';
import { api, ApiError } from '../api/client';
import type { SyncReport } from '../api/types';
import AddonInstall from './AddonInstall';
import styles from './Account.module.css';

interface Props {
  name: string;
  onDone: () => void;
  onUnauthorized: () => void;
  onSignOut: () => void;
}

type Method = 'password' | 'key';

/** Shown until the user's Stremio account is connected, then offers the addon. */
export default function ConnectStremio({ name, onDone, onUnauthorized, onSignOut }: Props) {
  const [method, setMethod] = useState<Method>('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authKey, setAuthKey] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [imported, setImported] = useState<SyncReport | null | undefined>(undefined);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api.connectStremio(
        method === 'password' ? { email: email.trim(), password } : { auth_key: authKey.trim() },
      );
      setPassword('');
      setImported(result.sync);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      else if (err instanceof ApiError && err.status === 400) setError(err.message);
      else setError('Could not reach Stremio. Try again in a moment.');
    } finally {
      setBusy(false);
    }
  }

  // Step 2: connected, now install the addon
  if (imported !== undefined) {
    const count = imported ? imported.added + imported.linked : 0;
    return (
      <main className={styles.screen}>
        <div className={styles.card}>
          <h1 className={styles.title}>Connected</h1>
          <p className={styles.note}>
            {imported === null
              ? 'Your Stremio library will appear within the next half hour.'
              : count === 0 && imported.remaining === 0
                ? 'Your Stremio library is connected and up to date.'
                : `${count} ${count === 1 ? 'film' : 'films'} imported from your Stremio library.` +
                  (imported.remaining > 0
                    ? ` The other ${imported.remaining} arrive within the next half hour.`
                    : '')}
          </p>
          <h2 className={styles.heading}>Add your collections to Stremio</h2>
          <p className={styles.note}>
            Your collections become rows on Stremio's home screen, and you can file films from a
            film's page.
          </p>
          <AddonInstall onUnauthorized={onUnauthorized} />
          <button type="button" className={styles.continue} onClick={onDone}>
            Continue to my library
          </button>
        </div>
      </main>
    );
  }

  // Step 1: connect Stremio
  return (
    <main className={styles.screen}>
      <form className={styles.card} onSubmit={handleSubmit}>
        <h1 className={styles.title}>Welcome, {name}</h1>
        <p className={styles.note}>
          Connect your Stremio account so Cinémathèque can read the films saved in your library and
          keep them in sync.
        </p>

        {method === 'password' ? (
          <>
            <label className={styles.label} htmlFor="stremio-email">
              Stremio email
            </label>
            <input
              id="stremio-email"
              className={styles.input}
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <label className={styles.label} htmlFor="stremio-password">
              Stremio password
            </label>
            <input
              id="stremio-password"
              className={styles.input}
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <p className={styles.hint}>
              Your password goes to Stremio once and is never stored here. Only Stremio's access
              key is kept, encrypted.
            </p>
          </>
        ) : (
          <>
            <ol className={styles.steps}>
              <li>
                Open{' '}
                <a href="https://web.strem.io" target="_blank" rel="noreferrer">
                  web.strem.io
                </a>{' '}
                on a computer and sign in.
              </li>
              <li>
                Open the browser console: <kbd>F12</kbd>, then the Console tab.
              </li>
              <li>
                Paste this line, press Enter, and copy the result:
                <code className={styles.code}>
                  JSON.parse(localStorage.getItem('profile')).auth.key
                </code>
              </li>
            </ol>
            <label className={styles.label} htmlFor="stremio-key">
              Access key
            </label>
            <input
              id="stremio-key"
              className={styles.input}
              autoComplete="off"
              spellCheck={false}
              value={authKey}
              onChange={(e) => setAuthKey(e.target.value)}
              required
            />
            <p className={styles.hint}>The key is stored encrypted and used only to read your library.</p>
          </>
        )}

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <button className={styles.primary} type="submit" disabled={busy}>
          {busy ? 'Connecting and importing…' : 'Connect Stremio'}
        </button>

        <button
          type="button"
          className={styles.link}
          onClick={() => {
            setMethod(method === 'password' ? 'key' : 'password');
            setError(null);
          }}
        >
          {method === 'password'
            ? 'Sign in to Stremio with Google, Facebook or Apple? Use an access key instead'
            : 'Use my Stremio email and password instead'}
        </button>
        <button type="button" className={styles.link} onClick={onSignOut}>
          Sign out
        </button>
      </form>
    </main>
  );
}
