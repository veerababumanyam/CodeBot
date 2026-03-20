export type PipelineStatus =
  | "pending"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export type StageStatus =
  | "idle"
  | "running"
  | "completed"
  | "failed"
  | "skipped"
  | "waiting";

export type PipelineMode = "full" | "quick" | "review_only";

export interface PipelineStage {
  id: string;
  name: string;
  stage_number: number;
  status: StageStatus;
  started_at: string | null;
  completed_at: string | null;
  agents: string[];
  phase_type?: string;
  requires_approval?: boolean;
  approved_by?: string | null;
  error_message?: string | null;
}

export interface Pipeline {
  id: string;
  project_id: string;
  mode: PipelineMode;
  status: PipelineStatus;
  current_phase: string;
  total_stages: number;
  stages: PipelineStage[];
  config: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  total_tokens_used: number;
  total_cost_usd: number;
  error_message?: string | null;
}

export interface StageStartEvent {
  pipeline_id: string;
  stage_id: string;
  stage_number: number;
  name: string;
}

export interface StageCompleteEvent {
  pipeline_id: string;
  stage_id: string;
  stage_number: number;
  name: string;
  duration_ms: number;
}

export interface StageErrorEvent {
  pipeline_id: string;
  stage_id: string;
  stage_number: number;
  error: string;
}

export interface GateEvent {
  pipeline_id: string;
  stage_id: string;
  gate_type: string;
}
