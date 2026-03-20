import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AgentPanel } from "./agent-panel";
import type { Agent, AgentLogEvent } from "@/types/agent";

const mockAgents: Agent[] = [
  {
    id: "agent-1",
    name: "BackendDev",
    agent_type: "BACKEND_DEV",
    pipeline_id: "pipe-1",
    stage_number: 5,
    status: "executing",
    model: "claude-sonnet-4-20250514",
    tokens_used: 15000,
    cost_usd: 0.045,
    started_at: "2026-03-20T10:00:00Z",
    completed_at: null,
  },
  {
    id: "agent-2",
    name: "CodeReviewer",
    agent_type: "CODE_REVIEWER",
    pipeline_id: "pipe-1",
    stage_number: 6,
    status: "completed",
    model: "gpt-4o",
    tokens_used: 8500,
    cost_usd: 0.025,
    started_at: "2026-03-20T09:00:00Z",
    completed_at: "2026-03-20T09:05:00Z",
  },
  {
    id: "agent-3",
    name: "SecurityAuditor",
    agent_type: "SECURITY_AUDITOR",
    pipeline_id: "pipe-1",
    stage_number: 6,
    status: "failed",
    model: "claude-sonnet-4-20250514",
    tokens_used: 3200,
    cost_usd: 0.0096,
    started_at: "2026-03-20T09:10:00Z",
    completed_at: "2026-03-20T09:12:00Z",
  },
];

const mockLogs: Record<string, AgentLogEvent[]> = {
  "agent-1": [
    {
      agent_id: "agent-1",
      pipeline_id: "pipe-1",
      level: "info",
      message: "Starting execution",
      timestamp: "2026-03-20T10:00:00Z",
    },
  ],
};

const mockSelectAgent = vi.fn();

vi.mock("@/stores/agent-store", () => ({
  useAgentStore: (selector: (state: Record<string, unknown>) => unknown) => {
    const agentsMap: Record<string, Agent> = {};
    for (const a of mockAgents) {
      agentsMap[a.id] = a;
    }
    const state = {
      agents: agentsMap,
      logs: mockLogs,
      selectedAgentId: null as string | null,
      selectAgent: mockSelectAgent,
    };
    return selector(state);
  },
}));

describe("AgentPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all agent names in the list", () => {
    render(<AgentPanel />);

    expect(screen.getByText("BackendDev")).toBeInTheDocument();
    expect(screen.getByText("CodeReviewer")).toBeInTheDocument();
    expect(screen.getByText("SecurityAuditor")).toBeInTheDocument();
  });

  it("clicking an agent card calls selectAgent", () => {
    render(<AgentPanel />);

    const backendDevCard = screen.getByText("BackendDev").closest("button");
    expect(backendDevCard).toBeTruthy();
    fireEvent.click(backendDevCard!);

    expect(mockSelectAgent).toHaveBeenCalledWith("agent-1");
  });

  it("shows detail panel text when no agent selected", () => {
    render(<AgentPanel />);

    expect(
      screen.getByText("Select an agent to view details"),
    ).toBeInTheDocument();
  });
});
