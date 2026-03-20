import { api } from "./client";
import type { Agent } from "@/types/agent";

interface Envelope<T> {
  status: string;
  data: T;
}

interface PaginatedEnvelope<T> {
  status: string;
  data: T[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  } | null;
}

export const agentApi = {
  list: (pipelineId: string) =>
    api.get<PaginatedEnvelope<Agent>>(
      `/api/v1/agents?pipeline_id=${pipelineId}`,
    ),

  get: (agentId: string) =>
    api.get<Envelope<Agent>>(`/api/v1/agents/${agentId}`),

  start: (agentId: string) =>
    api.post<Envelope<Agent>>(`/api/v1/agents/${agentId}/start`),

  stop: (agentId: string) =>
    api.post<Envelope<Agent>>(`/api/v1/agents/${agentId}/stop`),

  restart: (agentId: string) =>
    api.post<Envelope<Agent>>(`/api/v1/agents/${agentId}/restart`),
};
