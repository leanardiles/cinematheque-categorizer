import type { Collection } from '../api/types';
import styles from './Sidebar.module.css';

interface Props {
  collections: Collection[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  onSignOut: () => void;
}

export default function Sidebar({ collections, selectedId, onSelect, onSignOut }: Props) {
  return (
    <nav className={styles.sidebar} aria-label="Main">
      <div className={styles.brand}>
        <div className={styles.logo}>Cinémathèque</div>
        <div className={styles.tagline}>Salle de projection</div>
      </div>

      <div className={styles.section}>
        <div className={styles.heading}>Collections</div>
        {collections.map((collection) => (
          <button
            key={collection.id}
            type="button"
            className={styles.item}
            aria-current={collection.id === selectedId ? 'page' : undefined}
            onClick={() => onSelect(collection.id)}
          >
            {collection.name}
            <span className={styles.count}>{collection.title_count}</span>
          </button>
        ))}
      </div>

      <div className={styles.footer}>
        <button type="button" className={styles.signOut} onClick={onSignOut}>
          Sign out
        </button>
        <p className={styles.attribution}>
          This product uses the TMDB API but is not endorsed or certified by TMDB.
        </p>
      </div>
    </nav>
  );
}