import type {
  ResponseEnvelope,
  PaginatedEnvelope,
  ProjectResponse,
  PipelineResponse,
  AgentResponse,
} from "../types.js";

export class CodeBotAPIError extends Error {
  public readonly statusCode: number;

  constructor(statusCode: number, message: string) {
    super(message);
    this.name = "CodeBotAPIError";
    this.statusCode = statusCode;
  }
}

export class CodeBotClient {
  private baseUrl: string;
  private token: string | null;

  constructor(baseUrl: string, token: string | null = null) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.token = token;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const init: RequestInit = { method, headers };
    if (body !== undefined) {
      init.body = JSON.stringify(body);
    }

    const res = await fetch(`${this.baseUrl}${path}`, init);

    if (!res.ok) {
      const errBody = (await res
        .json()
        .catch(() => ({ error: { message: res.statusText } }))) as {
        error?: { message?: string };
      };
      throw new CodeBotAPIError(
        res.status,
        errBody?.error?.message ?? `HTTP ${res.status}`,
      );
    }

    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  }

  async login(
    email: string,
    password: string,
  ): Promise<{ access_token: string }> {
    const result = await this.request<
      ResponseEnvelope<{ access_token: string }>
    >("POST", "/api/v1/auth/login", { email, password });
    return result.data;
  }

  async createProject(
    name: string,
    description: string,
    prdContent?: string,
  ): Promise<ProjectResponse> {
    const result = await this.request<ResponseEnvelope<ProjectResponse>>(
      "POST",
      "/api/v1/projects",
      { name, description, prd_content: prdContent },
    );
    return result.data;
  }

  async listProjects(
    page = 1,
    perPage = 20,
  ): Promise<PaginatedEnvelope<ProjectResponse>> {
    return this.request<PaginatedEnvelope<ProjectResponse>>(
      "GET",
      `/api/v1/projects?page=${page}&per_page=${perPage}`,
    );
  }

  async deleteProject(projectId: string): Promise<void> {
    await this.request<void>("DELETE", `/api/v1/projects/${projectId}`);
  }

  async createPipeline(
    projectId: string,
    mode: string,
  ): Promise<PipelineResponse> {
    const result = await this.request<ResponseEnvelope<PipelineResponse>>(
      "POST",
      `/api/v1/projects/${projectId}/pipelines`,
      { mode },
    );
    return result.data;
  }

  async startPipeline(pipelineId: string): Promise<PipelineResponse> {
    const result = await this.request<ResponseEnvelope<PipelineResponse>>(
      "POST",
      `/api/v1/pipelines/${pipelineId}/start`,
    );
    return result.data;
  }

  async pausePipeline(pipelineId: string): Promise<PipelineResponse> {
    const result = await this.request<ResponseEnvelope<PipelineResponse>>(
      "POST",
      `/api/v1/pipelines/${pipelineId}/pause`,
    );
    return result.data;
  }

  async resumePipeline(pipelineId: string): Promise<PipelineResponse> {
    const result = await this.request<ResponseEnvelope<PipelineResponse>>(
      "POST",
      `/api/v1/pipelines/${pipelineId}/resume`,
    );
    return result.data;
  }

  async stopPipeline(pipelineId: string): Promise<PipelineResponse> {
    const result = await this.request<ResponseEnvelope<PipelineResponse>>(
      "POST",
      `/api/v1/pipelines/${pipelineId}/stop`,
    );
    return result.data;
  }

  async listAgents(
    pipelineId: string,
  ): Promise<PaginatedEnvelope<AgentResponse>> {
    return this.request<PaginatedEnvelope<AgentResponse>>(
      "GET",
      `/api/v1/agents?pipeline_id=${pipelineId}`,
    );
  }
}
