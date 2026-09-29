import type { SortKey, SortOption } from '../lib/sort';
import styles from './SortSelect.module.css';

interface Props {
  value: SortKey;
  options: SortOption[];
  onChange: (value: SortKey) => void;
}

export default function SortSelect({ value, options, onChange }: Props) {
  return (
    <label className={styles.sort}>
      <span className={styles.label}>Sort by</span>
      <select
        className={styles.select}
        value={value}
        onChange={(e) => onChange(e.target.value as SortKey)}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
