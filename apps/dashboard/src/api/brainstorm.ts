import { api } from "./client";

interface ResponseEnvelope<T> {
  status: "success";
  data: T;
  meta: { request_id: string; timestamp: string };
}

export interface BrainstormQuestion {
  id: string;
  category: string;
  prompt: string;
  required: boolean;
  priority: string;
  answer: string | null;
  status: string;
}

export interface BrainstormMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  created_at: string;
}

export interface BrainstormSummary {
  readiness_score: number;
  ready_for_pipeline: boolean;
  blockers: string[];
  recommended_preset: string;
  recommended_next_step: string;
  open_questions: number;
  answered_questions: number;
  required_questions_remaining: number;
}

export interface BrainstormSession {
  session_id: string;
  project_id: string;
  status: string;
  started_at: string;
  updated_at: string;
  overview: string;
  refined_brief: string;
  questions: BrainstormQuestion[];
  messages: BrainstormMessage[];
  summary: BrainstormSummary;
  source_context: Record<string, unknown> | null;
  agent_output: Record<string, unknown> | null;
}

export const brainstormApi = {
  start(projectId: string) {
    return api.post<ResponseEnvelope<BrainstormSession>>(
      `/api/v1/projects/${projectId}/brainstorm/start`,
    );
  },

  respond(projectId: string, body: { content: string; question_id?: string }) {
    return api.post<ResponseEnvelope<BrainstormSession>>(
      `/api/v1/projects/${projectId}/brainstorm/respond`,
      body,
    );
  },

  finalize(projectId: string) {
    return api.post<ResponseEnvelope<BrainstormSession>>(
      `/api/v1/projects/${projectId}/brainstorm/finalize`,
    );
  },
};