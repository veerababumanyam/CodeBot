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
const mockUpdateStageStatus = vi.fn();

vi.mock("@/stores/pipeline-store", () => ({
  usePipelineStore: {
    getState: () => ({
      updateStageStatus: mockUpdateStageStatus,
    }),
  },
}));

// Import after mocks are set up
const { usePipelineEvents } = await import("./use-pipeline-events");

describe("usePipelineEvents", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("subscribes to pipeline events with pipeline_id", () => {
    renderHook(() => usePipelineEvents("test-pipeline-id"));

    expect(mockEmit).toHaveBeenCalledWith("subscribe", {
      pipeline_id: "test-pipeline-id",
    });
  });

  it("registers listeners for stage:start, stage:complete, stage:error", () => {
    renderHook(() => usePipelineEvents("test-pipeline-id"));

    const registeredEvents = mockOn.mock.calls.map(
      (call: unknown[]) => call[0],
    );
    expect(registeredEvents).toContain("stage:start");
    expect(registeredEvents).toContain("stage:complete");
    expect(registeredEvents).toContain("stage:error");
  });

  it("calls updateStageStatus when stage:start event fires", () => {
    renderHook(() => usePipelineEvents("test-pipeline-id"));

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

    expect(mockUpdateStageStatus).toHaveBeenCalledWith("p-1", "s-0", "running");
  });

  it("unsubscribes and removes listeners on unmount", () => {
    const { unmount } = renderHook(() =>
      usePipelineEvents("test-pipeline-id"),
    );

    unmount();

    expect(mockEmit).toHaveBeenCalledWith("unsubscribe", {
      pipeline_id: "test-pipeline-id",
    });

    const removedEvents = mockOff.mock.calls.map(
      (call: unknown[]) => call[0],
    );
    expect(removedEvents).toContain("stage:start");
    expect(removedEvents).toContain("stage:complete");
    expect(removedEvents).toContain("stage:error");
  });

  it("does nothing when pipelineId is null", () => {
    renderHook(() => usePipelineEvents(null));

    expect(mockEmit).not.toHaveBeenCalled();
    expect(mockOn).not.toHaveBeenCalled();
  });
});
