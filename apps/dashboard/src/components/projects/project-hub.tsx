import { useCallback, useEffect, useMemo, useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { pipelineApi } from "@/api/pipelines";
import { projectApi } from "@/api/projects";
import { pipelineSocket } from "@/lib/socket";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useProjectStore } from "@/stores/project-store";
import { useUiStore } from "@/stores/ui-store";
import type { Project } from "@/types/project";
import type { Pipeline, PipelineUpdateEvent } from "@/types/pipeline";
import { ImportProjectWizard } from "./import-project-wizard";
import { NewProjectWizard } from "./new-project-wizard";
import { ProjectCard } from "./project-card";

type HubView = "list" | "new" | "import";
type SortOption = "updated_desc" | "created_desc" | "name_asc" | "name_desc";

const STATUS_OPTIONS: Array<{ value: "all" | Project["status"]; label: string }> = [
  { value: "all", label: "All statuses" },
  { value: "created", label: "Created" },
  { value: "brainstorming", label: "Brainstorming" },
  { value: "planning", label: "Planning" },
  { value: "in_progress", label: "Running" },
  { value: "review", label: "Review" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "paused", label: "Paused" },
  { value: "cancelled", label: "Cancelled" },
];

const SORT_OPTIONS: Array<{ value: SortOption; label: string }> = [
  { value: "updated_desc", label: "Recently updated" },
  { value: "created_desc", label: "Recently created" },
  { value: "name_asc", label: "Name A–Z" },
  { value: "name_desc", label: "Name Z–A" },
];

export function ProjectHub(): React.JSX.Element {
  const [view, setView] = useState<HubView>("list");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | Project["status"]>("all");
  const [openOnly, setOpenOnly] = useState(false);
  const [sortBy, setSortBy] = useState<SortOption>("updated_desc");
  const [latestPipelinesByProject, setLatestPipelinesByProject] = useState<Record<string, Pipeline | null>>({});
  const [runActionByProject, setRunActionByProject] = useState<Record<string, "pause" | "resume" | "cancel" | "retry" | null>>({});
  const [runActionErrors, setRunActionErrors] = useState<Record<string, string>>({});
  const [refreshingRuns, setRefreshingRuns] = useState(false);

  const projects = useProjectStore(useShallow((s) => s.projects));
  const openProjectIds = useProjectStore(useShallow((s) => s.openProjectIds));
  const setProjects = useProjectStore((s) => s.setProjects);
  const openProject = useProjectStore((s) => s.openProject);
  const removeProject = useProjectStore((s) => s.removeProject);
  const setActivePanel = useUiStore((s) => s.setActivePanel);
  const upsertPipeline = usePipelineStore((s) => s.upsertPipeline);
  const setActivePipeline = usePipelineStore((s) => s.setActivePipeline);
  const setFocusedStage = usePipelineStore((s) => s.setFocusedStage);

  const filteredProjects = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    return [...projects]
      .filter((project) => {
        if (statusFilter !== "all" && project.status !== statusFilter) {
          return false;
        }

        if (openOnly && !openProjectIds.includes(project.id)) {
          return false;
        }

        if (!normalizedQuery) {
          return true;
        }

        const haystack = [
          project.name,
          project.description,
          project.project_type,
          project.prd_format,
          Object.keys(project.tech_stack ?? {}).join(" "),
        ]
          .join(" ")
          .toLowerCase();

        return haystack.includes(normalizedQuery);
      })
      .sort((left, right) => {
        switch (sortBy) {
          case "created_desc":
            return new Date(right.created_at).getTime() - new Date(left.created_at).getTime();
          case "name_asc":
            return left.name.localeCompare(right.name);
          case "name_desc":
            return right.name.localeCompare(left.name);
          case "updated_desc":
          default:
            return new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime();
        }
      });
  }, [openOnly, openProjectIds, projects, searchQuery, sortBy, statusFilter]);

  const hasActiveFilters =
    searchQuery.trim().length > 0 || statusFilter !== "all" || openOnly;

  const loadLatestPipelines = useCallback(
    async (projectList: Project[], silent = false): Promise<void> => {
      if (projectList.length === 0) {
        setLatestPipelinesByProject({});
        return;
      }

      if (!silent) {
        setRefreshingRuns(true);
      }

      try {
        const latestEntries = await Promise.all(
          projectList.map(async (project) => {
            if (project.status === "brainstorming") {
              return [project.id, null] as const;
            }

            try {
              const response = await pipelineApi.list(project.id);
              return [project.id, response.data[0] ?? null] as const;
            } catch {
              return [project.id, null] as const;
            }
          }),
        );

        setLatestPipelinesByProject(Object.fromEntries(latestEntries));
      } finally {
        if (!silent) {
          setRefreshingRuns(false);
        }
      }
    },
    [],
  );

  useEffect(() => {
    let cancelled = false;

    async function load(): Promise<void> {
      try {
        const res = await projectApi.list();
        if (!cancelled) {
          setProjects(res.data);
          await loadLatestPipelines(res.data, true);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load projects");
          setLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [loadLatestPipelines, setProjects]);

  useEffect(() => {
    if (view !== "list" || projects.length === 0) {
      return;
    }

    const refreshTimer = window.setInterval(() => {
      void loadLatestPipelines(projects, true);
    }, 15000);

    return () => {
      window.clearInterval(refreshTimer);
    };
  }, [loadLatestPipelines, projects, view]);

  useEffect(() => {
    if (view !== "list" || projects.length === 0) {
      return;
    }

    const channels = projects.map((project) => `project:${project.id}`);
    if (channels.length === 0) {
      return;
    }

    const refreshProjectLatest = async (projectId: string): Promise<void> => {
      try {
        const response = await pipelineApi.list(projectId);
        setLatestPipelinesByProject((current) => ({
          ...current,
          [projectId]: response.data[0] ?? null,
        }));
      } catch {
        // Silent refresh miss; manual refresh remains available.
      }
    };

    const handlePipelineUpdate = (event: PipelineUpdateEvent): void => {
      setLatestPipelinesByProject((current) => {
        const existing = current[event.project_id];
        if (!existing) {
          void refreshProjectLatest(event.project_id);
          return current;
        }

        if (existing.id !== event.pipeline_id) {
          void refreshProjectLatest(event.project_id);
          return current;
        }

        return {
          ...current,
          [event.project_id]: {
            ...existing,
            status: event.status,
            current_phase: event.current_phase,
            started_at: event.started_at,
            completed_at: event.completed_at,
            total_tokens_used: event.total_tokens_used,
            total_cost_usd: event.total_cost_usd,
            error_message: event.error_message,
          },
        };
      });
    };

    pipelineSocket.emit("subscribe", { channels });
    pipelineSocket.on("pipeline:update", handlePipelineUpdate);

    return () => {
      pipelineSocket.emit("unsubscribe", { channels });
      pipelineSocket.off("pipeline:update", handlePipelineUpdate);
    };
  }, [projects, view]);

  function handleProjectCreated(project: Project): void {
    openProject(project.id);
    setActivePanel(project.status === "brainstorming" ? "brainstorm" : "pipeline");
  }

  async function handleOpenProject(projectId: string): Promise<void> {
    const project = projects.find((item) => item.id === projectId);
    openProject(projectId);
    setFocusedStage(null);

    if (project?.status === "brainstorming") {
      setActivePanel("brainstorm");
      return;
    }

    try {
      const pipelines = await pipelineApi.list(projectId);
      const latestPipeline = pipelines.data[0];

      if (latestPipeline) {
        const detailedPipeline = await pipelineApi.get(latestPipeline.id);
        upsertPipeline(detailedPipeline.data);
        setActivePipeline(detailedPipeline.data.id);
      } else {
        setActivePipeline(null);
      }
    } catch {
      setActivePipeline(null);
    }

    setActivePanel("pipeline");
  }

  async function handleInspectFailure(
    projectId: string,
    pipelineId: string,
    stageId: string,
  ): Promise<void> {
    openProject(projectId);

    try {
      const detailedPipeline = await pipelineApi.get(pipelineId);
      upsertPipeline(detailedPipeline.data);
      setActivePipeline(detailedPipeline.data.id);
      setFocusedStage(stageId);
    } catch {
      setActivePipeline(null);
      setFocusedStage(null);
    }

    setActivePanel("pipeline");
  }

  async function handleDelete(id: string): Promise<void> {
    try {
      await projectApi.delete(id);
      removeProject(id);
      setLatestPipelinesByProject((current) => {
        const next = { ...current };
        delete next[id];
        return next;
      });
    } catch {
      // Silently fail — could add toast notification later.
    }
  }

  async function handleRunAction(
    projectId: string,
    pipelineId: string,
    action: "pause" | "resume" | "cancel" | "retry",
  ): Promise<void> {
    setRunActionByProject((current) => ({
      ...current,
      [projectId]: action,
    }));
    setRunActionErrors((current) => {
      const next = { ...current };
      delete next[projectId];
      return next;
    });

    try {
      if (action === "pause") {
        await pipelineApi.pause(pipelineId);
      } else if (action === "resume") {
        await pipelineApi.resume(pipelineId);
      } else if (action === "cancel") {
        await pipelineApi.cancel(pipelineId);
      } else {
        const sourcePipeline = latestPipelinesByProject[projectId];
        const createdPipeline = await pipelineApi.create(projectId, sourcePipeline?.mode ?? "full");
        await pipelineApi.start(createdPipeline.data.id);
        const refreshedPipeline = await pipelineApi.get(createdPipeline.data.id);
        upsertPipeline(refreshedPipeline.data);
        setLatestPipelinesByProject((current) => ({
          ...current,
          [projectId]: refreshedPipeline.data,
        }));
        openProject(projectId);
        setActivePipeline(refreshedPipeline.data.id);
        setActivePanel("pipeline");
        return;
      }

      const refreshedPipeline = await pipelineApi.get(pipelineId);
      upsertPipeline(refreshedPipeline.data);
      setLatestPipelinesByProject((current) => ({
        ...current,
        [projectId]: refreshedPipeline.data,
      }));
    } catch (error) {
      setRunActionErrors((current) => ({
        ...current,
        [projectId]: error instanceof Error ? error.message : `Could not ${action} the latest run.`,
      }));
    } finally {
      setRunActionByProject((current) => ({
        ...current,
        [projectId]: null,
      }));
    }
  }

  function clearFilters(): void {
    setSearchQuery("");
    setStatusFilter("all");
    setOpenOnly(false);
    setSortBy("updated_desc");
  }

  async function handleRefreshRuns(): Promise<void> {
    await loadLatestPipelines(projects);
  }

  if (view === "new") {
    return (
      <div className="flex h-full items-start justify-center overflow-auto p-8">
        <NewProjectWizard onComplete={handleProjectCreated} onCancel={() => setView("list")} />
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
      <div className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-3 py-6 sm:px-4 lg:px-6">
        <section className="app-surface relative overflow-hidden rounded-[2rem] px-6 py-8 sm:px-8 lg:px-10">
          <div className="absolute inset-y-0 right-0 hidden w-72 bg-[radial-gradient(circle_at_top,theme(colors.accent-muted),transparent_68%)] lg:block" />
          <div className="relative flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-muted-foreground">
                Project command center
              </p>
              <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                Launch, revisit, and refine every CodeBot initiative from one place.
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground">
                Create new greenfield builds, import existing workspaces, and jump back into active projects without losing context.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setView("import")}
                className="app-button-secondary rounded-full px-4 py-2.5 text-sm font-medium"
              >
                <span className="mr-1.5">&#8599;</span>
                Import
              </button>
              <button
                type="button"
                onClick={() => setView("new")}
                className="app-button-primary rounded-full px-4 py-2.5 text-sm font-medium"
              >
                + New Project
              </button>
            </div>
          </div>
        </section>

        {error && (
          <div className="rounded-3xl border border-danger bg-danger-muted px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {loading && (
          <div className="app-surface flex items-center justify-center rounded-[1.75rem] py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-border border-t-accent" />
          </div>
        )}

        {!loading && projects.length === 0 && (
          <div className="app-surface flex flex-col items-center justify-center rounded-[2rem] py-20 text-center">
            <div className="mb-6 flex items-center justify-center">
              <img src="/logo.svg" alt="CodeBot" className="block h-12 dark:hidden" />
              <img src="/logo-dark.svg" alt="CodeBot" className="hidden h-12 dark:block" />
            </div>
            <h3 className="mb-1 text-lg font-medium text-foreground">
              No projects yet
            </h3>
            <p className="mb-6 text-sm text-muted-foreground">
              Create, import, and manage your software projects
            </p>
            <p className="mb-6 text-sm text-muted-foreground">
              Get started by creating a new project or importing an existing one
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setView("import")}
                className="app-button-secondary rounded-full px-4 py-2.5 text-sm font-medium"
              >
                Import Existing
              </button>
              <button
                type="button"
                onClick={() => setView("new")}
                className="app-button-primary rounded-full px-4 py-2.5 text-sm font-medium"
              >
                + New Project
              </button>
            </div>
          </div>
        )}

        {!loading && projects.length > 0 && (
          <>
            <div className="app-surface rounded-[1.75rem] p-4 sm:p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div className="grid flex-1 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <label className="flex flex-col gap-1 text-sm font-medium text-foreground">
                    Search
                    <input
                      type="search"
                      value={searchQuery}
                      onChange={(event) => setSearchQuery(event.target.value)}
                      placeholder="Search by name, description, or stack"
                      className="app-field rounded-2xl px-3 py-2.5 text-sm"
                    />
                  </label>

                  <label className="flex flex-col gap-1 text-sm font-medium text-foreground">
                    Status
                    <select
                      aria-label="Status"
                      value={statusFilter}
                      onChange={(event) =>
                        setStatusFilter(event.target.value as "all" | Project["status"])
                      }
                      className="app-select rounded-2xl px-3 py-2.5 text-sm"
                    >
                      {STATUS_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="flex flex-col gap-1 text-sm font-medium text-foreground">
                    Sort by
                    <select
                      aria-label="Sort by"
                      value={sortBy}
                      onChange={(event) => setSortBy(event.target.value as SortOption)}
                      className="app-select rounded-2xl px-3 py-2.5 text-sm"
                    >
                      {SORT_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="flex items-center gap-2 rounded-2xl border border-border bg-input px-3 py-2.5 text-sm font-medium text-foreground">
                    <input
                      type="checkbox"
                      checked={openOnly}
                      onChange={(event) => setOpenOnly(event.target.checked)}
                      aria-label="Open projects only"
                      className="h-4 w-4 rounded border-border text-accent focus:ring-ring"
                    />
                    Open projects only
                  </label>
                </div>

                <div className="flex items-center justify-between gap-3 lg:min-w-72 lg:justify-end">
                  <p className="text-sm text-muted-foreground">
                    Showing {filteredProjects.length} of {projects.length} projects
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        void handleRefreshRuns();
                      }}
                      disabled={refreshingRuns}
                      className="app-button-secondary rounded-full px-3.5 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {refreshingRuns ? "Refreshing runs..." : "Refresh runs"}
                    </button>
                    <button
                      type="button"
                      onClick={clearFilters}
                      disabled={!hasActiveFilters && sortBy === "updated_desc"}
                      className="app-button-secondary rounded-full px-3.5 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Clear filters
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {filteredProjects.length === 0 ? (
              <div className="app-surface flex flex-col items-center justify-center rounded-[1.75rem] border-dashed py-16 text-center">
                <h3 className="mb-1 text-lg font-medium text-foreground">
                  No matching projects
                </h3>
                <p className="mb-4 max-w-md text-sm text-muted-foreground">
                  Try adjusting your search, filters, or sort settings to find the project you need.
                </p>
                <button
                  type="button"
                  onClick={clearFilters}
                  className="app-button-primary rounded-full px-4 py-2.5 text-sm font-medium"
                >
                  Reset project discovery
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {filteredProjects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    isActive={openProjectIds.includes(project.id)}
                    latestPipeline={latestPipelinesByProject[project.id] ?? null}
                    activeRunAction={runActionByProject[project.id] ?? null}
                    runActionError={runActionErrors[project.id]}
                    onOpen={(projectId) => {
                      void handleOpenProject(projectId);
                    }}
                    onInspectFailure={(projectId, pipelineId, stageId) => {
                      void handleInspectFailure(projectId, pipelineId, stageId);
                    }}
                    onDelete={handleDelete}
                    onRunAction={(projectId, pipelineId, action) => {
                      void handleRunAction(projectId, pipelineId, action);
                    }}
                  />
                ))}

                <button
                  type="button"
                  onClick={() => setView("new")}
                  className="app-surface flex flex-col items-center justify-center rounded-[1.75rem] border-2 border-dashed p-5 text-muted-foreground transition-colors hover:border-border-strong hover:text-accent"
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
          </>
        )}
      </div>
    </div>
  );
}
