import { api } from "./client";
import type { Project } from "@/types/project";

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

  create(data: { name: string; description: string; project_type: string; prd_format: string }) {
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
