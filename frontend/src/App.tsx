import { useCallback, useEffect, useState } from 'react';
import { api, ApiError, openedFromInvite, tokenStore } from './api/client';
import type { Collection, Me } from './api/types';
import AccountDialog from './components/AccountDialog';
import AddonDialog from './components/AddonDialog';
import CollectionView from './components/CollectionView';
import ConfirmDialog from './components/ConfirmDialog';
import ConnectStremio from './components/ConnectStremio';
import CreateLogin from './components/CreateLogin';
import LibraryView from './components/LibraryView';
import SearchBar from './components/SearchBar';
import Sidebar, { type View } from './components/Sidebar';
import TokenScreen from './components/TokenScreen';
import styles from './App.module.css';

export default function App() {
  const [authenticated, setAuthenticated] = useState(() => tokenStore.get() !== null);
  // Who is signed in; null while loading
  const [me, setMe] = useState<Me | null>(null);
  const [addonOpen, setAddonOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  // Explains why the sign-in screen is showing, e.g. after a used invite link
  const [notice, setNotice] = useState<string | null>(null);
  const [confirmDisconnect, setConfirmDisconnect] = useState(false);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [libraryCount, setLibraryCount] = useState<number | null>(null);
  const [view, setView] = useState<View>({ kind: 'all' });
  const [error, setError] = useState<string | null>(null);
  // Opened from Stremio as /?q=<film name>: start with that search
  const [query, setQuery] = useState(() => new URLSearchParams(window.location.search).get('q') ?? '');

  const signOut = useCallback(() => {
    // Ends this device's login session; invite links and tokens just stay valid
    const token = tokenStore.get();
    if (token) api.logout(token).catch(() => {});
    tokenStore.clear();
    setAuthenticated(false);
    setMe(null);
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

  const reloadMe = useCallback(() => {
    api
      .me()
      .then(setMe)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) {
          signOut();
          if (openedFromInvite()) {
            setNotice(
              'This invite link has already been used. Sign in with your email and password, ' +
                'or ask for a new link.',
            );
          }
        } else setError('Could not reach the server.');
      });
  }, [signOut]);

  useEffect(() => {
    if (authenticated) reloadMe();
  }, [authenticated, reloadMe]);

  const connected = me?.stremio_connected === true;
  useEffect(() => {
    if (connected) loadSidebar();
  }, [connected, loadSidebar]);

  async function disconnectStremio() {
    setConfirmDisconnect(false);
    try {
      await api.disconnectStremio();
      setMe((current) => (current ? { ...current, stremio_connected: false } : current));
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) signOut();
      else setError('Could not disconnect Stremio.');
    }
  }

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
    return (
      <TokenScreen
        notice={notice}
        onAuthenticated={() => {
          setNotice(null);
          setAuthenticated(true);
        }}
      />
    );
  }

  if (me === null) {
    return error ? <p role="alert">{error}</p> : null;
  }

  if (me.via_invite) {
    return (
      <CreateLogin
        name={me.name}
        email={me.email}
        reset={me.has_password}
        onSaved={reloadMe}
        onUnauthorized={signOut}
      />
    );
  }

  if (!me.stremio_connected) {
    return (
      <ConnectStremio
        name={me.name}
        onDone={() => setMe({ ...me, stremio_connected: true })}
        onUnauthorized={signOut}
        onSignOut={signOut}
      />
    );
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
        hasLogin={me.has_password}
        onOpenAccount={() => setAccountOpen(true)}
        onInstallAddon={() => setAddonOpen(true)}
        onDisconnectStremio={() => setConfirmDisconnect(true)}
        onSignOut={signOut}
      />
      <AccountDialog
        open={accountOpen}
        me={me}
        onClose={() => setAccountOpen(false)}
        onSaved={() => {
          setAccountOpen(false);
          reloadMe();
        }}
        onUnauthorized={signOut}
      />
      <AddonDialog
        open={addonOpen}
        onClose={() => setAddonOpen(false)}
        onUnauthorized={signOut}
      />
      <ConfirmDialog
        open={confirmDisconnect}
        title="Disconnect Stremio?"
        message="Your collections stay, but your library stops syncing until you connect Stremio again."
        confirmLabel="Disconnect"
        onConfirm={disconnectStremio}
        onCancel={() => setConfirmDisconnect(false)}
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