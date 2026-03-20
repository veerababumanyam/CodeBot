import { api } from "./client";
import type {
  Pipeline,
  PipelineMode,
  PipelineStage,
  PipelineStatus,
  StageStatus,
} from "@/types/pipeline";

interface ResponseEnvelope<T> {
  status: "success";
  data: T;
  meta: { request_id: string; timestamp: string };
}

interface PaginatedEnvelope<T> {
  status: "success";
  data: T[];
  meta: { request_id: string; timestamp: string };
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
  } | null;
}

interface BackendPipelineResponse {
  id: string;
  project_id: string;
  status: PipelineStatus;
  current_phase: string;
  started_at: string | null;
  completed_at: string | null;
  total_tokens_used: number;
  total_cost_usd: number;
  graph_definition?: {
    mode?: string;
    config?: Record<string, unknown> | null;
  } | null;
  error_message?: string | null;
  config?: Record<string, unknown> | null;
  mode?: string | null;
}

interface BackendPipelinePhaseResponse {
  id: string;
  name: string;
  phase_type: string;
  status: string;
  order: number;
  requires_approval: boolean;
  approved_by: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message?: string | null;
}

interface PhaseApprovalPayload {
  approved: boolean;
  comment?: string;
}

interface PipelineActionResponse {
  id: string;
  status: PipelineStatus;
  timestamp: string;
}

function normalizeStageStatus(status: string): StageStatus {
  switch (status) {
    case "running":
      return "running";
    case "completed":
      return "completed";
    case "failed":
      return "failed";
    case "skipped":
      return "skipped";
    case "waiting_approval":
      return "waiting";
    case "pending":
    default:
      return "idle";
  }
}

function normalizeMode(mode: string | null | undefined): PipelineMode {
  const normalized = (mode ?? "full").replace(/-/g, "_");
  if (normalized === "quick" || normalized === "review_only") {
    return normalized;
  }
  return "full";
}

function normalizeStages(phases: BackendPipelinePhaseResponse[]): PipelineStage[] {
  return phases.map((phase) => ({
    id: phase.id,
    name: phase.name,
    stage_number: phase.order,
    status: normalizeStageStatus(phase.status),
    started_at: phase.started_at,
    completed_at: phase.completed_at,
    agents: [],
    phase_type: phase.phase_type,
    requires_approval: phase.requires_approval,
    approved_by: phase.approved_by,
    error_message: phase.error_message ?? null,
  }));
}

export function normalizePipeline(
  pipeline: BackendPipelineResponse,
  phases: BackendPipelinePhaseResponse[] = [],
): Pipeline {
  return {
    id: pipeline.id,
    project_id: pipeline.project_id,
    mode: normalizeMode(pipeline.mode ?? pipeline.graph_definition?.mode),
    status: pipeline.status,
    current_phase: pipeline.current_phase,
    total_stages: phases.length,
    stages: normalizeStages(phases),
    config: pipeline.config ?? pipeline.graph_definition?.config ?? null,
    started_at: pipeline.started_at,
    completed_at: pipeline.completed_at,
    total_tokens_used: pipeline.total_tokens_used,
    total_cost_usd: pipeline.total_cost_usd,
    error_message: pipeline.error_message ?? null,
  };
}

export const pipelineApi = {
  async list(projectId: string) {
    const response = await api.get<PaginatedEnvelope<BackendPipelineResponse>>(
      `/api/v1/projects/${projectId}/pipelines`,
    );
    return {
      ...response,
      data: response.data.map((pipeline) => normalizePipeline(pipeline)),
    };
  },

  async get(pipelineId: string) {
    const [pipelineResponse, phasesResponse] = await Promise.all([
      api.get<ResponseEnvelope<BackendPipelineResponse>>(
        `/api/v1/pipelines/${pipelineId}`,
      ),
      api.get<ResponseEnvelope<BackendPipelinePhaseResponse[]>>(
        `/api/v1/pipelines/${pipelineId}/phases`,
      ),
    ]);

    return {
      ...pipelineResponse,
      data: normalizePipeline(pipelineResponse.data, phasesResponse.data),
    };
  },

  async create(projectId: string, mode: PipelineMode) {
    const response = await api.post<ResponseEnvelope<BackendPipelineResponse>>(
      `/api/v1/projects/${projectId}/pipelines`,
      { mode },
    );
    return {
      ...response,
      data: normalizePipeline(response.data),
    };
  },

  start(pipelineId: string) {
    return api.post<ResponseEnvelope<PipelineActionResponse>>(
      `/api/v1/pipelines/${pipelineId}/start`,
    );
  },

  pause(pipelineId: string) {
    return api.post<ResponseEnvelope<PipelineActionResponse>>(
      `/api/v1/pipelines/${pipelineId}/pause`,
    );
  },

  resume(pipelineId: string) {
    return api.post<ResponseEnvelope<PipelineActionResponse>>(
      `/api/v1/pipelines/${pipelineId}/resume`,
    );
  },

  cancel(pipelineId: string) {
    return api.post<ResponseEnvelope<PipelineActionResponse>>(
      `/api/v1/pipelines/${pipelineId}/cancel`,
    );
  },

  approvePhase(
    pipelineId: string,
    phaseId: string,
    payload: PhaseApprovalPayload,
  ) {
    return api.post<ResponseEnvelope<BackendPipelinePhaseResponse>>(
      `/api/v1/pipelines/${pipelineId}/phases/${phaseId}/approve`,
      payload,
    );
  },
};
