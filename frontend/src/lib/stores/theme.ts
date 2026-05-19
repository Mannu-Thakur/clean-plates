import { browser } from '$app/environment';

export type ThemePreference = 'dark' | 'light';

const THEME_KEY = 'cleanplates.theme';
const THEME_COLORS: Record<ThemePreference, string> = {
  dark: '#0b0e11',
  light: '#f5f7fa'
};

export function normalizeTheme(value: unknown): ThemePreference {
  return value === 'light' ? 'light' : 'dark';
}

export function readTheme(): ThemePreference {
  return readStoredTheme() ?? 'dark';
}

export function readStoredTheme(): ThemePreference | null {
  if (!browser) return null;
  const value = window.localStorage.getItem(THEME_KEY);
  return value === 'dark' || value === 'light' ? value : null;
}

export function applyTheme(value: unknown) {
  if (!browser) return;
  const theme = normalizeTheme(value);
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  document
    .querySelector<HTMLMetaElement>('meta[name="theme-color"]')
    ?.setAttribute('content', THEME_COLORS[theme]);
  window.localStorage.setItem(THEME_KEY, theme);
  window.dispatchEvent(
    new CustomEvent('cleanplates:theme-change', { detail: { theme } })
  );
}
