import type { Pipeline, PipelineStage, StageStatus } from "@/types/pipeline";

export interface PipelineProgressSummary {
  completedStages: number;
  totalStages: number;
  percentComplete: number;
  activeStage: PipelineStage | null;
  waitingStages: number;
  failedStages: number;
}

export function formatPipelineMode(mode: Pipeline["mode"]): string {
  if (mode === "review_only") {
    return "Review only";
  }
  return mode.charAt(0).toUpperCase() + mode.slice(1);
}

export function formatStageLabel(name: string): string {
  return name
    .split(/[_-]/g)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function getPipelineProgressSummary(
  pipeline: Pipeline,
): PipelineProgressSummary {
  const completedStages = pipeline.stages.filter(
    (stage) => stage.status === "completed",
  ).length;
  const activeStage =
    pipeline.stages.find((stage) => stage.status === "running") ??
    pipeline.stages.find((stage) => stage.status === "waiting") ??
    pipeline.stages.find((stage) => stage.status === "failed") ??
    null;
  const waitingStages = pipeline.stages.filter(
    (stage) => stage.status === "waiting",
  ).length;
  const failedStages = pipeline.stages.filter(
    (stage) => stage.status === "failed",
  ).length;
  const totalStages = Math.max(pipeline.total_stages, pipeline.stages.length, 1);
  const percentComplete = Math.round((completedStages / totalStages) * 100);

  return {
    completedStages,
    totalStages,
    percentComplete,
    activeStage,
    waitingStages,
    failedStages,
  };
}

export function getStageTone(status: StageStatus): {
  container: string;
  badge: string;
  label: string;
} {
  switch (status) {
    case "running":
      return {
        container: "border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950",
        badge: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200",
        label: "Running",
      };
    case "completed":
      return {
        container: "border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950",
        badge: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200",
        label: "Completed",
      };
    case "failed":
      return {
        container: "border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950",
        badge: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200",
        label: "Failed",
      };
    case "waiting":
      return {
        container: "border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950",
        badge: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-200",
        label: "Waiting",
      };
    case "skipped":
      return {
        container: "border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900",
        badge: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-200",
        label: "Skipped",
      };
    default:
      return {
        container: "border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900",
        badge: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300",
        label: "Pending",
      };
  }
}