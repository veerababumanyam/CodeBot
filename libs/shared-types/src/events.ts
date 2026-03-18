/**
 * TypeScript interfaces for NATS event payloads.
 * Field names and types mirror the Python Pydantic schemas exactly.
 */

import type { AgentStatus, AgentType, EventType, TaskStatus } from "./enums.js";

export interface AgentEvent {
  agent_id: string;
  agent_type: AgentType;
  status: AgentStatus;
  timestamp: string;
  payload: Record<string, unknown> | null;
}

export interface TaskEvent {
  task_id: string;
  agent_id: string;
  status: TaskStatus;
  timestamp: string;
}

export interface PipelineEvent {
  pipeline_id: string;
  phase: string;
  status: string;
  timestamp: string;
}

export interface EventEnvelope {
  event_type: EventType;
  source_agent_id: string | null;
  /** Raw JSON bytes encoded as base64 string when transmitted over HTTP/JSON. */
  payload: string;
  timestamp: string;
}
