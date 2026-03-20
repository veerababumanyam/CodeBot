import { api } from "./client";
import type { Project } from "@/types/project";

export interface ProjectCreatePayload {
  name: string;
  description: string;
  prd_source: "text" | "file" | "url";
  prd_content?: string;
  prd_url?: string;
  prd_file?: string;
  source_name?: string;
  source_media_type?: string;
  project_type?: "greenfield" | "inflight" | "brownfield" | "improve";
  repository_path?: string;
  repository_url?: string;
  tech_stack?: Record<string, unknown>;
  settings?: Record<string, unknown>;
}

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

export const projectApi = {
  list(page = 1, perPage = 20) {
    return api.get<PaginatedEnvelope<Project>>(
      `/api/v1/projects?page=${String(page)}&per_page=${String(perPage)}`,
    );
  },

  get(projectId: string) {
    return api.get<ResponseEnvelope<Project>>(
      `/api/v1/projects/${projectId}`,
    );
  },

  create(data: ProjectCreatePayload) {
    return api.post<ResponseEnvelope<Project>>("/api/v1/projects", data);
  },

  update(projectId: string, data: Partial<Pick<Project, "name" | "description">>) {
    return api.patch<ResponseEnvelope<Project>>(
      `/api/v1/projects/${projectId}`,
      data,
    );
  },

  delete(projectId: string) {
    return api.delete<void>(`/api/v1/projects/${projectId}`);
  },
};
