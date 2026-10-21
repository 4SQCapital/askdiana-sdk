import type { InitData } from "../bridge";

/**
 * Applies the host's colour scheme from the bridge `init` payload.
 *
 * Sets `.dark` or `.light` on `<html>`. `.light` matters: `theme.css` follows
 * the OS (`prefers-color-scheme: dark`) unless `.light` is set, so without it
 * a view inside a light Ask DIANA turns dark on a computer set to dark mode.
 * Without a theme from the host, neither class is set and the OS decides.
 */
export function applyTheme(theme?: InitData["theme"]) {
  const scheme = theme?.colorScheme;
  const root = document.documentElement.classList;
  root.toggle("dark", scheme === "dark");
  root.toggle("light", scheme === "light");
}
