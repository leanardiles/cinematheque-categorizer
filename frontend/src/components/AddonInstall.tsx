import { useState } from 'react';
import { api, ApiError } from '../api/client';
import type { AddonLink } from '../api/types';
import styles from './Account.module.css';

interface Props {
  onUnauthorized: () => void;
}

/**
 * Creates the user's personal addon address on request and offers ways to
 * install it. Addresses are stored hashed, so each click makes a fresh one;
 * addresses installed earlier keep working.
 */
export default function AddonInstall({ onUnauthorized }: Props) {
  const [link, setLink] = useState<AddonLink | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function createLink() {
    setLoading(true);
    setError(null);
    try {
      setLink(await api.addonLink());
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) onUnauthorized();
      else setError('Could not create your addon address. Try again.');
    } finally {
      setLoading(false);
    }
  }

  async function copy() {
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link.manifest_url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard blocked: the address is selectable in the field
    }
  }

  if (!link) {
    return (
      <div className={styles.stack}>
        <button type="button" className={styles.primary} onClick={createLink} disabled={loading}>
          {loading ? 'Creating…' : 'Get my addon'}
        </button>
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }

  return (
    <div className={styles.stack}>
      <div className={styles.actions}>
        <a className={styles.primary} href={link.app_install_url}>
          Install in the Stremio app
        </a>
        <a
          className={styles.secondary}
          href={link.web_install_url}
          target="_blank"
          rel="noreferrer"
        >
          Install in Stremio Web
        </a>
      </div>
      <label className={styles.label} htmlFor="addon-address">
        Or paste this address into Stremio's addon search
      </label>
      <div className={styles.row}>
        <input
          id="addon-address"
          className={styles.input}
          value={link.manifest_url}
          readOnly
          onFocus={(e) => e.currentTarget.select()}
        />
        <button type="button" className={styles.secondary} onClick={copy}>
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <p className={styles.hint}>
        Keep this address private: it opens your collections. On a TV, the addon appears by
        itself once the TV is signed in to the same Stremio account.
      </p>
    </div>
  );
}
