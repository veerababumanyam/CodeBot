export type ProjectStatus =
  | "created"
  | "brainstorming"
  | "planning"
  | "in_progress"
  | "review"
  | "completed"
  | "failed"
  | "paused"
  | "cancelled";

export interface Project {
  id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  project_type: string;
  prd_format: string;
  tech_stack: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}
