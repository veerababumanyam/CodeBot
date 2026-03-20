import { useUiStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";
import { useProjectStore } from "@/stores/project-store";
import { ProjectSwitcher } from "@/components/projects/project-switcher";

const PANELS = [
  { key: "pipeline" as const, label: "Pipeline" },
  { key: "brainstorm" as const, label: "Brainstorm" },
  { key: "monitoring" as const, label: "Monitoring" },
  { key: "editor" as const, label: "Editor" },
  { key: "terminal" as const, label: "Terminal" },
  { key: "cost" as const, label: "Cost" },
  { key: "preview" as const, label: "Preview" },
] as const;

export function Sidebar(): React.JSX.Element {
  const activePanel = useUiStore((s) => s.activePanel);
  const setActivePanel = useUiStore((s) => s.setActivePanel);
  const activeProjectId = useProjectStore((s) => s.activeProjectId);

  return (
    <aside className="app-surface flex h-full w-72 flex-col border-r border-border text-foreground">
      <div className="border-b border-border px-5 py-5">
        <div className="mb-2">
          <img src="/logo.svg" alt="CodeBot" className="block h-8 dark:hidden" />
          <img src="/logo-dark.svg" alt="CodeBot" className="hidden h-8 dark:block" />
        </div>
        <p className="text-xs text-muted-foreground">
          AI Development Platform
        </p>
      </div>

      {/* Project switcher */}
      <div className="border-b border-border px-3 py-3">
        <ProjectSwitcher />
      </div>

      {/* Panel nav — only enabled when a project is active */}
      <nav className="flex-1 space-y-1 p-3">
        {PANELS.map((panel) => (
          <button
            key={panel.key}
            type="button"
            onClick={() => setActivePanel(panel.key)}
            disabled={!activeProjectId}
            className={cn(
              "flex w-full items-center rounded-2xl px-3.5 py-3 text-sm font-medium transition-all",
              !activeProjectId && "cursor-not-allowed text-muted-foreground/60",
              activeProjectId && activePanel === panel.key && "bg-accent-muted text-accent shadow-[var(--theme-shadow-panel)]",
              activeProjectId && activePanel !== panel.key && "text-foreground hover:bg-panel-muted hover:text-foreground",
            )}
          >
            {panel.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
