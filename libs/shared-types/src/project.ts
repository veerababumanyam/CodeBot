/**
 * TypeScript interfaces for Project, Pipeline, and PipelinePhase.
 * Field names and types mirror the Python Pydantic schemas exactly.
 * UUIDs use string, datetimes use ISO 8601 string.
 */

import type { PhaseStatus, PhaseType, PipelineStatus, ProjectStatus, ProjectType } from "./enums.js";

export interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  project_type: ProjectType;
  tech_stack: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Pipeline {
  id: string;
  project_id: string;
  status: PipelineStatus;
  current_phase: string;
  total_tokens_used: number;
  total_cost_usd: number;
  started_at: string;
  completed_at: string | null;
}

export interface PipelinePhase {
  id: string;
  pipeline_id: string;
  name: string;
  phase_type: PhaseType;
  status: PhaseStatus;
  order: number;
  requires_approval: boolean;
  started_at: string | null;
  completed_at: string | null;
}
