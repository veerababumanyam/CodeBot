import { useUiStore } from "@/stores/ui-store";
import { useProjectStore } from "@/stores/project-store";
import { ProjectTabs } from "@/components/projects/project-tabs";

const PANEL_LABELS: Record<string, string> = {
  pipeline: "Pipeline",
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
      <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6 dark:border-gray-700 dark:bg-gray-900">
        <h2 className="text-base font-semibold text-gray-900 dark:text-white">
          {activeProjectId
            ? (PANEL_LABELS[activePanel] ?? activePanel)
            : "Projects"}
        </h2>
        <button
          type="button"
          onClick={toggleSidebar}
          className="rounded-lg p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
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
      </header>
    </div>
  );
}
