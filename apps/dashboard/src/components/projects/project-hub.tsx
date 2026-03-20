import { useState, useEffect } from "react";
import { useShallow } from "zustand/react/shallow";
import { projectApi } from "@/api/projects";
import { useProjectStore } from "@/stores/project-store";
import { ProjectCard } from "./project-card";
import { NewProjectWizard } from "./new-project-wizard";
import { ImportProjectWizard } from "./import-project-wizard";
import type { Project } from "@/types/project";

type HubView = "list" | "new" | "import";

export function ProjectHub(): React.JSX.Element {
  const [view, setView] = useState<HubView>("list");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const projects = useProjectStore(useShallow((s) => s.projects));
  const openProjectIds = useProjectStore(
    useShallow((s) => s.openProjectIds),
  );
  const setProjects = useProjectStore((s) => s.setProjects);
  const openProject = useProjectStore((s) => s.openProject);
  const removeProject = useProjectStore((s) => s.removeProject);

  useEffect(() => {
    let cancelled = false;
    async function load(): Promise<void> {
      try {
        const res = await projectApi.list();
        if (!cancelled) {
          setProjects(res.data);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load projects",
          );
          setLoading(false);
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [setProjects]);

  function handleProjectCreated(project: Project): void {
    openProject(project.id);
  }

  async function handleDelete(id: string): Promise<void> {
    try {
      await projectApi.delete(id);
      removeProject(id);
    } catch {
      // Silently fail — could add toast notification
    }
  }

  if (view === "new") {
    return (
      <div className="flex h-full items-start justify-center overflow-auto p-8">
        <NewProjectWizard
          onComplete={handleProjectCreated}
          onCancel={() => setView("list")}
        />
      </div>
    );
  }

  if (view === "import") {
    return (
      <div className="flex h-full items-start justify-center overflow-auto p-8">
        <ImportProjectWizard
          onComplete={handleProjectCreated}
          onCancel={() => setView("list")}
        />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-auto">
      <div className="mx-auto w-full max-w-5xl px-8 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Projects
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Create, import, and manage your software projects
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setView("import")}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              <span className="mr-1.5">&#8599;</span>
              Import
            </button>
            <button
              type="button"
              onClick={() => setView("new")}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              + New Project
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600 dark:border-red-800 dark:bg-red-950 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-500" />
          </div>
        )}

        {/* Empty state */}
        {!loading && projects.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-gray-300 py-20 dark:border-gray-700">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="mb-4 h-12 w-12 text-gray-300 dark:text-gray-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            <h3 className="mb-1 text-lg font-medium text-gray-900 dark:text-white">
              No projects yet
            </h3>
            <p className="mb-6 text-sm text-gray-500 dark:text-gray-400">
              Get started by creating a new project or importing an existing one
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setView("import")}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
              >
                Import Existing
              </button>
              <button
                type="button"
                onClick={() => setView("new")}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                + New Project
              </button>
            </div>
          </div>
        )}

        {/* Project grid */}
        {!loading && projects.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                isActive={openProjectIds.includes(project.id)}
                onOpen={openProject}
                onDelete={handleDelete}
              />
            ))}

            {/* New project placeholder card */}
            <button
              type="button"
              onClick={() => setView("new")}
              className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 p-5 text-gray-400 transition-colors hover:border-blue-400 hover:text-blue-500 dark:border-gray-700 dark:hover:border-blue-500"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="mb-2 h-8 w-8"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              <span className="text-sm font-medium">New Project</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
