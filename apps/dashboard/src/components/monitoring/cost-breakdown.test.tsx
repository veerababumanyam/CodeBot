import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CostBreakdown } from "./cost-breakdown";
import type { Agent } from "@/types/agent";

const mockAgents: Agent[] = [
  {
    id: "a1",
    name: "Agent Alpha",
    agent_type: "BACKEND_DEV",
    pipeline_id: "pipe-1",
    stage_number: 5,
    status: "completed",
    model: "claude-sonnet-4-20250514",
    tokens_used: 10000,
    cost_usd: 0.1,
    started_at: "2026-03-20T10:00:00Z",
    completed_at: "2026-03-20T10:05:00Z",
  },
  {
    id: "a2",
    name: "Agent Beta",
    agent_type: "CODE_REVIEWER",
    pipeline_id: "pipe-1",
    stage_number: 6,
    status: "completed",
    model: "gpt-4o",
    tokens_used: 20000,
    cost_usd: 0.2,
    started_at: "2026-03-20T10:00:00Z",
    completed_at: "2026-03-20T10:05:00Z",
  },
  {
    id: "a3",
    name: "Agent Gamma",
    agent_type: "TESTER",
    pipeline_id: "pipe-1",
    stage_number: 7,
    status: "completed",
    model: "claude-sonnet-4-20250514",
    tokens_used: 30000,
    cost_usd: 0.3,
    started_at: "2026-03-20T10:00:00Z",
    completed_at: "2026-03-20T10:05:00Z",
  },
];

vi.mock("@/stores/agent-store", () => ({
  useAgentStore: (selector: (state: Record<string, unknown>) => unknown) => {
    const agentsMap: Record<string, Agent> = {};
    for (const a of mockAgents) {
      agentsMap[a.id] = a;
    }
    const state = { agents: agentsMap };
    return selector(state);
  },
}));

describe("CostBreakdown", () => {
  it("shows per-agent table with correct cost values", () => {
    render(<CostBreakdown />);

    expect(screen.getByText("Agent Alpha")).toBeInTheDocument();
    expect(screen.getByText("Agent Beta")).toBeInTheDocument();
    expect(screen.getByText("Agent Gamma")).toBeInTheDocument();

    // Check cost values appear (formatted as $X.XXXX)
    expect(screen.getAllByText("$0.1000").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("$0.2000").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("$0.3000").length).toBeGreaterThanOrEqual(1);
  });

  it("shows correct total sums", () => {
    render(<CostBreakdown />);

    // Total cost should be 0.1 + 0.2 + 0.3 = 0.6
    const totalElements = screen.getAllByText("$0.6000");
    expect(totalElements.length).toBeGreaterThanOrEqual(1);

    // Total tokens should be 10000 + 20000 + 30000 = 60000
    const tokenTotals = screen.getAllByText("60,000");
    expect(tokenTotals.length).toBeGreaterThanOrEqual(1);
  });

  it("shows per-stage section", () => {
    render(<CostBreakdown />);

    // Stage names should be present
    expect(screen.getByText("Per Stage")).toBeInTheDocument();
  });

  it("shows per-model section", () => {
    render(<CostBreakdown />);

    expect(screen.getByText("Per Model")).toBeInTheDocument();
    expect(screen.getByText("claude-sonnet-4-20250514")).toBeInTheDocument();
    expect(screen.getByText("gpt-4o")).toBeInTheDocument();
  });
});
