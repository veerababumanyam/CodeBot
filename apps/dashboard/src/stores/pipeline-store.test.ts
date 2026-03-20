import { describe, it, expect, beforeEach } from "vitest";
import { usePipelineStore } from "./pipeline-store";
import type { Pipeline } from "@/types/pipeline";

function makePipeline(overrides: Partial<Pipeline> = {}): Pipeline {
  return {
    id: "p-1",
    project_id: "proj-1",
    mode: "full",
    status: "pending",
    current_stage: 0,
    total_stages: 11,
    stages: [],
    config: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
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

  it("reset clears all state back to initial values", () => {
    usePipelineStore
      .getState()
      .setPipelines([makePipeline({ id: "p-1" })]);
    usePipelineStore.getState().setActivePipeline("p-1");
    usePipelineStore.getState().setLoading(true);
    usePipelineStore.getState().setError("test error");

    usePipelineStore.getState().reset();

    const state = usePipelineStore.getState();
    expect(Object.keys(state.pipelines)).toHaveLength(0);
    expect(state.activePipelineId).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });
});
