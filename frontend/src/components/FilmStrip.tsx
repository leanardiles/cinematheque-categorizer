import type { ReactNode } from 'react';
import styles from './FilmStrip.module.css';

const SPROCKETS = Array.from({ length: 28 }, (_, i) => i);

function Sprockets() {
  return (
    <div className={styles.sprockets} aria-hidden="true">
      {SPROCKETS.map((i) => (
        <span key={i} />
      ))}
    </div>
  );
}

/** Wraps a list of posters (each in an <li>) in the film strip frame. */
export default function FilmStrip({ children }: { children: ReactNode }) {
  return (
    <div className={styles.strip}>
      <Sprockets />
      <ul className={styles.grid}>{children}</ul>
      <Sprockets />
    </div>
  );
}