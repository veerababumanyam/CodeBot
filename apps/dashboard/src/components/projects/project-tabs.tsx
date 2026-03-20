import { useShallow } from "zustand/react/shallow";
import { cn } from "@/lib/utils";
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
    <div className="mt-4 flex items-center gap-1 rounded-3xl border border-border bg-panel px-2 py-1 shadow-[var(--theme-shadow-panel)] backdrop-blur-xl">
      {openProjects.map((project) => (
        <div
          key={project.id}
          className={cn(
            "group flex items-center gap-1.5 rounded-2xl px-3 py-2 text-xs transition-all",
            project.id === activeProjectId
              ? "bg-accent-muted text-accent shadow-[var(--theme-shadow-panel)]"
              : "text-muted-foreground hover:bg-panel-muted hover:text-foreground",
          )}
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
            className="ml-0.5 rounded-full p-1 text-muted-foreground opacity-0 transition-all hover:bg-panel hover:text-foreground group-hover:opacity-100"
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
        className="ml-1 rounded-full p-2 text-muted-foreground transition hover:bg-panel-muted hover:text-foreground"
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
