import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

type Panel =
  | "pipeline"
  | "monitoring"
  | "editor"
  | "terminal"
  | "cost"
  | "preview"
  | "projects";

type Theme = "light" | "dark";

interface UiState {
  sidebarOpen: boolean;
  activePanel: Panel;
  theme: Theme;
}

interface UiActions {
  toggleSidebar: () => void;
  setActivePanel: (panel: Panel) => void;
  setTheme: (theme: Theme) => void;
}

export const useUiStore = create<UiState & UiActions>()(
  devtools(
    immer((set) => ({
      sidebarOpen: true,
      activePanel: "pipeline" as Panel,
      theme: "light" as Theme,

      toggleSidebar: () =>
        set((state) => {
          state.sidebarOpen = !state.sidebarOpen;
        }),

      setActivePanel: (panel: Panel) =>
        set((state) => {
          state.activePanel = panel;
        }),

      setTheme: (theme: Theme) =>
        set((state) => {
          state.theme = theme;
        }),
    })),
    { name: "UiStore" },
  ),
);
