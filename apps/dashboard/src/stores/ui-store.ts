import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { ThemeId, ThemeMode } from "@/theme/themes";

type Panel =
  | "pipeline"
  | "brainstorm"
  | "monitoring"
  | "editor"
  | "terminal"
  | "cost"
  | "preview"
  | "projects";

interface UiState {
  sidebarOpen: boolean;
  activePanel: Panel;
  theme: ThemeMode;
  themeId: ThemeId;
}

interface UiActions {
  toggleSidebar: () => void;
  setActivePanel: (panel: Panel) => void;
  setTheme: (theme: ThemeMode) => void;
  setThemeId: (themeId: ThemeId) => void;
}

export const useUiStore = create<UiState & UiActions>()(
  devtools(
    persist(
      immer((set) => ({
        sidebarOpen: true,
        activePanel: "pipeline" as Panel,
        theme: "system" as ThemeMode,
        themeId: "default" as ThemeId,

        toggleSidebar: () =>
          set((state) => {
            state.sidebarOpen = !state.sidebarOpen;
          }),

        setActivePanel: (panel: Panel) =>
          set((state) => {
            state.activePanel = panel;
          }),

        setTheme: (theme: ThemeMode) =>
          set((state) => {
            state.theme = theme;
          }),

        setThemeId: (themeId: ThemeId) =>
          set((state) => {
            state.themeId = themeId;
          }),
      })),
      {
        name: "codebot-ui",
        partialize: (state) => ({
          sidebarOpen: state.sidebarOpen,
          theme: state.theme,
          themeId: state.themeId,
        }),
      },
    ),
    { name: "UiStore" },
  ),
);
