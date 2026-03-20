import { useState, useRef, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { cn } from "@/lib/utils";
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
        className="flex w-full items-center justify-between rounded-2xl border border-border bg-panel-muted px-3.5 py-3 text-sm text-foreground shadow-[var(--theme-shadow-panel)] transition hover:border-border-strong"
      >
        <div className="flex items-center gap-2 overflow-hidden">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent-muted text-xs font-bold text-accent">
            {activeProject ? activeProject.name[0]?.toUpperCase() : "?"}
          </div>
          <span className="truncate font-medium text-foreground">
            {activeProject?.name ?? "No Project"}
          </span>
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={cn(
            "h-4 w-4 shrink-0 text-muted-foreground transition-transform",
            open && "rotate-180",
          )}
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
        <div className="app-surface absolute left-0 right-0 z-50 mt-2 rounded-2xl py-2">
          {openProjects.length > 0 && (
            <>
              <div className="px-3 py-1.5 text-xs font-medium uppercase tracking-[0.24em] text-muted-foreground">
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
                  className={cn(
                    "flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm transition-colors",
                    project.id === activeProjectId
                      ? "bg-accent-muted text-accent"
                      : "text-foreground hover:bg-panel-muted",
                  )}
                >
                  <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-panel text-xs font-bold text-muted-foreground">
                    {project.name[0]?.toUpperCase()}
                  </div>
                  <span className="truncate">{project.name}</span>
                </button>
              ))}
              <div className="my-2 border-t border-border" />
            </>
          )}
          <button
            type="button"
            onClick={() => {
              setActiveProject(null);
              setOpen(false);
            }}
            className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-panel-muted hover:text-foreground"
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
