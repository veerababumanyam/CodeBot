/**
 * TypeScript interfaces for Agent and AgentExecution.
 * Field names and types mirror the Python Pydantic schemas exactly.
 */

import type { AgentStatus, AgentType, ExecutionStatus } from "./enums.js";

export interface Agent {
  id: string;
  project_id: string;
  agent_type: AgentType;
  status: AgentStatus;
  llm_provider: string;
  llm_model: string;
  worktree_path: string | null;
  cli_agent_type: string | null;
  system_prompt_hash: string;
  tokens_used: number;
  cost_usd: number;
  started_at: string;
  completed_at: string | null;
  error_count: number;
}

export interface AgentExecution {
  id: string;
  agent_id: string;
  task_id: string;
  llm_provider: string;
  llm_model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: number;
  duration_ms: number;
  status: ExecutionStatus;
  input_messages: Record<string, unknown>[];
  output_messages: Record<string, unknown>[];
  tool_calls: Record<string, unknown>[];
  error_message: string | null;
  created_at: string;
}
