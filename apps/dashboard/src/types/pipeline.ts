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

export interface PipelineStage {
  id: string;
  name: string;
  stage_number: number;
  status: StageStatus;
  started_at: string | null;
  completed_at: string | null;
  agents: string[];
}

export interface Pipeline {
  id: string;
  project_id: string;
  mode: "full" | "quick" | "review_only";
  status: PipelineStatus;
  current_stage: number;
  total_stages: number;
  stages: PipelineStage[];
  config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
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
