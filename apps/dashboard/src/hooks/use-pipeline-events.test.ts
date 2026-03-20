import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook } from "@testing-library/react";

// Mock the socket module
const mockOn = vi.fn();
const mockOff = vi.fn();
const mockEmit = vi.fn();

vi.mock("@/lib/socket", () => ({
  pipelineSocket: {
    on: mockOn,
    off: mockOff,
    emit: mockEmit,
  },
}));

// Mock the pipeline store
const mockApplyPipelineUpdate = vi.fn();
const mockApplyStageEvent = vi.fn();
let mockPipelines: Record<string, unknown> = {};

vi.mock("@/stores/pipeline-store", () => ({
  usePipelineStore: {
    getState: () => ({
      applyPipelineUpdate: mockApplyPipelineUpdate,
      applyStageEvent: mockApplyStageEvent,
      pipelines: mockPipelines,
    }),
  },
}));

// Import after mocks are set up
const { usePipelineEvents } = await import("./use-pipeline-events");

describe("usePipelineEvents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPipelines = {};
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("subscribes to pipeline events with pipeline_id", () => {
    renderHook(() => usePipelineEvents("test-pipeline-id", "proj-1"));

    expect(mockEmit).toHaveBeenCalledWith("subscribe", {
      channels: ["project:proj-1"],
    });
  });

  it("registers listeners for phase, stage, and pipeline update events", () => {
    renderHook(() => usePipelineEvents("test-pipeline-id", "proj-1"));

    const registeredEvents = mockOn.mock.calls.map(
      (call: unknown[]) => call[0],
    );
    expect(registeredEvents).toContain("phase.started");
    expect(registeredEvents).toContain("phase.completed");
    expect(registeredEvents).toContain("stage:start");
    expect(registeredEvents).toContain("stage:complete");
    expect(registeredEvents).toContain("stage:error");
    expect(registeredEvents).toContain("pipeline:update");
  });

  it("maps workflow phase.started events onto the active pipeline stage", () => {
    mockPipelines = {
      "test-pipeline-id": {
        id: "test-pipeline-id",
        project_id: "proj-1",
        mode: "full",
        status: "pending",
        current_phase: "",
        total_stages: 2,
        stages: [
          {
            id: "stage-1",
            name: "planning",
            stage_number: 0,
            status: "idle",
            started_at: null,
            completed_at: null,
            agents: [],
          },
        ],
        config: null,
        started_at: null,
        completed_at: null,
        total_tokens_used: 0,
        total_cost_usd: 0,
        error_message: null,
      },
    };

    renderHook(() => usePipelineEvents("test-pipeline-id", "proj-1"));

    const phaseStartCall = mockOn.mock.calls.find(
      (call: unknown[]) => call[0] === "phase.started",
    ) as unknown[] | undefined;
    expect(phaseStartCall).toBeDefined();
    if (!phaseStartCall) throw new Error("phaseStartCall not found");

    const callback = phaseStartCall[1] as (event: {
      pipeline_id: string;
      project_id: string;
      phase: string;
      phase_idx: number;
    }) => void;

    callback({
      pipeline_id: "test-pipeline-id",
      project_id: "proj-1",
      phase: "planning",
      phase_idx: 0,
    });

    expect(mockApplyPipelineUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        pipelineId: "test-pipeline-id",
        status: "running",
        currentPhase: "planning",
      }),
    );
    expect(mockApplyStageEvent).toHaveBeenCalledWith({
      pipelineId: "test-pipeline-id",
      stageId: "stage-1",
      status: "running",
      stageName: "planning",
      errorMessage: null,
    });
  });

  it("applies a running stage event when stage:start fires", () => {
    renderHook(() => usePipelineEvents("test-pipeline-id", "proj-1"));

    // Find the stage:start callback
    const stageStartCall = mockOn.mock.calls.find(
      (call: unknown[]) => call[0] === "stage:start",
    ) as unknown[] | undefined;
    expect(stageStartCall).toBeDefined();
    if (!stageStartCall) throw new Error("stageStartCall not found");

    const callback = stageStartCall[1] as (event: {
      pipeline_id: string;
      stage_id: string;
      stage_number: number;
      name: string;
    }) => void;
    callback({
      pipeline_id: "p-1",
      stage_id: "s-0",
      stage_number: 0,
      name: "Init",
    });

    expect(mockApplyStageEvent).toHaveBeenCalledWith({
      pipelineId: "p-1",
      stageId: "s-0",
      status: "running",
      stageName: "Init",
      errorMessage: null,
    });
  });

  it("applies a completed stage event when stage:complete fires", () => {
    renderHook(() => usePipelineEvents("test-pipeline-id", "proj-1"));

    const stageCompleteCall = mockOn.mock.calls.find(
      (call: unknown[]) => call[0] === "stage:complete",
    ) as unknown[] | undefined;
    expect(stageCompleteCall).toBeDefined();
    if (!stageCompleteCall) throw new Error("stageCompleteCall not found");

    const callback = stageCompleteCall[1] as (event: {
      pipeline_id: string;
      stage_id: string;
      stage_number: number;
      name: string;
      duration_ms: number;
    }) => void;
    callback({
      pipeline_id: "p-1",
      stage_id: "s-0",
      stage_number: 0,
      name: "Init",
      duration_ms: 123,
    });

    expect(mockApplyStageEvent).toHaveBeenCalledWith({
      pipelineId: "p-1",
      stageId: "s-0",
      status: "completed",
      stageName: "Init",
      errorMessage: null,
    });
  });

  it("applies a failed stage event when stage:error fires", () => {
    renderHook(() => usePipelineEvents("test-pipeline-id", "proj-1"));

    const stageErrorCall = mockOn.mock.calls.find(
      (call: unknown[]) => call[0] === "stage:error",
    ) as unknown[] | undefined;
    expect(stageErrorCall).toBeDefined();
    if (!stageErrorCall) throw new Error("stageErrorCall not found");

    const callback = stageErrorCall[1] as (event: {
      pipeline_id: string;
      stage_id: string;
      stage_number: number;
      error: string;
    }) => void;
    callback({
      pipeline_id: "p-1",
      stage_id: "s-0",
      stage_number: 0,
      error: "Build failed",
    });

    expect(mockApplyStageEvent).toHaveBeenCalledWith({
      pipelineId: "p-1",
      stageId: "s-0",
      status: "failed",
      errorMessage: "Build failed",
    });
  });

  it("applies a pipeline update when pipeline:update fires", () => {
    renderHook(() => usePipelineEvents("test-pipeline-id", "proj-1"));

    const pipelineUpdateCall = mockOn.mock.calls.find(
      (call: unknown[]) => call[0] === "pipeline:update",
    ) as unknown[] | undefined;
    expect(pipelineUpdateCall).toBeDefined();
    if (!pipelineUpdateCall) throw new Error("pipelineUpdateCall not found");

    const callback = pipelineUpdateCall[1] as (event: {
      pipeline_id: string;
      project_id: string;
      status: "paused";
      current_phase: string;
      started_at: string | null;
      completed_at: string | null;
      total_tokens_used: number;
      total_cost_usd: number;
      error_message: string | null;
    }) => void;

    callback({
      pipeline_id: "p-1",
      project_id: "proj-1",
      status: "paused",
      current_phase: "Code review",
      started_at: "2026-03-20T10:00:00Z",
      completed_at: null,
      total_tokens_used: 128,
      total_cost_usd: 3.5,
      error_message: "Waiting on approval",
    });

    expect(mockApplyPipelineUpdate).toHaveBeenCalledWith({
      pipelineId: "p-1",
      status: "paused",
      currentPhase: "Code review",
      startedAt: "2026-03-20T10:00:00Z",
      completedAt: null,
      totalTokensUsed: 128,
      totalCostUsd: 3.5,
      errorMessage: "Waiting on approval",
    });
  });

  it("unsubscribes and removes listeners on unmount", () => {
    const { unmount } = renderHook(() =>
      usePipelineEvents("test-pipeline-id", "proj-1"),
    );

    unmount();

    expect(mockEmit).toHaveBeenCalledWith("unsubscribe", {
      channels: ["project:proj-1"],
    });

    const removedEvents = mockOff.mock.calls.map(
      (call: unknown[]) => call[0],
    );
    expect(removedEvents).toContain("phase.started");
    expect(removedEvents).toContain("phase.completed");
    expect(removedEvents).toContain("stage:start");
    expect(removedEvents).toContain("stage:complete");
    expect(removedEvents).toContain("stage:error");
    expect(removedEvents).toContain("pipeline:update");
  });

  it("does nothing when pipelineId is null", () => {
    renderHook(() => usePipelineEvents(null, null));

    expect(mockEmit).not.toHaveBeenCalled();
    expect(mockOn).not.toHaveBeenCalled();
  });
});
