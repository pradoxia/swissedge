"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark";

const storageKey = "swissedge-public-theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const savedTheme = window.localStorage.getItem(storageKey);
    const initialTheme: Theme = savedTheme === "dark" ? "dark" : "light";
    setTheme(initialTheme);
    document.documentElement.dataset.theme = initialTheme;
  }, []);

  function updateTheme(nextTheme: Theme) {
    setTheme(nextTheme);
    window.localStorage.setItem(storageKey, nextTheme);
    document.documentElement.dataset.theme = nextTheme;
  }

  return (
    <div className="theme-toggle" aria-label="Theme preference">
      <span>Theme</span>
      <button
        aria-pressed={theme === "light"}
        onClick={() => updateTheme("light")}
        type="button"
      >
        Light
      </button>
      <button
        aria-pressed={theme === "dark"}
        onClick={() => updateTheme("dark")}
        type="button"
      >
        Dark
      </button>
    </div>
  );
}
