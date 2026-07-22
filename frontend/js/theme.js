export const THEME_STORAGE_KEYS = Object.freeze({
  admin: "dict-attendance-admin-theme",
  public: "dict-attendance-public-theme",
});

const systemDarkMode = window.matchMedia("(prefers-color-scheme: dark)");

function readStoredTheme(storageKey) {
  try {
    const value = window.localStorage.getItem(storageKey);
    return value === "light" || value === "dark" ? value : null;
  } catch {
    return null;
  }
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
}

function resolvedTheme(preference) {
  return preference || (systemDarkMode.matches ? "dark" : "light");
}

export function initializeThemeToggle(button, storageKey) {
  let preference = readStoredTheme(storageKey);

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
      window.localStorage.setItem(storageKey, nextTheme);
    } catch {
      // Gumagana pa rin ang toggle kahit blocked ang browser storage.
    }
    setTheme(nextTheme);
  });

  systemDarkMode.addEventListener("change", (event) => {
    if (!preference) setTheme(event.matches ? "dark" : "light");
  });
}
