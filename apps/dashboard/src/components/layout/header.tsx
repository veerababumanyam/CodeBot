import { useUiStore } from "@/stores/ui-store";
import { useProjectStore } from "@/stores/project-store";
import { ProjectTabs } from "@/components/projects/project-tabs";
import { ThemeSwitcher } from "./theme-switcher";

const PANEL_LABELS: Record<string, string> = {
  pipeline: "Pipeline",
  brainstorm: "Brainstorm",
  monitoring: "Monitoring",
  editor: "Editor",
  terminal: "Terminal",
  cost: "Cost",
  preview: "Preview",
  projects: "Projects",
};

export function Header(): React.JSX.Element {
  const activePanel = useUiStore((s) => s.activePanel);
  const toggleSidebar = useUiStore((s) => s.toggleSidebar);
  const activeProjectId = useProjectStore((s) => s.activeProjectId);

  return (
    <div>
      <ProjectTabs />
      <header className="app-surface mt-3 flex h-16 items-center justify-between rounded-3xl border border-border px-5 text-foreground">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
            Workspace view
          </p>
          <h2 className="mt-1 text-base font-semibold text-foreground">
            {activeProjectId
              ? (PANEL_LABELS[activePanel] ?? activePanel)
              : "Projects"}
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <ThemeSwitcher />
          <button
            type="button"
            onClick={toggleSidebar}
            className="flex h-10 w-10 items-center justify-center rounded-full border border-border bg-panel text-muted-foreground transition hover:border-border-strong hover:text-foreground"
            aria-label="Toggle sidebar"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        </div>
      </header>
    </div>
  );
}
