export type AgentStatus =
  | "idle"
  | "initializing"
  | "executing"
  | "reviewing"
  | "completed"
  | "failed"
  | "recovering"
  | "terminated";

export interface Agent {
  id: string;
  name: string;
  agent_type: string;
  pipeline_id: string;
  stage_number: number;
  status: AgentStatus;
  model: string | null;
  tokens_used: number;
  cost_usd: number;
  started_at: string | null;
  completed_at: string | null;
}

export interface AgentStatusEvent {
  agent_id: string;
  pipeline_id: string;
  status: AgentStatus;
  timestamp: string;
}

export interface AgentLogEvent {
  agent_id: string;
  pipeline_id: string;
  level: "info" | "warn" | "error" | "debug";
  message: string;
  timestamp: string;
}

export interface AgentMetricsEvent {
  agent_id: string;
  pipeline_id: string;
  tokens_used: number;
  cost_usd: number;
  execution_time_ms: number;
}
