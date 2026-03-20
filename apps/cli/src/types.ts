export interface ResponseEnvelope<T> {
  status: "success";
  data: T;
  meta: { request_id: string; timestamp: string };
}

export interface PaginatedEnvelope<T> {
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

export interface ErrorResponse {
  status: "error";
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>[];
  };
}

export interface ProjectResponse {
  id: string;
  name: string;
  description: string;
  status: string;
  project_type: string;
  created_at: string;
  updated_at: string;
}

export interface PipelineResponse {
  id: string;
  project_id: string;
  mode: "full" | "quick" | "review_only";
  status: string;
  current_stage: number;
  total_stages: number;
  created_at: string;
  updated_at: string;
}

export interface AgentResponse {
  id: string;
  name: string;
  agent_type: string;
  pipeline_id: string;
  stage_number: number;
  status: string;
  model: string | null;
  tokens_used: number;
  cost_usd: number;
  started_at: string | null;
  completed_at: string | null;
}

export interface AgentLogEvent {
  agent_id: string;
  pipeline_id: string;
  level: "info" | "warn" | "error" | "debug";
  message: string;
  timestamp: string;
}

export interface CLIConfig {
  server_url: string;
  preset: string;
  token?: string | undefined;
}
