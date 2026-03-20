import type { PipelineMode } from "@/types/pipeline";

export interface ExecutionPlanStep {
  key: string;
  label: string;
  description: string;
}

const EXECUTION_PLAN_STEPS: Record<PipelineMode, ExecutionPlanStep[]> = {
  full: [
    {
      key: "initialize",
      label: "Initialize",
      description: "Set up project context, scaffolding, and orchestration state.",
    },
    {
      key: "brainstorm",
      label: "Brainstorm",
      description: "Run deeper solution exploration and requirement framing inside the pipeline.",
    },
    {
      key: "research",
      label: "Research",
      description: "Collect references, prior art, and implementation constraints.",
    },
    {
      key: "design",
      label: "Design",
      description: "Produce architecture and design outputs, with human review where needed.",
    },
    {
      key: "plan",
      label: "Plan",
      description: "Translate the brief into concrete execution tasks and configuration.",
    },
    {
      key: "implement",
      label: "Implement",
      description: "Build the product slice across frontend, backend, and middleware.",
    },
    {
      key: "qa",
      label: "Quality assurance",
      description: "Run code review and security checks.",
    },
    {
      key: "test",
      label: "Test",
      description: "Validate functionality and regressions through automated tests.",
    },
    {
      key: "fix",
      label: "Stabilize",
      description: "Loop through debugging until the delivery bar is met.",
    },
    {
      key: "document",
      label: "Document",
      description: "Write supporting docs and knowledge artifacts.",
    },
    {
      key: "deliver",
      label: "Deliver",
      description: "Prepare deployment and delivery handoff with approval gates.",
    },
  ],
  quick: [
    {
      key: "initialize",
      label: "Initialize",
      description: "Set up the project context and execution scaffolding.",
    },
    {
      key: "design",
      label: "Design",
      description: "Generate architecture and design outputs with fast review loops.",
    },
    {
      key: "plan",
      label: "Plan",
      description: "Translate the clarified brief into build tasks.",
    },
    {
      key: "implement",
      label: "Implement",
      description: "Build the core product slice quickly across the main surfaces.",
    },
    {
      key: "qa",
      label: "Quality assurance",
      description: "Run review and security checks.",
    },
    {
      key: "test",
      label: "Test",
      description: "Verify the implementation with automated tests.",
    },
    {
      key: "fix",
      label: "Stabilize",
      description: "Repair failing paths before handoff.",
    },
    {
      key: "deliver",
      label: "Deliver",
      description: "Prepare the output for deployment or handoff.",
    },
  ],
  review_only: [
    {
      key: "qa",
      label: "Quality assurance",
      description: "Run review and security analysis only, without a full build pipeline.",
    },
  ],
};

function normalizeMode(mode: string): PipelineMode {
  const normalized = mode.replace(/-/g, "_");
  if (normalized === "quick" || normalized === "review_only") {
    return normalized;
  }
  return "full";
}

export function getExecutionPlan(mode: string): ExecutionPlanStep[] {
  return EXECUTION_PLAN_STEPS[normalizeMode(mode)];
}

export function getExecutionPlanLabel(mode: string): string {
  const normalized = normalizeMode(mode);
  if (normalized === "review_only") {
    return "Review only";
  }
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}