/**
 * TypeScript interface for Task.
 * Field names and types mirror the Python Pydantic schema exactly.
 */

import type { TaskStatus } from "./enums.js";

export interface Task {
  id: string;
  project_id: string;
  phase_id: string;
  parent_task_id: string | null;
  title: string;
  description: string;
  status: TaskStatus;
  priority: number;
  assigned_agent_type: string;
  dependencies: string[];
  input_context: Record<string, unknown>;
  output_artifacts: Record<string, unknown> | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}
