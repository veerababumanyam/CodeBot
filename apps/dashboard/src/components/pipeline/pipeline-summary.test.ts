import { describe, expect, it } from "vitest";
import {
  formatPipelineMode,
  formatStageLabel,
  getPipelineProgressSummary,
  getStageTone,
} from "./pipeline-summary";
import type { Pipeline } from "@/types/pipeline";

function makePipeline(overrides: Partial<Pipeline> = {}): Pipeline {
  return {
    id: "pipe-1",
    project_id: "proj-1",
    mode: "quick",
    status: "running",
    current_phase: "implement",
    total_stages: 3,
    stages: [
      {
        id: "stage-1",
        name: "plan",
        stage_number: 0,
        status: "completed",
        started_at: null,
        completed_at: null,
        agents: [],
      },
      {
        id: "stage-2",
        name: "implement",
        stage_number: 1,
        status: "running",
        started_at: null,
        completed_at: null,
        agents: [],
      },
      {
        id: "stage-3",
        name: "test",
        stage_number: 2,
        status: "waiting",
        started_at: null,
        completed_at: null,
        agents: [],
        requires_approval: true,
      },
    ],
    config: null,
    started_at: null,
    completed_at: null,
    total_tokens_used: 42,
    total_cost_usd: 1.5,
    ...overrides,
  };
}

describe("pipeline summary helpers", () => {
  it("computes progress and active stage", () => {
    const summary = getPipelineProgressSummary(makePipeline());

    expect(summary.completedStages).toBe(1);
    expect(summary.totalStages).toBe(3);
    expect(summary.percentComplete).toBe(33);
    expect(summary.activeStage?.name).toBe("implement");
    expect(summary.waitingStages).toBe(1);
    expect(summary.failedStages).toBe(0);
  });

  it("formats labels for display", () => {
    expect(formatPipelineMode("review_only")).toBe("Review only");
    expect(formatStageLabel("debug_fix")).toBe("Debug Fix");
  });

  it("returns the correct visual tone for waiting stages", () => {
    const tone = getStageTone("waiting");
    expect(tone.label).toBe("Waiting");
    expect(tone.container).toContain("amber");
  });
});
