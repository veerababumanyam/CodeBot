import { describe, it, expect, vi, beforeEach } from "vitest";
import { CodeBotClient } from "../src/client/api.js";
import { formatAgentTable } from "../src/output/formatters.js";
import type { AgentResponse, PaginatedEnvelope } from "../src/types.js";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function makeAgent(overrides: Partial<AgentResponse> = {}): AgentResponse {
  return {
    id: "agent-001-uuid",
    name: "BackendDevAgent",
    agent_type: "backend_dev",
    pipeline_id: "pipe-001",
    stage_number: 5,
    status: "idle",
    model: "claude-sonnet-4-20250514",
    tokens_used: 1500,
    cost_usd: 0.0045,
    started_at: null,
    completed_at: null,
    ...overrides,
  };
}

describe("CodeBotClient - Agents", () => {
  let client: CodeBotClient;

  beforeEach(() => {
    vi.resetAllMocks();
    client = new CodeBotClient("http://localhost:8000", "test-token");
  });

  it("listAgents calls GET /api/v1/agents with pipeline_id", async () => {
    const agents = [
      makeAgent({ id: "a1", name: "OrchestratorAgent", status: "completed" }),
      makeAgent({ id: "a2", name: "BackendDevAgent", status: "executing" }),
      makeAgent({ id: "a3", name: "CodeReviewerAgent", status: "idle" }),
    ];
    const envelope: PaginatedEnvelope<AgentResponse> = {
      status: "success",
      data: agents,
      meta: { request_id: "r1", timestamp: "2026-03-20T10:00:00Z" },
      pagination: { page: 1, per_page: 20, total: 3, total_pages: 1 },
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(envelope),
    });

    const result = await client.listAgents("pipe-001");

    expect(result.data).toHaveLength(3);
    expect(result.data[0]!.name).toBe("OrchestratorAgent");
    expect(result.data[1]!.status).toBe("executing");
    expect(result.data[2]!.status).toBe("idle");

    const [url] = mockFetch.mock.calls[0]!;
    expect(url).toContain("/api/v1/agents?pipeline_id=pipe-001");
  });

  it("handles empty agent list", async () => {
    const envelope: PaginatedEnvelope<AgentResponse> = {
      status: "success",
      data: [],
      meta: { request_id: "r2", timestamp: "2026-03-20T10:00:00Z" },
      pagination: null,
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(envelope),
    });

    const result = await client.listAgents("pipe-empty");
    expect(result.data).toHaveLength(0);
  });
});

describe("formatAgentTable", () => {
  it("formats agents into a table with status and cost", () => {
    const agents = [
      makeAgent({
        id: "agent-001-uuid",
        name: "OrchestratorAgent",
        agent_type: "orchestrator",
        status: "completed",
        tokens_used: 5000,
        cost_usd: 0.015,
      }),
      makeAgent({
        id: "agent-002-uuid",
        name: "BackendDevAgent",
        agent_type: "backend_dev",
        status: "executing",
        tokens_used: 12000,
        cost_usd: 0.036,
      }),
      makeAgent({
        id: "agent-003-uuid",
        name: "CodeReviewerAgent",
        agent_type: "code_reviewer",
        status: "idle",
        tokens_used: 0,
        cost_usd: 0,
      }),
    ];

    const output = formatAgentTable(agents);

    expect(output).toContain("agent-00");
    expect(output).toContain("OrchestratorAgent");
    expect(output).toContain("BackendDevAgent");
    expect(output).toContain("CodeReviewerAgent");
    expect(output).toContain("$0.0150");
    expect(output).toContain("$0.0360");
    expect(output).toContain("$0.0000");
    expect(output).toContain("---");
  });
});
