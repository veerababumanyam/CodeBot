import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";

const mockOn = vi.fn();
const mockOff = vi.fn();
const mockEmit = vi.fn();

vi.mock("@/lib/socket", () => ({
  agentSocket: {
    on: mockOn,
    off: mockOff,
    emit: mockEmit,
  },
}));

const mockUpdateAgentStatus = vi.fn();
const mockAppendLog = vi.fn();
const mockUpdateAgentMetrics = vi.fn();

vi.mock("@/stores/agent-store", () => ({
  useAgentStore: {
    getState: () => ({
      updateAgentStatus: mockUpdateAgentStatus,
      appendLog: mockAppendLog,
      updateAgentMetrics: mockUpdateAgentMetrics,
    }),
  },
}));

const { useAgentStatus } = await import("./use-agent-status");

describe("useAgentStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("subscribes to the project room for agent events", () => {
    renderHook(() => useAgentStatus("pipe-1", "proj-1"));

    expect(mockEmit).toHaveBeenCalledWith("subscribe", {
      channels: ["project:proj-1"],
    });
  });

  it("registers agent event listeners", () => {
    renderHook(() => useAgentStatus("pipe-1", "proj-1"));

    const events = mockOn.mock.calls.map((call: unknown[]) => call[0]);
    expect(events).toContain("agent:status");
    expect(events).toContain("agent:log");
    expect(events).toContain("agent:metrics");
  });

  it("updates the store from agent events", () => {
    renderHook(() => useAgentStatus("pipe-1", "proj-1"));

    const statusHandler = mockOn.mock.calls.find(
      (call: unknown[]) => call[0] === "agent:status",
    )?.[1] as ((event: { agent_id: string; status: string }) => void) | undefined;
    const logHandler = mockOn.mock.calls.find(
      (call: unknown[]) => call[0] === "agent:log",
    )?.[1] as ((event: { agent_id: string; message: string }) => void) | undefined;
    const metricsHandler = mockOn.mock.calls.find(
      (call: unknown[]) => call[0] === "agent:metrics",
    )?.[1] as ((event: { agent_id: string; tokens_used: number; cost_usd: number }) => void) | undefined;

    statusHandler?.({ agent_id: "agent-1", status: "running" });
    logHandler?.({ agent_id: "agent-1", message: "hello" });
    metricsHandler?.({ agent_id: "agent-1", tokens_used: 100, cost_usd: 0.25 });

    expect(mockUpdateAgentStatus).toHaveBeenCalledWith("agent-1", "running");
    expect(mockAppendLog).toHaveBeenCalledWith(
      "agent-1",
      expect.objectContaining({ message: "hello" }),
    );
    expect(mockUpdateAgentMetrics).toHaveBeenCalledWith("agent-1", {
      tokens_used: 100,
      cost_usd: 0.25,
    });
  });

  it("unsubscribes from the project room on cleanup", () => {
    const { unmount } = renderHook(() => useAgentStatus("pipe-1", "proj-1"));

    unmount();

    expect(mockEmit).toHaveBeenCalledWith("unsubscribe", {
      channels: ["project:proj-1"],
    });
  });
});