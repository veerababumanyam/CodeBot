import { describe, it, expect, vi, beforeEach } from "vitest";
import { CodeBotClient } from "../src/client/api.js";
import { formatPipelineStatus } from "../src/output/formatters.js";
import type { PipelineResponse } from "../src/types.js";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function makePipeline(
  overrides: Partial<PipelineResponse> = {},
): PipelineResponse {
  return {
    id: "pipe-001",
    project_id: "proj-001",
    mode: "full",
    status: "created",
    current_stage: 0,
    total_stages: 11,
    created_at: "2026-03-20T10:00:00Z",
    updated_at: "2026-03-20T10:00:00Z",
    ...overrides,
  };
}

function envelope(data: PipelineResponse) {
  return {
    status: "success",
    data,
    meta: { request_id: "r1", timestamp: "2026-03-20T10:00:00Z" },
  };
}

describe("CodeBotClient - Pipelines", () => {
  let client: CodeBotClient;

  beforeEach(() => {
    vi.resetAllMocks();
    client = new CodeBotClient("http://localhost:8000", "test-token");
  });

  it("start pipeline creates and starts in sequence", async () => {
    const created = makePipeline({ status: "created" });
    const started = makePipeline({ status: "running", current_stage: 1 });

    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: () => Promise.resolve(envelope(created)),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve(envelope(started)),
      });

    const pipeline = await client.createPipeline("proj-001", "full");
    expect(pipeline.id).toBe("pipe-001");
    expect(pipeline.status).toBe("created");

    const result = await client.startPipeline(pipeline.id);
    expect(result.status).toBe("running");
    expect(result.current_stage).toBe(1);

    expect(mockFetch).toHaveBeenCalledTimes(2);
    const [createUrl] = mockFetch.mock.calls[0]!;
    expect(createUrl).toContain("/api/v1/projects/proj-001/pipelines");
    const [startUrl] = mockFetch.mock.calls[1]!;
    expect(startUrl).toContain("/api/v1/pipelines/pipe-001/start");
  });

  it("maps review-only preset to review_only for API", async () => {
    const created = makePipeline({ mode: "review_only" });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: () => Promise.resolve(envelope(created)),
    });

    const result = await client.createPipeline("proj-001", "review_only");
    expect(result.mode).toBe("review_only");

    const [, init] = mockFetch.mock.calls[0]!;
    const body = JSON.parse(init.body as string) as { mode: string };
    expect(body.mode).toBe("review_only");
  });

  it("pausePipeline calls POST /api/v1/pipelines/{id}/pause", async () => {
    const paused = makePipeline({ status: "paused" });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(envelope(paused)),
    });

    const result = await client.pausePipeline("pipe-001");
    expect(result.status).toBe("paused");

    const [url, init] = mockFetch.mock.calls[0]!;
    expect(url).toContain("/api/v1/pipelines/pipe-001/pause");
    expect(init.method).toBe("POST");
  });

  it("resumePipeline calls POST /api/v1/pipelines/{id}/resume", async () => {
    const resumed = makePipeline({ status: "running" });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(envelope(resumed)),
    });

    const result = await client.resumePipeline("pipe-001");
    expect(result.status).toBe("running");
  });

  it("stopPipeline calls POST /api/v1/pipelines/{id}/stop", async () => {
    const stopped = makePipeline({ status: "cancelled" });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve(envelope(stopped)),
    });

    const result = await client.stopPipeline("pipe-001");
    expect(result.status).toBe("cancelled");
  });
});

describe("formatPipelineStatus", () => {
  it("formats pipeline status into readable output", () => {
    const pipeline = makePipeline({
      status: "running",
      current_stage: 3,
      total_stages: 11,
    });

    const output = formatPipelineStatus(pipeline);

    expect(output).toContain("Pipeline Status");
    expect(output).toContain("pipe-001");
    expect(output).toContain("full");
    expect(output).toContain("3/11");
  });
});
