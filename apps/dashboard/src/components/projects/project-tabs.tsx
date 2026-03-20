import { useShallow } from "zustand/react/shallow";
import { useProjectStore } from "@/stores/project-store";

export function ProjectTabs(): React.JSX.Element | null {
  const openProjectIds = useProjectStore(
    useShallow((s) => s.openProjectIds),
  );
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const projects = useProjectStore(useShallow((s) => s.projects));
  const setActiveProject = useProjectStore((s) => s.setActiveProject);
  const closeProject = useProjectStore((s) => s.closeProject);

  if (openProjectIds.length === 0) return null;

  const openProjects = openProjectIds
    .map((id) => projects.find((p) => p.id === id))
    .filter((p) => p !== undefined);

  return (
    <div className="flex items-center gap-0.5 border-b border-gray-200 bg-gray-50 px-2 dark:border-gray-700 dark:bg-gray-950">
      {openProjects.map((project) => (
        <div
          key={project.id}
          className={`group flex items-center gap-1.5 border-b-2 px-3 py-1.5 text-xs transition-colors ${
            project.id === activeProjectId
              ? "border-blue-500 bg-white text-blue-600 dark:bg-gray-900 dark:text-blue-400"
              : "border-transparent text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800"
          }`}
        >
          <button
            type="button"
            onClick={() => setActiveProject(project.id)}
            className="max-w-[120px] truncate"
          >
            {project.name}
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              closeProject(project.id);
            }}
            className="ml-0.5 rounded p-0.5 text-gray-400 opacity-0 transition-opacity hover:bg-gray-200 hover:text-gray-600 group-hover:opacity-100 dark:hover:bg-gray-700"
            aria-label={`Close ${project.name}`}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-3 w-3"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      ))}

      <button
        type="button"
        onClick={() => setActiveProject(null)}
        className="ml-1 rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-600 dark:hover:bg-gray-700"
        aria-label="Open project hub"
        title="All Projects"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-3.5 w-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 4v16m8-8H4"
          />
        </svg>
      </button>
    </div>
  );
}
