import { describe, it, expect, beforeEach } from "vitest";
import { useAgentStore } from "./agent-store";
import type { Agent, AgentLogEvent } from "@/types/agent";

function makeAgent(overrides: Partial<Agent> = {}): Agent {
  return {
    id: "a-1",
    name: "TestAgent",
    agent_type: "backend_dev",
    pipeline_id: "p-1",
    stage_number: 5,
    status: "idle",
    model: null,
    tokens_used: 0,
    cost_usd: 0,
    started_at: null,
    completed_at: null,
    ...overrides,
  };
}

function makeLog(overrides: Partial<AgentLogEvent> = {}): AgentLogEvent {
  return {
    agent_id: "a-1",
    pipeline_id: "p-1",
    level: "info",
    message: "test log message",
    timestamp: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("useAgentStore", () => {
  beforeEach(() => {
    useAgentStore.getState().reset();
  });

  it("upsertAgent adds agent to store", () => {
    const agent = makeAgent({ id: "a-1" });
    useAgentStore.getState().upsertAgent(agent);

    expect(useAgentStore.getState().agents["a-1"]?.name).toBe("TestAgent");
  });

  it("appendLog adds log entries and caps at 500 per agent", () => {
    const agent = makeAgent({ id: "a-1" });
    useAgentStore.getState().upsertAgent(agent);

    // Append 501 logs
    for (let i = 0; i < 501; i++) {
      useAgentStore
        .getState()
        .appendLog("a-1", makeLog({ message: `log-${String(i)}` }));
    }

    const logs = useAgentStore.getState().logs["a-1"];
    expect(logs).toHaveLength(500);
    // Oldest log (log-0) should be dropped; newest (log-500) should be present
    expect(logs?.[logs.length - 1]?.message).toBe("log-500");
  });

  it("updateAgentStatus changes agent's status field", () => {
    useAgentStore.getState().upsertAgent(makeAgent({ id: "a-1" }));
    useAgentStore.getState().updateAgentStatus("a-1", "executing");

    expect(useAgentStore.getState().agents["a-1"]?.status).toBe("executing");
  });

  it("updateAgentMetrics merges tokens_used and cost_usd into agent", () => {
    useAgentStore.getState().upsertAgent(makeAgent({ id: "a-1" }));
    useAgentStore
      .getState()
      .updateAgentMetrics("a-1", { tokens_used: 5000, cost_usd: 0.15 });

    const agent = useAgentStore.getState().agents["a-1"];
    expect(agent?.tokens_used).toBe(5000);
    expect(agent?.cost_usd).toBe(0.15);
  });
});
