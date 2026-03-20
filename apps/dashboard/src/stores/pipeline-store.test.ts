import { describe, it, expect, beforeEach } from "vitest";
import { usePipelineStore } from "./pipeline-store";
import type { Pipeline } from "@/types/pipeline";

function makePipeline(overrides: Partial<Pipeline> = {}): Pipeline {
  return {
    id: "p-1",
    project_id: "proj-1",
    mode: "full",
    status: "pending",
    current_phase: "",
    total_stages: 11,
    stages: [],
    config: null,
    started_at: null,
    completed_at: null,
    total_tokens_used: 0,
    total_cost_usd: 0,
    ...overrides,
  };
}

describe("usePipelineStore", () => {
  beforeEach(() => {
    usePipelineStore.getState().reset();
  });

  it("setPipelines normalizes list into Record keyed by id", () => {
    const p1 = makePipeline({ id: "p-1" });
    const p2 = makePipeline({ id: "p-2" });

    usePipelineStore.getState().setPipelines([p1, p2]);

    const state = usePipelineStore.getState();
    expect(Object.keys(state.pipelines)).toHaveLength(2);
    expect(state.pipelines["p-1"]?.id).toBe("p-1");
    expect(state.pipelines["p-2"]?.id).toBe("p-2");
  });

  it("upsertPipeline adds new pipeline and updates existing", () => {
    const p1 = makePipeline({ id: "p-1", status: "pending" });
    usePipelineStore.getState().upsertPipeline(p1);

    expect(usePipelineStore.getState().pipelines["p-1"]?.status).toBe(
      "pending",
    );

    const p1Updated = makePipeline({ id: "p-1", status: "running" });
    usePipelineStore.getState().upsertPipeline(p1Updated);

    expect(usePipelineStore.getState().pipelines["p-1"]?.status).toBe(
      "running",
    );
  });

  it("updateStageStatus changes a stage's status within a pipeline", () => {
    const pipeline = makePipeline({
      id: "p-1",
      stages: [
        {
          id: "s-0",
          name: "Init",
          stage_number: 0,
          status: "idle",
          started_at: null,
          completed_at: null,
          agents: [],
        },
        {
          id: "s-1",
          name: "Brainstorm",
          stage_number: 1,
          status: "idle",
          started_at: null,
          completed_at: null,
          agents: [],
        },
      ],
    });

    usePipelineStore.getState().setPipelines([pipeline]);
    usePipelineStore.getState().updateStageStatus("p-1", "s-0", "running");

    const updated = usePipelineStore.getState().pipelines["p-1"];
    expect(updated?.stages[0]?.status).toBe("running");
    expect(updated?.stages[1]?.status).toBe("idle");
  });

  it("applyStageEvent updates pipeline phase, status, and stage error details", () => {
    const pipeline = makePipeline({
      id: "p-1",
      status: "pending",
      current_phase: "",
      stages: [
        {
          id: "s-0",
          name: "Init",
          stage_number: 0,
          status: "idle",
          started_at: null,
          completed_at: null,
          agents: [],
          error_message: null,
        },
        {
          id: "s-1",
          name: "Test",
          stage_number: 1,
          status: "idle",
          started_at: null,
          completed_at: null,
          agents: [],
          error_message: null,
        },
      ],
    });

    usePipelineStore.getState().setPipelines([pipeline]);

    usePipelineStore.getState().applyStageEvent({
      pipelineId: "p-1",
      stageId: "s-0",
      status: "running",
      stageName: "Initialization",
      errorMessage: null,
    });

    let updated = usePipelineStore.getState().pipelines["p-1"];
    expect(updated?.status).toBe("running");
    expect(updated?.current_phase).toBe("Initialization");
    expect(updated?.error_message).toBeNull();
    expect(updated?.stages[0]?.name).toBe("Initialization");

    usePipelineStore.getState().applyStageEvent({
      pipelineId: "p-1",
      stageId: "s-1",
      status: "failed",
      errorMessage: "Suite timed out",
    });

    updated = usePipelineStore.getState().pipelines["p-1"];
    expect(updated?.status).toBe("failed");
    expect(updated?.current_phase).toBe("Test");
    expect(updated?.error_message).toBe("Suite timed out");
    expect(updated?.stages[1]?.error_message).toBe("Suite timed out");
  });

  it("marks the pipeline completed when the final stage completes", () => {
    const pipeline = makePipeline({
      id: "p-1",
      status: "running",
      current_phase: "Implementation",
      stages: [
        {
          id: "s-0",
          name: "Init",
          stage_number: 0,
          status: "completed",
          started_at: null,
          completed_at: null,
          agents: [],
        },
        {
          id: "s-1",
          name: "Review",
          stage_number: 1,
          status: "running",
          started_at: null,
          completed_at: null,
          agents: [],
        },
      ],
    });

    usePipelineStore.getState().setPipelines([pipeline]);

    usePipelineStore.getState().applyStageEvent({
      pipelineId: "p-1",
      stageId: "s-1",
      status: "completed",
      stageName: "Review",
      errorMessage: null,
    });

    const updated = usePipelineStore.getState().pipelines["p-1"];
    expect(updated?.status).toBe("completed");
    expect(updated?.current_phase).toBe("Review");
    expect(updated?.error_message).toBeNull();
  });

  it("applies pipeline-level updates for lifecycle status and usage", () => {
    const pipeline = makePipeline({
      id: "p-1",
      status: "running",
      current_phase: "Implementation",
      started_at: null,
      completed_at: null,
      total_tokens_used: 5,
      total_cost_usd: 0.25,
      error_message: null,
    });

    usePipelineStore.getState().setPipelines([pipeline]);

    usePipelineStore.getState().applyPipelineUpdate({
      pipelineId: "p-1",
      status: "paused",
      currentPhase: "Code review",
      startedAt: "2026-03-20T10:00:00Z",
      completedAt: null,
      totalTokensUsed: 128,
      totalCostUsd: 3.5,
      errorMessage: "Waiting on approval",
    });

    const updated = usePipelineStore.getState().pipelines["p-1"];
    expect(updated?.status).toBe("paused");
    expect(updated?.current_phase).toBe("Code review");
    expect(updated?.started_at).toBe("2026-03-20T10:00:00Z");
    expect(updated?.completed_at).toBeNull();
    expect(updated?.total_tokens_used).toBe(128);
    expect(updated?.total_cost_usd).toBe(3.5);
    expect(updated?.error_message).toBe("Waiting on approval");
  });

  it("reset clears all state back to initial values", () => {
    usePipelineStore
      .getState()
      .setPipelines([makePipeline({ id: "p-1" })]);
    usePipelineStore.getState().setActivePipeline("p-1");
    usePipelineStore.getState().setFocusedStage("s-1");
    usePipelineStore.getState().setLoading(true);
    usePipelineStore.getState().setError("test error");

    usePipelineStore.getState().reset();

    const state = usePipelineStore.getState();
    expect(Object.keys(state.pipelines)).toHaveLength(0);
    expect(state.activePipelineId).toBeNull();
    expect(state.focusedStageId).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it("tracks a focused stage for diagnostics handoff", () => {
    usePipelineStore.getState().setFocusedStage("s-42");

    expect(usePipelineStore.getState().focusedStageId).toBe("s-42");

    usePipelineStore.getState().setFocusedStage(null);

    expect(usePipelineStore.getState().focusedStageId).toBeNull();
  });
});
