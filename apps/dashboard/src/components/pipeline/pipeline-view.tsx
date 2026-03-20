import { useOperatorStore } from "@/stores/operator-store";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { AgentNode, type AgentNodeData } from "./agent-node";
import { edgeTypes } from "./edge-types";
import {
  formatPipelineMode,
  formatStageLabel,
  getPipelineProgressSummary,
  getStageTone,
} from "./pipeline-summary";
import { pipelineApi } from "@/api/pipelines";
import type { Pipeline, StageStatus } from "@/types/pipeline";
import {
  usePipelineStore,
  selectActivePipeline,
} from "@/stores/pipeline-store";
import { useAgentStore } from "@/stores/agent-store";
import { usePipelineEvents } from "@/hooks/use-pipeline-events";
import { useAgentStatus } from "@/hooks/use-agent-status";
import { useOperatorSocket } from "@/hooks/use-operator-socket";

const nodeTypes = { agent: AgentNode } as const;

const STAGE_Y_GAP = 180;
const AGENT_X_GAP = 200;

function mapStageStatusToAgentStatus(
  status: StageStatus,
): AgentNodeData["status"] {
  switch (status) {
    case "running":
      return "executing";
    case "completed":
      return "completed";
    case "failed":
      return "failed";
    case "waiting":
      return "reviewing";
    default:
      return "idle";
  }
}

function formatFailureReason(errorMessage: string | null | undefined): string | null {
  const trimmed = errorMessage?.trim();

  if (!trimmed) {
    return null;
  }

  return trimmed.length > 180 ? `${trimmed.slice(0, 177)}...` : trimmed;
}

function formatStageTimestamp(value: string | null): string {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function getFailedStageSummary(
  pipeline: Pipeline | null,
): { id: string; name: string; errorMessage: string | null } | null {
  const failedStage = pipeline?.stages.find(
    (stage) => stage.status === "failed" || Boolean(stage.error_message?.trim()),
  );

  if (!failedStage) {
    return null;
  }

  return {
    id: failedStage.id,
    name: formatStageLabel(failedStage.name),
    errorMessage: formatFailureReason(failedStage.error_message),
  };
}

interface PipelineDiagnosticsBundle {
  pipelineId: string;
  projectId: string;
  mode: string;
  status: Pipeline["status"];
  currentPhase: string;
  totalTokensUsed: number;
  totalCostUsd: number;
  failureReason: string | null;
  failedStage: {
    id: string;
    name: string;
    errorMessage: string | null;
  } | null;
  stages: Array<{
    id: string;
    name: string;
    stageNumber: number;
    status: StageStatus;
    startedAt: string | null;
    completedAt: string | null;
    agents: string[];
    requiresApproval: boolean;
    approvedBy: string | null;
    errorMessage: string | null;
  }>;
}

function buildDiagnosticsData(pipeline: Pipeline): PipelineDiagnosticsBundle {
  const failedStage = getFailedStageSummary(pipeline);

  return {
    pipelineId: pipeline.id,
    projectId: pipeline.project_id,
    mode: formatPipelineMode(pipeline.mode),
    status: pipeline.status,
    currentPhase: pipeline.current_phase
      ? formatStageLabel(pipeline.current_phase)
      : "Not started",
    totalTokensUsed: pipeline.total_tokens_used,
    totalCostUsd: pipeline.total_cost_usd,
    failureReason: pipeline.error_message?.trim() || null,
    failedStage,
    stages: pipeline.stages.map((stage) => ({
      id: stage.id,
      name: formatStageLabel(stage.name),
      stageNumber: stage.stage_number + 1,
      status: stage.status,
      startedAt: stage.started_at,
      completedAt: stage.completed_at,
      agents: stage.agents,
      requiresApproval: Boolean(stage.requires_approval),
      approvedBy: stage.approved_by ?? null,
      errorMessage: stage.error_message?.trim() || null,
    })),
  };
}

function buildDiagnosticsBundle(pipeline: Pipeline): string {
  const diagnostics = buildDiagnosticsData(pipeline);

  return [
    `Pipeline ID: ${diagnostics.pipelineId}`,
    `Project ID: ${diagnostics.projectId}`,
    `Mode: ${diagnostics.mode}`,
    `Status: ${diagnostics.status}`,
    `Current phase: ${diagnostics.currentPhase}`,
    `Tokens used: ${diagnostics.totalTokensUsed.toLocaleString()}`,
    `Total cost: $${diagnostics.totalCostUsd.toFixed(2)}`,
    diagnostics.failureReason ? `Failure reason: ${diagnostics.failureReason}` : null,
    diagnostics.failedStage ? `Failed stage: ${diagnostics.failedStage.name}` : null,
    diagnostics.failedStage?.errorMessage ? `Stage error: ${diagnostics.failedStage.errorMessage}` : null,
  ]
    .filter((value): value is string => Boolean(value))
    .join("\n");
}

function buildDiagnosticsMarkdown(pipeline: Pipeline): string {
  const diagnostics = buildDiagnosticsData(pipeline);

  const stageLines = diagnostics.stages.map((stage) => {
    const detailParts = [
      `Status: ${stage.status}`,
      `Started: ${stage.startedAt ?? "n/a"}`,
      `Completed: ${stage.completedAt ?? "n/a"}`,
      `Agents: ${stage.agents.length > 0 ? stage.agents.join(", ") : "Awaiting agent telemetry"}`,
      `Approval: ${stage.requiresApproval ? stage.approvedBy ? `Approved by ${stage.approvedBy}` : "Required" : "Not required"}`,
    ];

    if (stage.errorMessage) {
      detailParts.push(`Error: ${stage.errorMessage}`);
    }

    return `- Stage ${stage.stageNumber}: ${stage.name} — ${detailParts.join(" · ")}`;
  });

  return [
    `# Pipeline diagnostics`,
    "",
    `- Pipeline ID: ${diagnostics.pipelineId}`,
    `- Project ID: ${diagnostics.projectId}`,
    `- Mode: ${diagnostics.mode}`,
    `- Status: ${diagnostics.status}`,
    `- Current phase: ${diagnostics.currentPhase}`,
    `- Tokens used: ${diagnostics.totalTokensUsed.toLocaleString()}`,
    `- Total cost: $${diagnostics.totalCostUsd.toFixed(2)}`,
    diagnostics.failureReason ? `- Failure reason: ${diagnostics.failureReason}` : null,
    diagnostics.failedStage ? `- Failed stage: ${diagnostics.failedStage.name}` : null,
    diagnostics.failedStage?.errorMessage ? `- Stage error: ${diagnostics.failedStage.errorMessage}` : null,
    "",
    `## Stage timeline`,
    ...stageLines,
  ]
    .filter((value): value is string => Boolean(value))
    .join("\n");
}

function downloadDiagnosticsFile(
  pipeline: Pipeline,
  format: "json" | "markdown",
): void {
  const diagnostics = buildDiagnosticsData(pipeline);
  const isJson = format === "json";
  const content = isJson
    ? JSON.stringify(diagnostics, null, 2)
    : buildDiagnosticsMarkdown(pipeline);
  const blob = new Blob([content], {
    type: isJson ? "application/json" : "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${pipeline.id}-diagnostics.${isJson ? "json" : "md"}`;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function upsertHistoryPipeline(
  current: Pipeline[],
  nextPipeline: Pipeline,
): Pipeline[] {
  const filtered = current.filter((item) => item.id !== nextPipeline.id);
  return [nextPipeline, ...filtered];
}

export function PipelineView(): React.JSX.Element {
  const pipeline = usePipelineStore(selectActivePipeline);
  const focusedStageId = usePipelineStore((s) => s.focusedStageId);
  const upsertPipeline = usePipelineStore((s) => s.upsertPipeline);
  const setActivePipeline = usePipelineStore((s) => s.setActivePipeline);
  const setFocusedStage = usePipelineStore((s) => s.setFocusedStage);
  const agents = useAgentStore((s) => s.agents);
  const stageRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const [approvalNotes, setApprovalNotes] = useState<Record<string, string>>({});
  const [activeApprovalStageId, setActiveApprovalStageId] = useState<string | null>(null);
  const [approvalError, setApprovalError] = useState<string | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [activeHistoryPipelineId, setActiveHistoryPipelineId] = useState<string | null>(null);
  const [historyPipelines, setHistoryPipelines] = useState<Pipeline[]>([]);
  const [activeRunAction, setActiveRunAction] = useState<"pause" | "resume" | "cancel" | "retry" | null>(null);
  const [runActionError, setRunActionError] = useState<string | null>(null);
  const [copiedDiagnosticsId, setCopiedDiagnosticsId] = useState<string | null>(null);
  const [expandedStageIds, setExpandedStageIds] = useState<Record<string, boolean>>({});

  usePipelineEvents(pipeline?.id ?? null, pipeline?.project_id ?? null);
  useAgentStatus(pipeline?.id ?? null, pipeline?.project_id ?? null);
  useOperatorSocket(pipeline?.project_id ?? "");

  useEffect(() => {
    if (!pipeline?.project_id) {
      return;
    }

    const projectId = pipeline.project_id;

    let cancelled = false;

    async function loadHistory(): Promise<void> {
      setHistoryLoading(true);
      setHistoryError(null);

      try {
        const response = await pipelineApi.list(projectId);
        if (cancelled) {
          return;
        }
        setHistoryPipelines(response.data);
      } catch (error) {
        if (cancelled) {
          return;
        }
        setHistoryError(
          error instanceof Error ? error.message : "Could not load pipeline history.",
        );
      } finally {
        if (!cancelled) {
          setHistoryLoading(false);
        }
      }
    }

    void loadHistory();

    return () => {
      cancelled = true;
    };
  }, [pipeline?.project_id]);

  useEffect(() => {
    if (!pipeline) {
      return;
    }

    setHistoryPipelines((current) => upsertHistoryPipeline(current, pipeline));

    setExpandedStageIds((current) => {
      const next: Record<string, boolean> = {};

      for (const stage of pipeline.stages) {
        if (current[stage.id] !== undefined) {
          next[stage.id] = current[stage.id] ?? false;
        }
      }

      return next;
    });
  }, [pipeline]);

  useEffect(() => {
    if (!focusedStageId) {
      return;
    }

    const stageExists = pipeline?.stages.some((stage) => stage.id === focusedStageId);
    if (!stageExists) {
      return;
    }

    setExpandedStageIds((current) => {
      if (current[focusedStageId]) {
        return current;
      }

      return {
        ...current,
        [focusedStageId]: true,
      };
    });

    const stageElement = stageRefs.current[focusedStageId];
    if (typeof stageElement?.scrollIntoView === "function") {
      stageElement.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [focusedStageId, pipeline]);

  async function handlePhaseApproval(
    stageId: string,
    approved: boolean,
  ): Promise<void> {
    if (!pipeline) {
      return;
    }

    setActiveApprovalStageId(stageId);
    setApprovalError(null);

    try {
      const comment = approvalNotes[stageId]?.trim();

      await pipelineApi.approvePhase(pipeline.id, stageId, {
        approved,
        ...(comment ? { comment } : {}),
      });
      const refreshed = await pipelineApi.get(pipeline.id);
      upsertPipeline(refreshed.data);
      setApprovalNotes((current) => ({
        ...current,
        [stageId]: "",
      }));
    } catch (error) {
      setApprovalError(
        error instanceof Error
          ? error.message
          : "Could not update the phase approval status.",
      );
    } finally {
      setActiveApprovalStageId(null);
    }
  }

  async function handleSelectPipeline(pipelineId: string): Promise<void> {
    setActiveHistoryPipelineId(pipelineId);
    setApprovalError(null);

    try {
      const response = await pipelineApi.get(pipelineId);
      upsertPipeline(response.data);
      setActivePipeline(response.data.id);
    } catch (error) {
      setHistoryError(
        error instanceof Error ? error.message : "Could not open the selected pipeline run.",
      );
    } finally {
      setActiveHistoryPipelineId(null);
    }
  }

  async function handleInspectFailure(
    targetPipeline: Pipeline,
    stageId: string,
  ): Promise<void> {
    setFocusedStage(stageId);

    if (pipeline?.id === targetPipeline.id) {
      return;
    }

    await handleSelectPipeline(targetPipeline.id);
  }

  async function handleRunAction(action: "pause" | "resume" | "cancel" | "retry"): Promise<void> {
    if (!pipeline) {
      return;
    }

    setActiveRunAction(action);
    setRunActionError(null);

    try {
      if (action === "pause") {
        await pipelineApi.pause(pipeline.id);
      } else if (action === "resume") {
        await pipelineApi.resume(pipeline.id);
      } else if (action === "cancel") {
        await pipelineApi.cancel(pipeline.id);
      } else {
        const createdPipeline = await pipelineApi.create(pipeline.project_id, pipeline.mode);
        await pipelineApi.start(createdPipeline.data.id);
        const refreshedPipeline = await pipelineApi.get(createdPipeline.data.id);
        upsertPipeline(refreshedPipeline.data);
        setActivePipeline(refreshedPipeline.data.id);
        setHistoryPipelines((current) => upsertHistoryPipeline(current, refreshedPipeline.data));
        return;
      }

      const refreshed = await pipelineApi.get(pipeline.id);
      upsertPipeline(refreshed.data);
    } catch (error) {
      setRunActionError(
        error instanceof Error ? error.message : `Could not ${action} the pipeline run.`,
      );
    } finally {
      setActiveRunAction(null);
    }
  }

  async function handleCopyDiagnostics(targetPipeline: Pipeline): Promise<void> {
    if (!navigator.clipboard?.writeText) {
      return;
    }

    await navigator.clipboard.writeText(buildDiagnosticsBundle(targetPipeline));
    setCopiedDiagnosticsId(targetPipeline.id);
  }

  function handleExportDiagnostics(
    targetPipeline: Pipeline,
    format: "json" | "markdown",
  ): void {
    downloadDiagnosticsFile(targetPipeline, format);
  }

  const historyEntries = useMemo(() => {
    if (!pipeline) {
      return [];
    }

    const runs = upsertHistoryPipeline(historyPipelines, pipeline);

    return runs
      .filter((item) => item.project_id === pipeline.project_id)
      .sort((left, right) => {
        const leftTime = new Date(left.started_at ?? left.completed_at ?? 0).getTime();
        const rightTime = new Date(right.started_at ?? right.completed_at ?? 0).getTime();
        return rightTime - leftTime;
      });
  }, [historyPipelines, pipeline]);

  function formatHistoryTimestamp(value: string | null): string {
    if (!value) {
      return "Not started";
    }

    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(value));
  }

  function formatHistoryStatus(status: string): string {
    return status.replace(/_/g, " ");
  }

  function toggleStageDetails(stageId: string, expanded: boolean): void {
    setExpandedStageIds((current) => ({
      ...current,
      [stageId]: expanded,
    }));
  }

  const { nodes, edges } = useMemo(() => {
    if (!pipeline) return { nodes: [] as Node[], edges: [] as Edge[] };

    const builtNodes: Node<AgentNodeData>[] = [];
    const builtEdges: Edge[] = [];

    for (const stage of pipeline.stages) {
      const stageAgents = stage.agents
        .map((agentId) => agents[agentId])
        .filter((a) => a !== undefined);

      if (stageAgents.length === 0) {
        builtNodes.push({
          id: stage.id,
          type: "agent",
          position: {
            x: 0,
            y: stage.stage_number * STAGE_Y_GAP,
          },
          data: {
            label: stage.name,
            agentType: stage.phase_type ?? "pipeline stage",
            status: mapStageStatusToAgentStatus(stage.status),
            stageNumber: stage.stage_number,
          },
        });
        continue;
      }

      const startX =
        stageAgents.length > 1
          ? -((stageAgents.length - 1) * AGENT_X_GAP) / 2
          : 0;

      stageAgents.forEach((agent, idx) => {
        builtNodes.push({
          id: agent.id,
          type: "agent",
          position: {
            x: startX + idx * AGENT_X_GAP,
            y: stage.stage_number * STAGE_Y_GAP,
          },
          data: {
            label: agent.name,
            agentType: agent.agent_type,
            status: agent.status,
            stageNumber: stage.stage_number,
          },
        });
      });
    }

    // Build sequential stage connection edges
    const sortedStages = [...pipeline.stages].sort(
      (a, b) => a.stage_number - b.stage_number,
    );

    for (let i = 0; i < sortedStages.length - 1; i++) {
      const currentStage = sortedStages[i];
      const nextStage = sortedStages[i + 1];

      if (!currentStage || !nextStage) continue;

      const currentAgents = currentStage.agents.length > 0
        ? currentStage.agents
        : [currentStage.id];
      const nextAgents = nextStage.agents.length > 0
        ? nextStage.agents
        : [nextStage.id];

      // Connect last agent of current stage to first agent of next stage
      const sourceId = currentAgents[currentAgents.length - 1];
      const targetId = nextAgents[0];

      if (sourceId && targetId) {
        builtEdges.push({
          id: `edge-s${String(currentStage.stage_number)}-s${String(nextStage.stage_number)}`,
          source: sourceId,
          target: targetId,
          type: "control",
        });
      }
    }

    return { nodes: builtNodes, edges: builtEdges };
  }, [pipeline, agents]);

  const progress = useMemo(
    () => (pipeline ? getPipelineProgressSummary(pipeline) : null),
    [pipeline],
  );

  // Get all operator status/actions, filter by projectId in render
  const allOperatorStatus = useOperatorStore((s) => s.status);
  const allOperatorActions = useOperatorStore((s) => s.actions);
  const projectId = pipeline?.project_id;
  const operatorStatus = projectId ? allOperatorStatus[projectId] : undefined;
  const operatorActions = projectId ? allOperatorActions[projectId] ?? [] : [];

  const canPause = pipeline?.status === "running";
  const canResume = pipeline?.status === "paused";
  const canCancel = pipeline?.status === "pending" || pipeline?.status === "running" || pipeline?.status === "paused";
  const canRetry = pipeline?.status === "failed" || pipeline?.status === "cancelled";
  const pipelineFailureReason = formatFailureReason(pipeline?.error_message);
  const failedStage = getFailedStageSummary(pipeline);

  if (!pipeline) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        Select a pipeline to view its execution graph
      </div>
    );
  }

  return (
    <div className="grid h-full grid-cols-12 gap-4 p-4">
      <aside className="col-span-4 flex min-h-0 flex-col gap-4 xl:col-span-3">
        <div className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
                Execution overview
              </p>
              <h2 className="mt-1 text-lg font-semibold text-gray-900 dark:text-white">
                {formatPipelineMode(pipeline.mode)} pipeline
              </h2>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Current phase: {pipeline.current_phase ? formatStageLabel(pipeline.current_phase) : "Not started"}
              </p>
            </div>
            <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-200">
              {pipeline.status}
            </span>
          </div>

          <div className="mt-4">
            <div className="mb-4 flex flex-wrap gap-2">
              {canPause ? (
                <button
                  type="button"
                  aria-label="Pause pipeline run"
                  disabled={activeRunAction !== null}
                  onClick={() => {
                    void handleRunAction("pause");
                  }}
                  className="rounded-lg border border-amber-300 px-3 py-2 text-sm font-medium text-amber-700 hover:bg-amber-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-amber-800 dark:text-amber-300 dark:hover:bg-amber-950"
                >
                  {activeRunAction === "pause" ? "Pausing..." : "Pause run"}
                </button>
              ) : null}
              {canResume ? (
                <button
                  type="button"
                  aria-label="Resume pipeline run"
                  disabled={activeRunAction !== null}
                  onClick={() => {
                    void handleRunAction("resume");
                  }}
                  className="rounded-lg border border-emerald-300 px-3 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-emerald-800 dark:text-emerald-300 dark:hover:bg-emerald-950"
                >
                  {activeRunAction === "resume" ? "Resuming..." : "Resume run"}
                </button>
              ) : null}
              {canCancel ? (
                <button
                  type="button"
                  aria-label="Cancel pipeline run"
                  disabled={activeRunAction !== null}
                  onClick={() => {
                    void handleRunAction("cancel");
                  }}
                  className="rounded-lg border border-red-300 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-950"
                >
                  {activeRunAction === "cancel" ? "Cancelling..." : "Cancel run"}
                </button>
              ) : null}
              {canRetry ? (
                <button
                  type="button"
                  aria-label="Retry pipeline run"
                  disabled={activeRunAction !== null}
                  onClick={() => {
                    void handleRunAction("retry");
                  }}
                  className="rounded-lg border border-blue-300 px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-blue-800 dark:text-blue-300 dark:hover:bg-blue-950"
                >
                  {activeRunAction === "retry" ? "Retrying..." : "Retry run"}
                </button>
              ) : null}
            </div>

            {runActionError ? (
              <div className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
                {runActionError}
              </div>
            ) : null}

            {pipelineFailureReason ? (
              <div className="mb-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
                <span className="font-semibold">Failure reason:</span> {pipelineFailureReason}
              </div>
            ) : null}

            {failedStage ? (
              <div className="mb-3 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
                <span className="font-semibold">Failed stage:</span> {failedStage.name}
                {failedStage.errorMessage ? ` · ${failedStage.errorMessage}` : ""}
                <button
                  type="button"
                  onClick={() => setFocusedStage(failedStage.id)}
                  className="ml-2 rounded-full border border-amber-300 px-2.5 py-1 text-xs font-medium transition-colors hover:bg-amber-100 dark:border-amber-700 dark:hover:bg-amber-900"
                >
                  Jump to stage
                </button>
              </div>
            ) : null}

            {(pipelineFailureReason || failedStage) ? (
              <div className="mb-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  aria-label="Copy pipeline diagnostics"
                  onClick={() => {
                    void handleCopyDiagnostics(pipeline);
                  }}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                >
                  {copiedDiagnosticsId === pipeline.id ? "Diagnostics copied" : "Copy diagnostics"}
                </button>
                <button
                  type="button"
                  aria-label="Export diagnostics as JSON"
                  onClick={() => {
                    handleExportDiagnostics(pipeline, "json");
                  }}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                >
                  Export JSON
                </button>
                <button
                  type="button"
                  aria-label="Export diagnostics as Markdown"
                  onClick={() => {
                    handleExportDiagnostics(pipeline, "markdown");
                  }}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                >
                  Export Markdown
                </button>
              </div>
            ) : null}

            <div className="mb-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>Progress</span>
              <span>{progress?.percentComplete ?? 0}%</span>
            </div>
            <div className="h-2 rounded-full bg-gray-200 dark:bg-gray-700">
              <div
                className="h-2 rounded-full bg-blue-500 transition-all"
                style={{ width: `${String(progress?.percentComplete ?? 0)}%` }}
              />
            </div>
            <div className="mt-3 grid grid-cols-2 gap-3 text-sm">

            {/* Operator status and actions */}
            {(operatorStatus || operatorActions.length > 0) && (
              <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50 p-3 text-xs text-indigo-900 dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-200">
                <div className="mb-1 font-semibold">Operator activity</div>
                {operatorStatus && (
                  <div data-testid="operator-status" className="mb-2">
                    <span className="font-medium">Status:</span> {operatorStatus}
                  </div>
                )}
                {operatorActions.length > 0 && (
                  <div data-testid="operator-actions">
                    <span className="font-medium">Recent actions:</span>
                    <ul className="mt-1 list-disc pl-4">
                      {operatorActions.slice(-5).reverse().map((action, idx) => (
                        <li key={idx}>
                          <span className="font-mono">{action.action}</span>
                          {action.payload?.by && (
                            <span> by <span className="font-semibold">{action.payload.by}</span></span>
                          )}
                          <span className="ml-2 text-gray-500 dark:text-gray-400">{new Date(action.timestamp).toLocaleTimeString()}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
              <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-800">
                <div className="text-xs text-gray-500 dark:text-gray-400">Completed</div>
                <div className="mt-1 font-semibold text-gray-900 dark:text-white">
                  {progress?.completedStages ?? 0}/{progress?.totalStages ?? pipeline.total_stages}
                </div>
              </div>
              <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-800">
                <div className="text-xs text-gray-500 dark:text-gray-400">Active stage</div>
                <div className="mt-1 font-semibold text-gray-900 dark:text-white">
                  {progress?.activeStage ? formatStageLabel(progress.activeStage.name) : "—"}
                </div>
              </div>
              <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-800">
                <div className="text-xs text-gray-500 dark:text-gray-400">Tokens</div>
                <div className="mt-1 font-semibold text-gray-900 dark:text-white">
                  {pipeline.total_tokens_used.toLocaleString()}
                </div>
              </div>
              <div className="rounded-xl bg-gray-50 p-3 dark:bg-gray-800">
                <div className="text-xs text-gray-500 dark:text-gray-400">Cost</div>
                <div className="mt-1 font-semibold text-gray-900 dark:text-white">
                  ${pipeline.total_cost_usd.toFixed(2)}
                </div>
              </div>
            </div>

            {(progress?.waitingStages ?? 0) > 0 || (progress?.failedStages ?? 0) > 0 ? (
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                {(progress?.waitingStages ?? 0) > 0 && (
                  <span className="rounded-full bg-amber-100 px-2.5 py-1 font-medium text-amber-700 dark:bg-amber-900 dark:text-amber-200">
                    {progress?.waitingStages} waiting for review
                  </span>
                )}
                {(progress?.failedStages ?? 0) > 0 && (
                  <span className="rounded-full bg-red-100 px-2.5 py-1 font-medium text-red-700 dark:bg-red-900 dark:text-red-200">
                    {progress?.failedStages} failed stage{progress?.failedStages === 1 ? "" : "s"}
                  </span>
                )}
              </div>
            ) : null}
          </div>
        </div>

        <div className="min-h-0 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Run history
            </h3>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {historyEntries.length} run{historyEntries.length === 1 ? "" : "s"}
            </span>
          </div>

          {historyLoading ? (
            <div className="rounded-xl border border-dashed border-gray-200 px-3 py-4 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
              Loading pipeline runs...
            </div>
          ) : historyEntries.length === 0 ? (
            <div className="rounded-xl border border-dashed border-gray-200 px-3 py-4 text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
              No previous runs available for this project yet.
            </div>
          ) : (
            <div className="space-y-2 overflow-y-auto pr-1">
              {historyEntries.map((entry, index) => {
                const isCurrent = entry.id === pipeline.id;
                const isSwitching = activeHistoryPipelineId === entry.id;
                const historyFailureReason = formatFailureReason(entry.error_message);
                const historyFailedStage = getFailedStageSummary(entry);

                return (
                  <div
                    key={entry.id}
                    className={`w-full rounded-xl border p-3 text-left transition ${
                      isCurrent
                        ? "border-blue-300 bg-blue-50 dark:border-blue-800 dark:bg-blue-950"
                        : "border-gray-200 hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:hover:border-gray-600 dark:hover:bg-gray-800"
                    }`}
                  >
                    <button
                      type="button"
                      aria-label={`Open pipeline run ${index + 1}`}
                      onClick={() => {
                        if (!isCurrent) {
                          void handleSelectPipeline(entry.id);
                        }
                      }}
                      disabled={isSwitching || isCurrent}
                      className="w-full text-left disabled:cursor-not-allowed disabled:opacity-80"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                            Run {index + 1}
                          </p>
                          <h4 className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                            {formatPipelineMode(entry.mode)} pipeline
                          </h4>
                        </div>
                        <span className="rounded-full bg-gray-100 px-2.5 py-1 text-[11px] font-medium text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                          {formatHistoryStatus(entry.status)}
                        </span>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-gray-500 dark:text-gray-400">
                        <span className="rounded-full bg-white/80 px-2 py-1 dark:bg-black/10">
                          {entry.current_phase ? formatStageLabel(entry.current_phase) : "No active phase"}
                        </span>
                        <span className="rounded-full bg-white/80 px-2 py-1 dark:bg-black/10">
                          {formatHistoryTimestamp(entry.started_at ?? entry.completed_at)}
                        </span>
                        <span className="rounded-full bg-white/80 px-2 py-1 dark:bg-black/10">
                          ${entry.total_cost_usd.toFixed(2)} · {entry.total_tokens_used.toLocaleString()} tokens
                        </span>
                      </div>
                      {historyFailureReason ? (
                        <div className="mt-2 rounded-lg border border-red-200 bg-red-50 px-2.5 py-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
                          <span className="font-semibold">Failure reason:</span> {historyFailureReason}
                        </div>
                      ) : null}
                      {historyFailedStage ? (
                        <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-2 text-xs text-amber-800 dark:border-amber-800 dark:bg-amber-950 dark:text-amber-200">
                          <span className="font-semibold">Failed stage:</span> {historyFailedStage.name}
                          {historyFailedStage.errorMessage ? ` · ${historyFailedStage.errorMessage}` : ""}
                        </div>
                      ) : null}
                    </button>
                    {historyFailureReason || historyFailedStage ? (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {historyFailedStage ? (
                          <button
                            type="button"
                            aria-label={`Inspect failure for run ${index + 1}`}
                            onClick={() => {
                              void handleInspectFailure(entry, historyFailedStage.id);
                            }}
                            className="rounded-lg border border-amber-300 px-2.5 py-1.5 text-xs font-medium text-amber-800 transition-colors hover:bg-amber-100 dark:border-amber-800 dark:text-amber-200 dark:hover:bg-amber-900"
                          >
                            Inspect failure
                          </button>
                        ) : null}
                        <button
                          type="button"
                          aria-label={`Copy diagnostics for run ${index + 1}`}
                          onClick={() => {
                            void handleCopyDiagnostics(entry);
                          }}
                          className="rounded-lg border border-gray-300 px-2.5 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                        >
                          {copiedDiagnosticsId === entry.id ? "Diagnostics copied" : "Copy diagnostics"}
                        </button>
                        <button
                          type="button"
                          aria-label={`Export diagnostics as JSON for run ${index + 1}`}
                          onClick={() => {
                            handleExportDiagnostics(entry, "json");
                          }}
                          className="rounded-lg border border-gray-300 px-2.5 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                        >
                          Export JSON
                        </button>
                        <button
                          type="button"
                          aria-label={`Export diagnostics as Markdown for run ${index + 1}`}
                          onClick={() => {
                            handleExportDiagnostics(entry, "markdown");
                          }}
                          className="rounded-lg border border-gray-300 px-2.5 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
                        >
                          Export Markdown
                        </button>
                      </div>
                    ) : null}
                    {isCurrent ? (
                      <p className="mt-2 text-xs font-medium text-blue-700 dark:text-blue-300">
                        Active run
                      </p>
                    ) : isSwitching ? (
                      <p className="mt-2 text-xs font-medium text-gray-500 dark:text-gray-400">
                        Opening run...
                      </p>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}

          {historyError ? (
            <div className="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {historyError}
            </div>
          ) : null}
        </div>

        <div className="min-h-0 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Stage timeline
            </h3>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {pipeline.stages.length} stages
            </span>
          </div>
          <div className="space-y-3 overflow-y-auto pr-1">
            {pipeline.stages.map((stage) => {
              const tone = getStageTone(stage.status);
              const isAwaitingDecision =
                stage.requires_approval && stage.status === "waiting";
              const isActing = activeApprovalStageId === stage.id;
              const hasStageError = Boolean(stage.error_message?.trim());
              const isExpanded = expandedStageIds[stage.id] ?? (
                isAwaitingDecision ||
                focusedStageId === stage.id ||
                stage.status === "failed" ||
                hasStageError
              );
              const stageLabel = formatStageLabel(stage.name);
              return (
                <div
                  key={stage.id}
                  ref={(element) => {
                    stageRefs.current[stage.id] = element;
                  }}
                  className={`rounded-xl border p-3 ${tone.container} ${focusedStageId === stage.id ? "ring-2 ring-amber-400 ring-offset-2 dark:ring-amber-500 dark:ring-offset-gray-900" : ""}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
                        Stage {stage.stage_number + 1}
                      </p>
                      <h4 className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                        {stageLabel}
                      </h4>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {stage.phase_type ? formatStageLabel(stage.phase_type) : "Pipeline stage"}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-2">
                      <span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${tone.badge}`}>
                        {tone.label}
                      </span>
                      <button
                        type="button"
                        aria-expanded={isExpanded}
                        aria-label={`${isExpanded ? "Hide" : "Show"} details for ${stageLabel}`}
                        onClick={() => toggleStageDetails(stage.id, !isExpanded)}
                        className="rounded-full border border-gray-300 px-2.5 py-1 text-[11px] font-medium text-gray-600 transition-colors hover:bg-white/80 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
                      >
                        {isExpanded ? "Hide details" : "Show details"}
                      </button>
                    </div>
                  </div>
                  {focusedStageId === stage.id ? (
                    <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
                      Focused failure
                    </p>
                  ) : null}
                  <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-gray-500 dark:text-gray-400">
                    {stage.requires_approval ? (
                      <span className="rounded-full bg-white/80 px-2 py-1 dark:bg-black/10">
                        {stage.approved_by ? `Approved by ${stage.approved_by}` : "Human approval"}
                      </span>
                    ) : null}
                    {stage.agents.length > 0 ? (
                      <span className="rounded-full bg-white/80 px-2 py-1 dark:bg-black/10">
                        {stage.agents.length} agent{stage.agents.length === 1 ? "" : "s"}
                      </span>
                    ) : (
                      <span className="rounded-full bg-white/80 px-2 py-1 dark:bg-black/10">
                        Awaiting agent telemetry
                      </span>
                    )}
                  </div>
                  {isExpanded ? (
                    <div className="mt-3 space-y-3 rounded-lg border border-gray-200 bg-white/70 p-3 dark:border-gray-700 dark:bg-black/10">
                      <dl className="grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-gray-300">
                        <div>
                          <dt className="font-semibold uppercase tracking-wide text-gray-400">
                            Started
                          </dt>
                          <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                            {formatStageTimestamp(stage.started_at)}
                          </dd>
                        </div>
                        <div>
                          <dt className="font-semibold uppercase tracking-wide text-gray-400">
                            Completed
                          </dt>
                          <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                            {formatStageTimestamp(stage.completed_at)}
                          </dd>
                        </div>
                        <div>
                          <dt className="font-semibold uppercase tracking-wide text-gray-400">
                            Approval
                          </dt>
                          <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                            {stage.requires_approval
                              ? stage.approved_by
                                ? `Approved by ${stage.approved_by}`
                                : isAwaitingDecision
                                  ? "Awaiting reviewer decision"
                                  : "Required"
                              : "Not required"}
                          </dd>
                        </div>
                        <div>
                          <dt className="font-semibold uppercase tracking-wide text-gray-400">
                            Agents
                          </dt>
                          <dd className="mt-1 text-sm text-gray-900 dark:text-white">
                            {stage.agents.length > 0 ? stage.agents.join(", ") : "Awaiting agent telemetry"}
                          </dd>
                        </div>
                      </dl>
                      {stage.error_message ? (
                        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
                          {stage.error_message}
                        </div>
                      ) : null}
                      {isAwaitingDecision ? (
                        <div className="space-y-3 rounded-lg border border-amber-200 bg-white/70 p-3 dark:border-amber-800 dark:bg-black/10">
                          <label className="block">
                            <span className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                              Review note
                            </span>
                            <textarea
                              value={approvalNotes[stage.id] ?? ""}
                              onChange={(event) => {
                                const value = event.target.value;
                                setApprovalNotes((current) => ({
                                  ...current,
                                  [stage.id]: value,
                                }));
                              }}
                              rows={3}
                              aria-label={`Review note for ${stage.name}`}
                              placeholder="Optional note for the team or agent handoff"
                              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white"
                            />
                          </label>
                          <div className="flex items-center justify-end gap-2">
                            <button
                              type="button"
                              aria-label={`Request changes for ${stage.name}`}
                              disabled={isActing}
                              onClick={() => {
                                void handlePhaseApproval(stage.id, false);
                              }}
                              className="rounded-lg border border-red-300 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-950"
                            >
                              {isActing ? "Updating..." : "Request changes"}
                            </button>
                            <button
                              type="button"
                              aria-label={`Approve ${stage.name}`}
                              disabled={isActing}
                              onClick={() => {
                                void handlePhaseApproval(stage.id, true);
                              }}
                              className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-500"
                            >
                              {isActing ? "Updating..." : "Approve stage"}
                            </button>
                          </div>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
          {approvalError ? (
            <div className="mt-3 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
              {approvalError}
            </div>
          ) : null}
        </div>
      </aside>

      <section className="col-span-8 min-h-0 rounded-2xl border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-900 xl:col-span-9">
        <div className="flex h-full flex-col">
          <div className="border-b border-gray-200 px-4 py-3 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              Execution graph
            </h3>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Live stage flow with agent nodes when telemetry is available.
            </p>
          </div>
          <div className="min-h-0 flex-1">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              fitView
              proOptions={{ hideAttribution: true }}
            >
              <Background variant={BackgroundVariant.Dots} />
              <Controls />
              <MiniMap />
            </ReactFlow>
          </div>
        </div>
      </section>
    </div>
  );
}
