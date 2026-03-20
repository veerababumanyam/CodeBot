import { useState, useRef, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { useProjectStore } from "@/stores/project-store";

export function ProjectSwitcher(): React.JSX.Element {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const projects = useProjectStore(useShallow((s) => s.projects));
  const openProjectIds = useProjectStore(
    useShallow((s) => s.openProjectIds),
  );
  const setActiveProject = useProjectStore((s) => s.setActiveProject);
  const openProject = useProjectStore((s) => s.openProject);

  const activeProject = projects.find((p) => p.id === activeProjectId);
  const openProjects = openProjectIds
    .map((id) => projects.find((p) => p.id === id))
    .filter((p) => p !== undefined);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent): void {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-800"
      >
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded bg-blue-100 text-xs font-bold text-blue-600 dark:bg-blue-900 dark:text-blue-400">
            {activeProject ? activeProject.name[0]?.toUpperCase() : "?"}
          </div>
          <span className="truncate font-medium text-gray-900 dark:text-white">
            {activeProject?.name ?? "No Project"}
          </span>
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={`h-4 w-4 shrink-0 text-gray-400 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {open && (
        <div className="absolute left-0 right-0 z-50 mt-1 rounded-lg border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-900">
          {openProjects.length > 0 && (
            <>
              <div className="px-3 py-1.5 text-xs font-medium uppercase tracking-wider text-gray-400">
                Open
              </div>
              {openProjects.map((project) => (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => {
                    setActiveProject(project.id);
                    setOpen(false);
                  }}
                  className={`flex w-full items-center gap-2 px-3 py-2 text-sm ${
                    project.id === activeProjectId
                      ? "bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400"
                      : "text-gray-700 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800"
                  }`}
                >
                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-gray-100 text-xs font-bold text-gray-500 dark:bg-gray-800 dark:text-gray-400">
                    {project.name[0]?.toUpperCase()}
                  </div>
                  <span className="truncate">{project.name}</span>
                </button>
              ))}
              <div className="my-1 border-t border-gray-100 dark:border-gray-800" />
            </>
          )}
          <button
            type="button"
            onClick={() => {
              setActiveProject(null);
              setOpen(false);
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 dark:text-gray-400 dark:hover:bg-gray-800"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
              />
            </svg>
            All Projects
          </button>
        </div>
      )}
    </div>
  );
}
