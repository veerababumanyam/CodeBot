export type ThemeMode = "light" | "dark" | "system";
export type ResolvedThemeMode = Exclude<ThemeMode, "system">;
export type ThemeId = "default" | "midnight";

type ThemeTokenMap = Record<string, string>;

interface ThemeDefinition {
  id: ThemeId;
  label: string;
  description: string;
  modes: Record<ResolvedThemeMode, ThemeTokenMap>;
}

function createThemeTokens(tokens: {
  background: string;
  foreground: string;
  mutedForeground: string;
  panel: string;
  panelStrong: string;
  panelMuted: string;
  border: string;
  borderStrong: string;
  accent: string;
  accentForeground: string;
  accentMuted: string;
  danger: string;
  dangerMuted: string;
  success: string;
  successMuted: string;
  warning: string;
  warningMuted: string;
  input: string;
  ring: string;
  gradient: string;
  panelShadow: string;
  floatingShadow: string;
}): ThemeTokenMap {
  return {
    "--theme-color-background": tokens.background,
    "--theme-color-foreground": tokens.foreground,
    "--theme-color-muted-foreground": tokens.mutedForeground,
    "--theme-color-panel": tokens.panel,
    "--theme-color-panel-strong": tokens.panelStrong,
    "--theme-color-panel-muted": tokens.panelMuted,
    "--theme-color-border": tokens.border,
    "--theme-color-border-strong": tokens.borderStrong,
    "--theme-color-accent": tokens.accent,
    "--theme-color-accent-foreground": tokens.accentForeground,
    "--theme-color-accent-muted": tokens.accentMuted,
    "--theme-color-danger": tokens.danger,
    "--theme-color-danger-muted": tokens.dangerMuted,
    "--theme-color-success": tokens.success,
    "--theme-color-success-muted": tokens.successMuted,
    "--theme-color-warning": tokens.warning,
    "--theme-color-warning-muted": tokens.warningMuted,
    "--theme-color-input": tokens.input,
    "--theme-color-ring": tokens.ring,
    "--theme-gradient-app": tokens.gradient,
    "--theme-shadow-panel": tokens.panelShadow,
    "--theme-shadow-floating": tokens.floatingShadow,
  };
}

export const THEMES: readonly ThemeDefinition[] = [
  {
    id: "default",
    label: "Aurora",
    description: "Balanced glass surfaces with a crisp editorial contrast.",
    modes: {
      light: createThemeTokens({
        background: "#f4f7fb",
        foreground: "#102033",
        mutedForeground: "#5b6b82",
        panel: "rgba(255, 255, 255, 0.78)",
        panelStrong: "rgba(255, 255, 255, 0.92)",
        panelMuted: "rgba(244, 248, 252, 0.72)",
        border: "rgba(138, 156, 184, 0.24)",
        borderStrong: "rgba(122, 140, 166, 0.42)",
        accent: "#2f6df6",
        accentForeground: "#f8fbff",
        accentMuted: "rgba(47, 109, 246, 0.14)",
        danger: "#d9485f",
        dangerMuted: "rgba(217, 72, 95, 0.14)",
        success: "#1fa971",
        successMuted: "rgba(31, 169, 113, 0.14)",
        warning: "#c98a19",
        warningMuted: "rgba(201, 138, 25, 0.16)",
        input: "rgba(255, 255, 255, 0.9)",
        ring: "rgba(47, 109, 246, 0.34)",
        gradient:
          "radial-gradient(circle at top left, rgba(47, 109, 246, 0.16), transparent 28%), radial-gradient(circle at top right, rgba(104, 82, 255, 0.1), transparent 24%), linear-gradient(180deg, #f9fbfd 0%, #eef3f9 100%)",
        panelShadow: "0 24px 48px -24px rgba(15, 23, 42, 0.26)",
        floatingShadow: "0 30px 60px -28px rgba(47, 109, 246, 0.28)",
      }),
      dark: createThemeTokens({
        background: "#08111f",
        foreground: "#f4f8ff",
        mutedForeground: "#8ea4c4",
        panel: "rgba(11, 23, 40, 0.72)",
        panelStrong: "rgba(15, 29, 49, 0.9)",
        panelMuted: "rgba(16, 30, 50, 0.62)",
        border: "rgba(148, 179, 255, 0.16)",
        borderStrong: "rgba(160, 188, 255, 0.3)",
        accent: "#70a2ff",
        accentForeground: "#06111f",
        accentMuted: "rgba(112, 162, 255, 0.18)",
        danger: "#ff6b81",
        dangerMuted: "rgba(255, 107, 129, 0.18)",
        success: "#34d399",
        successMuted: "rgba(52, 211, 153, 0.18)",
        warning: "#f6c65b",
        warningMuted: "rgba(246, 198, 91, 0.18)",
        input: "rgba(16, 29, 47, 0.88)",
        ring: "rgba(112, 162, 255, 0.34)",
        gradient:
          "radial-gradient(circle at top left, rgba(112, 162, 255, 0.22), transparent 30%), radial-gradient(circle at top right, rgba(79, 70, 229, 0.18), transparent 26%), linear-gradient(180deg, #08111f 0%, #050b15 100%)",
        panelShadow: "0 24px 64px -30px rgba(4, 10, 24, 0.8)",
        floatingShadow: "0 34px 80px -32px rgba(112, 162, 255, 0.26)",
      }),
    },
  },
  {
    id: "midnight",
    label: "Midnight",
    description: "A deeper nocturne palette with cobalt accents and richer glass.",
    modes: {
      light: createThemeTokens({
        background: "#eef1f8",
        foreground: "#172034",
        mutedForeground: "#66728a",
        panel: "rgba(255, 255, 255, 0.72)",
        panelStrong: "rgba(255, 255, 255, 0.92)",
        panelMuted: "rgba(237, 241, 248, 0.78)",
        border: "rgba(112, 129, 166, 0.26)",
        borderStrong: "rgba(102, 120, 156, 0.42)",
        accent: "#3659ff",
        accentForeground: "#f5f7ff",
        accentMuted: "rgba(54, 89, 255, 0.16)",
        danger: "#cf4f76",
        dangerMuted: "rgba(207, 79, 118, 0.14)",
        success: "#1d9f84",
        successMuted: "rgba(29, 159, 132, 0.14)",
        warning: "#b9851f",
        warningMuted: "rgba(185, 133, 31, 0.16)",
        input: "rgba(255, 255, 255, 0.92)",
        ring: "rgba(54, 89, 255, 0.34)",
        gradient:
          "radial-gradient(circle at top left, rgba(54, 89, 255, 0.16), transparent 28%), radial-gradient(circle at bottom right, rgba(80, 65, 207, 0.12), transparent 30%), linear-gradient(180deg, #f8faff 0%, #edf2f9 100%)",
        panelShadow: "0 24px 48px -24px rgba(17, 24, 39, 0.24)",
        floatingShadow: "0 36px 72px -30px rgba(54, 89, 255, 0.24)",
      }),
      dark: createThemeTokens({
        background: "#050816",
        foreground: "#f3f6ff",
        mutedForeground: "#9aa7ca",
        panel: "rgba(10, 15, 32, 0.74)",
        panelStrong: "rgba(13, 20, 40, 0.9)",
        panelMuted: "rgba(14, 21, 39, 0.64)",
        border: "rgba(120, 145, 255, 0.18)",
        borderStrong: "rgba(132, 156, 255, 0.3)",
        accent: "#8ba4ff",
        accentForeground: "#040916",
        accentMuted: "rgba(139, 164, 255, 0.18)",
        danger: "#ff7f9a",
        dangerMuted: "rgba(255, 127, 154, 0.18)",
        success: "#44d7b6",
        successMuted: "rgba(68, 215, 182, 0.18)",
        warning: "#ffca6c",
        warningMuted: "rgba(255, 202, 108, 0.18)",
        input: "rgba(16, 22, 41, 0.88)",
        ring: "rgba(139, 164, 255, 0.34)",
        gradient:
          "radial-gradient(circle at top left, rgba(139, 164, 255, 0.22), transparent 30%), radial-gradient(circle at bottom right, rgba(68, 215, 182, 0.14), transparent 24%), linear-gradient(180deg, #050816 0%, #02040b 100%)",
        panelShadow: "0 24px 64px -28px rgba(0, 0, 0, 0.84)",
        floatingShadow: "0 34px 80px -32px rgba(80, 96, 255, 0.28)",
      }),
    },
  },
] as const;

export function getThemeDefinition(themeId: ThemeId): ThemeDefinition {
  const fallbackTheme = THEMES[0];

  if (!fallbackTheme) {
    throw new Error("At least one theme must be registered.");
  }

  return THEMES.find((theme) => theme.id === themeId) ?? fallbackTheme;
}

export function resolveThemeMode(
  themeMode: ThemeMode,
  systemPrefersDark: boolean,
): ResolvedThemeMode {
  if (themeMode === "system") {
    return systemPrefersDark ? "dark" : "light";
  }

  return themeMode;
}

export function applyThemeToDocument(options: {
  root: HTMLElement;
  themeId: ThemeId;
  themeMode: ThemeMode;
  systemPrefersDark: boolean;
}): ResolvedThemeMode {
  const resolvedMode = resolveThemeMode(options.themeMode, options.systemPrefersDark);
  const theme = getThemeDefinition(options.themeId);
  const tokens = theme.modes[resolvedMode];

  options.root.dataset.theme = theme.id;
  options.root.dataset.colorMode = resolvedMode;
  options.root.style.colorScheme = resolvedMode;
  options.root.classList.toggle("dark", resolvedMode === "dark");

  for (const [token, value] of Object.entries(tokens)) {
    options.root.style.setProperty(token, value);
  }

  return resolvedMode;
}