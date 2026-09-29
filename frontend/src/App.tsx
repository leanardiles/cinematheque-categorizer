import { useCallback, useEffect, useState } from 'react';
import { api, ApiError, tokenStore } from './api/client';
import type { Collection } from './api/types';
import CollectionView from './components/CollectionView';
import LibraryView from './components/LibraryView';
import SearchBar from './components/SearchBar';
import Sidebar, { type View } from './components/Sidebar';
import TokenScreen from './components/TokenScreen';
import styles from './App.module.css';

export default function App() {
  const [authenticated, setAuthenticated] = useState(() => tokenStore.get() !== null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [libraryCount, setLibraryCount] = useState<number | null>(null);
  const [view, setView] = useState<View>({ kind: 'all' });
  const [error, setError] = useState<string | null>(null);
  // Opened from Stremio as /?q=<film name>: start with that search
  const [query, setQuery] = useState(() => new URLSearchParams(window.location.search).get('q') ?? '');

  const signOut = useCallback(() => {
    tokenStore.clear();
    setAuthenticated(false);
    setCollections([]);
    setLibraryCount(null);
    setView({ kind: 'all' });
    setQuery('');
  }, []);

  /** Reloads the collections and library count shown in the sidebar. */
  const loadSidebar = useCallback(() => {
    Promise.all([api.listCollections(), api.listTitles()])
      .then(([collectionData, titleData]) => {
        setCollections(collectionData);
        setLibraryCount(titleData.length);
        // If the open collection no longer exists, fall back to All
        setView((current) =>
          current.kind === 'collection' && !collectionData.some((c) => c.id === current.id)
            ? { kind: 'all' }
            : current,
        );
      })
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) signOut();
        else setError('Could not load your collections.');
      });
  }, [signOut]);

  useEffect(() => {
    if (authenticated) loadSidebar();
  }, [authenticated, loadSidebar]);

  async function createCollection(name: string): Promise<string | null> {
    try {
      const collection = await api.createCollection(name);
      loadSidebar();
      setView({ kind: 'collection', id: collection.id });
      return null;
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        signOut();
        return null;
      }
      if (err instanceof ApiError && err.status === 409) {
        return 'A collection with this name already exists.';
      }
      return 'Could not create the collection.';
    }
  }

  async function reorderCollections(ids: number[]) {
    const previous = collections;
    // Show the new order right away, and undo it if saving fails
    setCollections(ids.map((id) => collections.find((c) => c.id === id)!));
    try {
      setCollections(await api.reorderCollections(ids));
    } catch (err) {
      setCollections(previous);
      if (err instanceof ApiError && err.status === 401) signOut();
      else setError('Could not save the new order.');
    }
  }

  if (!authenticated) {
    return <TokenScreen onAuthenticated={() => setAuthenticated(true)} />;
  }

  const selected =
    view.kind === 'collection' ? collections.find((c) => c.id === view.id) : undefined;
  const searching = query.trim() !== '';

  /** Choosing a page in the sidebar ends the search. */
  function selectView(next: View) {
    setQuery('');
    setView(next);
  }

  return (
    <div className={styles.layout}>
      <Sidebar
        collections={collections}
        libraryCount={libraryCount}
        view={view}
        onSelect={selectView}
        onCreateCollection={createCollection}
        onReorderCollections={reorderCollections}
        onSignOut={signOut}
      />
      <main className={styles.main}>
        <div className={styles.topBar}>
          <SearchBar value={query} onChange={setQuery} />
        </div>
        {error && <p role="alert">{error}</p>}
        {searching && (
          <LibraryView
            key="search"
            collections={collections}
            query={query}
            onChanged={loadSidebar}
            onUnauthorized={signOut}
          />
        )}
        {!searching && view.kind === 'all' && (
          <LibraryView
            collections={collections}
            onChanged={loadSidebar}
            onUnauthorized={signOut}
          />
        )}
        {!searching && selected && (
          <CollectionView
            key={selected.id}
            collection={selected}
            collections={collections}
            onChanged={loadSidebar}
            onDeleted={() => {
              setView({ kind: 'all' });
              loadSidebar();
            }}
            onUnauthorized={signOut}
          />
        )}
      </main>
    </div>
  );
}