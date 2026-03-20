import type { Project, ProjectStatus } from "@/types/project";
import type { Pipeline } from "@/types/pipeline";
import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<ProjectStatus, { dot: string; label: string }> = {
  created: { dot: "bg-border-strong", label: "Created" },
  brainstorming: { dot: "bg-accent animate-pulse", label: "Brainstorming" },
  planning: { dot: "bg-accent", label: "Planning" },
  in_progress: { dot: "bg-success animate-pulse", label: "Running" },
  review: { dot: "bg-warning", label: "Review" },
  completed: { dot: "bg-success", label: "Completed" },
  failed: { dot: "bg-danger", label: "Failed" },
  paused: { dot: "bg-warning", label: "Paused" },
  cancelled: { dot: "bg-border-strong", label: "Cancelled" },
};

function timeAgo(dateStr: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(dateStr).getTime()) / 1000,
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${String(minutes)}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${String(hours)}h ago`;
  const days = Math.floor(hours / 24);
  return `${String(days)}d ago`;
}

interface ProjectCardProps {
  project: Project;
  isActive: boolean;
  latestPipeline: Pipeline | null;
  activeRunAction: "pause" | "resume" | "cancel" | "retry" | null;
  runActionError: string | undefined;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
  onRunAction: (projectId: string, pipelineId: string, action: "pause" | "resume" | "cancel" | "retry") => void;
}

function formatPipelineMode(mode: Pipeline["mode"]): string {
  return mode === "review_only"
    ? "Review only"
    : mode.charAt(0).toUpperCase() + mode.slice(1);
}

function formatPipelineStatus(status: Pipeline["status"]): string {
  return status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, " ");
}

function formatPhaseName(phase: string): string {
  return phase.replace(/[_-]/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function getFailureReason(errorMessage: string | null | undefined): string | null {
  const trimmed = errorMessage?.trim();

  if (!trimmed) {
    return null;
  }

  return trimmed.length > 140 ? `${trimmed.slice(0, 137)}...` : trimmed;
}

function getFailedStageSummary(
  pipeline: Pipeline | null,
): { name: string; errorMessage: string | null } | null {
  const failedStage = pipeline?.stages.find(
    (stage) => stage.status === "failed" || Boolean(stage.error_message?.trim()),
  );

  if (!failedStage) {
    return null;
  }

  return {
    name: formatPhaseName(failedStage.name),
    errorMessage: getFailureReason(failedStage.error_message),
  };
}

export function ProjectCard({
  project,
  isActive,
  latestPipeline,
  activeRunAction,
  runActionError,
  onOpen,
  onDelete,
  onRunAction,
}: ProjectCardProps): React.JSX.Element {
  const status = STATUS_STYLES[project.status] ?? STATUS_STYLES.created;
  const canPause = latestPipeline?.status === "running";
  const canResume = latestPipeline?.status === "paused";
  const canCancel = latestPipeline?.status === "pending" || latestPipeline?.status === "running" || latestPipeline?.status === "paused";
  const canRetry = latestPipeline?.status === "failed" || latestPipeline?.status === "cancelled";
  const failureReason = getFailureReason(latestPipeline?.error_message);
  const failedStage = getFailedStageSummary(latestPipeline);

  return (
    <div
      className={cn(
        "group relative flex w-full flex-col rounded-[1.75rem] border p-5 text-left transition-all app-surface",
        isActive
          ? "border-border-strong bg-accent-muted shadow-[var(--theme-shadow-floating)]"
          : "hover:border-border-strong hover:-translate-y-0.5",
      )}
    >
      <button
        type="button"
        onClick={() => onOpen(project.id)}
        className="flex w-full flex-col text-left"
      >
        <div className="mb-3 pr-10">
          <h3 className="truncate text-sm font-semibold text-foreground">
            {project.name}
          </h3>
        </div>

        {project.description && (
          <p className="mb-3 line-clamp-2 text-xs text-muted-foreground">
            {project.description}
          </p>
        )}

        <div className="mt-auto flex items-center justify-between">
          <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
            <span className={`inline-block h-2 w-2 rounded-full ${status.dot}`} />
            {status.label}
          </span>
          <span className="text-xs text-muted-foreground/80">
            {timeAgo(project.updated_at)}
          </span>
        </div>

        {latestPipeline ? (
          <div className="mt-4 rounded-2xl border border-border bg-panel-muted px-3 py-2.5">
            <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
              <span className="font-semibold uppercase tracking-wide text-foreground">
                Latest run
              </span>
              <span className="rounded-full bg-accent-muted px-2 py-1 text-foreground">
                {formatPipelineMode(latestPipeline.mode)}
              </span>
              <span className="rounded-full bg-input px-2 py-1">
                {formatPipelineStatus(latestPipeline.status)}
              </span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
              <span className="rounded-full bg-input px-2 py-1">
                {latestPipeline.current_phase
                  ? formatPhaseName(latestPipeline.current_phase)
                  : "Not started"}
              </span>
              <span className="rounded-full bg-input px-2 py-1">
                ${latestPipeline.total_cost_usd.toFixed(2)} · {latestPipeline.total_tokens_used.toLocaleString()} tokens
              </span>
            </div>
            {failureReason ? (
              <div className="mt-3 rounded-xl border border-danger bg-danger-muted px-2.5 py-2 text-[11px] text-danger">
                <span className="font-semibold">Failure reason:</span> {failureReason}
              </div>
            ) : null}
            {failedStage ? (
              <div className="mt-2 rounded-xl border border-warning bg-warning-muted px-2.5 py-2 text-[11px] text-warning">
                <span className="font-semibold">Failed stage:</span> {failedStage.name}
                {failedStage.errorMessage ? ` · ${failedStage.errorMessage}` : ""}
              </div>
            ) : null}
          </div>
        ) : null}
      </button>

      {latestPipeline && (canPause || canResume || canCancel || canRetry) ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {canPause ? (
            <button
              type="button"
              aria-label={`Pause latest run for ${project.name}`}
              disabled={activeRunAction !== null}
              onClick={() => onRunAction(project.id, latestPipeline.id, "pause")}
              className="rounded-full border border-warning px-3 py-1.5 text-xs font-medium text-warning transition-colors hover:bg-warning-muted disabled:cursor-not-allowed disabled:opacity-60"
            >
              {activeRunAction === "pause" ? "Pausing..." : "Pause run"}
            </button>
          ) : null}
          {canResume ? (
            <button
              type="button"
              aria-label={`Resume latest run for ${project.name}`}
              disabled={activeRunAction !== null}
              onClick={() => onRunAction(project.id, latestPipeline.id, "resume")}
              className="rounded-full border border-success px-3 py-1.5 text-xs font-medium text-success transition-colors hover:bg-success-muted disabled:cursor-not-allowed disabled:opacity-60"
            >
              {activeRunAction === "resume" ? "Resuming..." : "Resume run"}
            </button>
          ) : null}
          {canCancel ? (
            <button
              type="button"
              aria-label={`Cancel latest run for ${project.name}`}
              disabled={activeRunAction !== null}
              onClick={() => onRunAction(project.id, latestPipeline.id, "cancel")}
              className="rounded-full border border-danger px-3 py-1.5 text-xs font-medium text-danger transition-colors hover:bg-danger-muted disabled:cursor-not-allowed disabled:opacity-60"
            >
              {activeRunAction === "cancel" ? "Cancelling..." : "Cancel run"}
            </button>
          ) : null}
          {canRetry ? (
            <button
              type="button"
              aria-label={`Retry latest run for ${project.name}`}
              disabled={activeRunAction !== null}
              onClick={() => onRunAction(project.id, latestPipeline.id, "retry")}
              className="rounded-full border border-accent px-3 py-1.5 text-xs font-medium text-accent transition-colors hover:bg-accent-muted disabled:cursor-not-allowed disabled:opacity-60"
            >
              {activeRunAction === "retry" ? "Retrying..." : "Retry run"}
            </button>
          ) : null}
        </div>
      ) : null}

      {runActionError ? (
        <div className="mt-3 rounded-2xl border border-danger bg-danger-muted px-3 py-2 text-xs text-danger">
          {runActionError}
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => onDelete(project.id)}
        className="absolute right-4 top-4 rounded-full p-1.5 text-muted-foreground opacity-0 transition-all hover:bg-danger-muted hover:text-danger group-hover:opacity-100"
        aria-label={`Delete ${project.name}`}
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
            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
          />
        </svg>
      </button>
    </div>
  );
}
