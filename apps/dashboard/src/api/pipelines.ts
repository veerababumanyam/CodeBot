import { api } from "./client";
import type { Pipeline } from "@/types/pipeline";

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

export const pipelineApi = {
  list(projectId: string) {
    return api.get<PaginatedEnvelope<Pipeline>>(
      `/api/v1/projects/${projectId}/pipelines`,
    );
  },

  get(projectId: string, pipelineId: string) {
    return api.get<ResponseEnvelope<Pipeline>>(
      `/api/v1/projects/${projectId}/pipelines/${pipelineId}`,
    );
  },

  create(projectId: string, mode: Pipeline["mode"]) {
    return api.post<ResponseEnvelope<Pipeline>>(
      `/api/v1/projects/${projectId}/pipelines`,
      { mode },
    );
  },

  start(pipelineId: string) {
    return api.post<ResponseEnvelope<Pipeline>>(
      `/api/v1/pipelines/${pipelineId}/start`,
    );
  },

  pause(pipelineId: string) {
    return api.post<ResponseEnvelope<Pipeline>>(
      `/api/v1/pipelines/${pipelineId}/pause`,
    );
  },

  resume(pipelineId: string) {
    return api.post<ResponseEnvelope<Pipeline>>(
      `/api/v1/pipelines/${pipelineId}/resume`,
    );
  },

  stop(pipelineId: string) {
    return api.post<ResponseEnvelope<Pipeline>>(
      `/api/v1/pipelines/${pipelineId}/stop`,
    );
  },
};
