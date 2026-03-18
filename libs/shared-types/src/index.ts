/**
 * Barrel export for all @codebot/shared-types.
 * Import enums directly (not as types) so they are available as values.
 * Import interfaces with `export type` per verbatimModuleSyntax requirements.
 */

// Enums (value exports)
export {
  AgentStatus,
  AgentType,
  CommentStatus,
  CommentType,
  EventType,
  ExecutionStatus,
  ExperimentStatus,
  FindingStatus,
  FindingType,
  PhaseStatus,
  PhaseType,
  PipelineStatus,
  ProjectStatus,
  ProjectType,
  Severity,
  TaskStatus,
  TestStatus,
} from "./enums.js";

// Interfaces (type-only exports)
export type { Agent, AgentExecution } from "./agent.js";
export type { AgentEvent, EventEnvelope, PipelineEvent, TaskEvent } from "./events.js";
export type { Pipeline, PipelinePhase, Project } from "./project.js";
export type { Task } from "./task.js";
