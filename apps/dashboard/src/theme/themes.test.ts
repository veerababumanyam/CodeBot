import { afterEach, describe, expect, it } from "vitest";
import { applyThemeToDocument, getThemeDefinition, resolveThemeMode } from "./themes";

const TOKEN_KEYS = [
  "--theme-color-background",
  "--theme-color-foreground",
  "--theme-color-panel",
  "--theme-color-accent",
  "--theme-gradient-app",
] as const;

describe("theme registry", () => {
  afterEach(() => {
    const root = document.documentElement;

    root.classList.remove("dark");
    delete root.dataset.theme;
    delete root.dataset.colorMode;
    root.style.colorScheme = "";

    for (const token of TOKEN_KEYS) {
      root.style.removeProperty(token);
    }
  });

  it("resolves system mode using the system preference", () => {
    expect(resolveThemeMode("system", true)).toBe("dark");
    expect(resolveThemeMode("system", false)).toBe("light");
    expect(resolveThemeMode("light", true)).toBe("light");
  });

  it("applies theme tokens and document attributes", () => {
    const root = document.documentElement;
    const expected = getThemeDefinition("midnight").modes.dark;

    const resolved = applyThemeToDocument({
      root,
      themeId: "midnight",
      themeMode: "dark",
      systemPrefersDark: false,
    });

    expect(resolved).toBe("dark");
    expect(root.dataset.theme).toBe("midnight");
    expect(root.dataset.colorMode).toBe("dark");
    expect(root.classList.contains("dark")).toBe(true);
    expect(root.style.getPropertyValue("--theme-color-background").trim()).toBe(
      expected["--theme-color-background"],
    );
    expect(root.style.getPropertyValue("--theme-gradient-app").trim()).toBe(
      expected["--theme-gradient-app"],
    );
  });
});