const THEME_STORAGE_KEY = "dict-attendance-theme";
const systemDarkMode = window.matchMedia("(prefers-color-scheme: dark)");

function readStoredTheme() {
  try {
    const value = window.localStorage.getItem(THEME_STORAGE_KEY);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
}

function resolvedTheme(preference = readStoredTheme()) {
  return preference || (systemDarkMode.matches ? "dark" : "light");
}

export function initializeThemeToggle(button) {
  let preference = readStoredTheme();

  function updateButton(theme) {
    const dark = theme === "dark";
    button.setAttribute("aria-pressed", String(dark));
    button.setAttribute("aria-label", dark ? "Use light theme" : "Use dark theme");
    button.title = dark ? "Use light theme" : "Use dark theme";
    const icon = button.querySelector(".material-symbols-outlined");
    if (icon) icon.textContent = dark ? "light_mode" : "dark_mode";
  }

  function setTheme(theme) {
    applyTheme(theme);
    updateButton(theme);
  }

  setTheme(resolvedTheme(preference));

  button.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    preference = nextTheme;
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
    } catch {
      // Gumagana pa rin ang toggle kahit blocked ang browser storage.
    }
    setTheme(nextTheme);
  });

  systemDarkMode.addEventListener("change", (event) => {
    if (!preference) setTheme(event.matches ? "dark" : "light");
  });
}

applyTheme(resolvedTheme());
