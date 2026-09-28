import { useCallback, useEffect, useState } from 'react';
import { api, ApiError, tokenStore } from './api/client';
import type { Collection } from './api/types';
import Sidebar from './components/Sidebar';
import TokenScreen from './components/TokenScreen';
import styles from './App.module.css';

export default function App() {
  const [authenticated, setAuthenticated] = useState(() => tokenStore.get() !== null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const signOut = useCallback(() => {
    tokenStore.clear();
    setAuthenticated(false);
    setCollections([]);
    setSelectedId(null);
  }, []);

  useEffect(() => {
    if (!authenticated) return;
    api
      .listCollections()
      .then((data) => {
        setCollections(data);
        setSelectedId((current) => current ?? data[0]?.id ?? null);
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) signOut();
        else setError('Could not load collections.');
      });
  }, [authenticated, signOut]);

  if (!authenticated) {
    return <TokenScreen onAuthenticated={() => setAuthenticated(true)} />;
  }

  const selected = collections.find((c) => c.id === selectedId);

  return (
    <div className={styles.layout}>
      <Sidebar
        collections={collections}
        selectedId={selectedId}
        onSelect={setSelectedId}
        onSignOut={signOut}
      />
      <main className={styles.main}>
        {error && <p role="alert">{error}</p>}
        {selected && (
          <header>
            <h1 className={styles.title}>{selected.name}</h1>
            <p className={styles.meta}>
              {selected.title_count} {selected.title_count === 1 ? 'film' : 'films'}
            </p>
          </header>
        )}
      </main>
    </div>
  );
}