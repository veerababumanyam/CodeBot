import { beforeEach, describe, expect, it } from "vitest";
import { useUiStore } from "./ui-store";

describe("useUiStore", () => {
  beforeEach(() => {
    localStorage.clear();
    useUiStore.setState({
      sidebarOpen: true,
      activePanel: "pipeline",
      theme: "system",
      themeId: "default",
    });
  });

  it("updates appearance mode and theme family independently", () => {
    useUiStore.getState().setTheme("dark");
    useUiStore.getState().setThemeId("midnight");

    const state = useUiStore.getState();
    expect(state.theme).toBe("dark");
    expect(state.themeId).toBe("midnight");
  });

  it("keeps layout state changes isolated from theme state", () => {
    useUiStore.getState().toggleSidebar();
    useUiStore.getState().setActivePanel("preview");

    const state = useUiStore.getState();
    expect(state.sidebarOpen).toBe(false);
    expect(state.activePanel).toBe("preview");
    expect(state.theme).toBe("system");
    expect(state.themeId).toBe("default");
  });
});