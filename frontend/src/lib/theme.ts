export type Theme = "light" | "dark";

const KEY = "theme";

function systemPrefersDark(): boolean {
  // jsdom and very old browsers have no matchMedia.
  return typeof window.matchMedia === "function" && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

// Storage can be missing or throw (private windows, blocked site data), so every access is guarded.
export function readStoredTheme(): Theme | null {
  try {
    const value = localStorage.getItem(KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

function storeTheme(theme: Theme | null) {
  try {
    if (theme) localStorage.setItem(KEY, theme);
    else localStorage.removeItem(KEY);
  } catch {
    // Not remembered; the switch still works for this visit.
  }
}

export function currentTheme(): Theme {
  return readStoredTheme() ?? (systemPrefersDark() ? "dark" : "light");
}

// styles.css redefines its colors under :root[data-theme="dark"|"light"].
export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme;
}

// What to remember after the user picks `next`; null forgets the choice, so the page follows the system again.
function rememberChoice(next: Theme, systemTheme: Theme): Theme | null {
  return next === systemTheme ? null : next;
}

export function chooseTheme(next: Theme) {
  applyTheme(next);
  storeTheme(rememberChoice(next, systemPrefersDark() ? "dark" : "light"));
}
