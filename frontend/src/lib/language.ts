const names = new Intl.DisplayNames(['en'], { type: 'language' });

/** 'fr' -> 'French', 'es' -> 'Spanish'; returns null for missing or unknown codes. */
export function languageName(code: string | null): string | null {
  if (!code) return null;
  try {
    return names.of(code) ?? null;
  } catch {
    return null;
  }
}