import type { InitData } from "../bridge";

/**
 * Toggles the `.dark` class on `<html>` based on the host's bridge `init`
 * payload, so `theme.css`'s `.dark` token overrides take effect.
 */
export function applyTheme(theme?: InitData["theme"]) {
  document.documentElement.classList.toggle("dark", theme?.colorScheme === "dark");
}
