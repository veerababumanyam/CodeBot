import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./client";
import { normalizePipeline, pipelineApi } from "./pipelines";

vi.mock("./client", () => ({
  api: {
    post: vi.fn(),
  },
}));

afterEach(() => {
  vi.clearAllMocks();
});

describe("normalizePipeline", () => {
  it("maps backend pipeline detail and phases into dashboard pipeline shape", () => {
    const normalized = normalizePipeline(
      {
        id: "pipe-1",
        project_id: "proj-1",
        status: "pending",
        current_phase: "planning",
        started_at: null,
        completed_at: null,
        total_tokens_used: 0,
        total_cost_usd: 0,
        graph_definition: {
          mode: "review-only",
          config: { kickoff_flow: "brainstorm" },
        },
      },
      [
        {
          id: "phase-1",
          name: "planning",
          phase_type: "planning",
          status: "pending",
          order: 0,
          requires_approval: false,
          approved_by: null,
          started_at: null,
          completed_at: null,
        },
        {
          id: "phase-2",
          name: "review",
          phase_type: "review",
          status: "waiting_approval",
          order: 1,
          requires_approval: true,
          approved_by: null,
          started_at: null,
          completed_at: null,
          error_message: null,
        },
      ],
    );

    expect(normalized.mode).toBe("review_only");
    expect(normalized.current_phase).toBe("planning");
    expect(normalized.total_stages).toBe(2);
    expect(normalized.stages[0]).toMatchObject({
      id: "phase-1",
      stage_number: 0,
      status: "idle",
    });
    expect(normalized.stages[1]).toMatchObject({
      id: "phase-2",
      status: "waiting",
      requires_approval: true,
    });
    expect(normalized.config).toEqual({ kickoff_flow: "brainstorm" });
  });

  it("posts phase approval decisions to the approval endpoint", async () => {
    vi.mocked(api.post).mockResolvedValue({
      status: "success",
      data: {
        id: "phase-2",
        name: "review",
        phase_type: "review",
        status: "completed",
        order: 1,
        requires_approval: true,
        approved_by: "reviewer@example.com",
        started_at: null,
        completed_at: "2026-03-20T10:00:00Z",
        error_message: null,
      },
      meta: { request_id: "req-1", timestamp: "2026-03-20T10:00:00Z" },
    });

    await pipelineApi.approvePhase("pipe-1", "phase-2", {
      approved: true,
      comment: "Looks good.",
    });

    expect(api.post).toHaveBeenCalledWith(
      "/api/v1/pipelines/pipe-1/phases/phase-2/approve",
      {
        approved: true,
        comment: "Looks good.",
      },
    );
  });
});
