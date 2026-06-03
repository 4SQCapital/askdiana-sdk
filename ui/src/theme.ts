export interface ThemeTokens {
  bg?: string;
  fg?: string;
  primary?: string;
  primaryFg?: string;
  border?: string;
  muted?: string;
  radius?: string;
}

export const defaultTheme: Required<ThemeTokens> = {
  bg: "#ffffff",
  fg: "#1a1a2e",
  primary: "#6366f1",
  primaryFg: "#ffffff",
  border: "#e2e8f0",
  muted: "#f1f5f9",
  radius: "8px",
};

export function applyTheme(tokens: ThemeTokens = {}) {
  const t = { ...defaultTheme, ...tokens };
  const r = document.documentElement.style;
  r.setProperty("--ext-bg", t.bg);
  r.setProperty("--ext-fg", t.fg);
  r.setProperty("--ext-primary", t.primary);
  r.setProperty("--ext-primary-fg", t.primaryFg);
  r.setProperty("--ext-border", t.border);
  r.setProperty("--ext-muted", t.muted);
  r.setProperty("--ext-radius", t.radius);
}
