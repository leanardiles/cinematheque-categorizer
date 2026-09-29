import { useState } from 'react';
import type { Title } from '../api/types';
import { languageName } from '../lib/language';
import styles from './PosterCard.module.css';

interface Props {
  title: Title;
  collectionName: string;
  onRemove: () => void;
}

export default function PosterCard({ title, collectionName, onRemove }: Props) {
  const [imageFailed, setImageFailed] = useState(false);
  const details = [title.year, languageName(title.original_language)]
    .filter(Boolean)
    .join(' · ');

  return (
    <article className={styles.card}>
      <div className={styles.frame}>
        {title.poster && !imageFailed ? (
          <img
            className={styles.poster}
            src={title.poster}
            alt=""
            loading="lazy"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className={styles.placeholder}>
            <span>{title.name}</span>
          </div>
        )}
        <button
          type="button"
          className={styles.remove}
          onClick={onRemove}
          aria-label={`Remove ${title.name} from ${collectionName}`}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
        </button>
      </div>
      <div className={styles.name}>{title.name}</div>
      {details && <div className={styles.details}>{details}</div>}
    </article>
  );
}