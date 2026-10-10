export type Theme = 'light' | 'dark';

const THEME_KEY = 'pref-theme';

export function getTheme(): Theme {
  try {
    return localStorage.getItem(THEME_KEY) === 'dark' ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

export function applyTheme(theme: Theme): void {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  document.documentElement.style.colorScheme = theme;

  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    // Keep the selected theme active for this page even when storage is unavailable.
  }
}
