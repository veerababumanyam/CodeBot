import { useEffect } from "react";
import { useUiStore } from "@/stores/ui-store";
import { applyThemeToDocument } from "@/theme/themes";

function createMediaQueryList(): MediaQueryList | null {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return null;
  }

  return window.matchMedia("(prefers-color-scheme: dark)");
}

export function useThemeSync(): void {
  const theme = useUiStore((state) => state.theme);
  const themeId = useUiStore((state) => state.themeId);

  useEffect(() => {
    if (typeof document === "undefined") {
      return;
    }

    const root = document.documentElement;
    const mediaQuery = createMediaQueryList();

    const applyTheme = () => {
      applyThemeToDocument({
        root,
        themeId,
        themeMode: theme,
        systemPrefersDark: mediaQuery?.matches ?? false,
      });
    };

    applyTheme();

    if (theme !== "system" || mediaQuery === null) {
      return;
    }

    const handleChange = () => {
      applyTheme();
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, [theme, themeId]);
}