import { useUiStore } from "@/stores/ui-store";
import { useProjectStore } from "@/stores/project-store";
import { ProjectSwitcher } from "@/components/projects/project-switcher";

const PANELS = [
  { key: "pipeline" as const, label: "Pipeline" },
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
    <aside className="flex h-full w-64 flex-col border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
      <div className="border-b border-gray-200 p-4 dark:border-gray-700">
        <h1 className="text-lg font-bold text-gray-900 dark:text-white">
          CodeBot
        </h1>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          AI Development Platform
        </p>
      </div>

      {/* Project switcher */}
      <div className="border-b border-gray-200 p-2 dark:border-gray-700">
        <ProjectSwitcher />
      </div>

      {/* Panel nav — only enabled when a project is active */}
      <nav className="flex-1 space-y-1 p-2">
        {PANELS.map((panel) => (
          <button
            key={panel.key}
            type="button"
            onClick={() => setActivePanel(panel.key)}
            disabled={!activeProjectId}
            className={`flex w-full items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              !activeProjectId
                ? "cursor-not-allowed text-gray-300 dark:text-gray-600"
                : activePanel === panel.key
                  ? "bg-gray-100 text-blue-600 dark:bg-gray-800 dark:text-blue-400"
                  : "text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
            }`}
          >
            {panel.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
