import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { brainstormApi, type BrainstormSession } from "@/api/brainstorm";
import { pipelineApi } from "@/api/pipelines";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useProjectStore } from "@/stores/project-store";
import { useUiStore } from "@/stores/ui-store";
import type { Pipeline } from "@/types/pipeline";
import { BrainstormPanel } from "./brainstorm-panel";

const originalConsoleError = console.error;

vi.mock("@/api/brainstorm", () => ({
  brainstormApi: {
    start: vi.fn(),
    respond: vi.fn(),
    finalize: vi.fn(),
  },
}));

vi.mock("@/api/pipelines", () => ({
  pipelineApi: {
    create: vi.fn(),
    start: vi.fn(),
    get: vi.fn(),
  },
}));

function makeSession(overrides: Partial<BrainstormSession> = {}): BrainstormSession {
  return {
    session_id: "session-1",
    project_id: "project-1",
    status: "active",
    started_at: "2026-03-20T10:00:00Z",
    updated_at: "2026-03-20T10:05:00Z",
    overview: "Clarify the workflow before kickoff.",
    refined_brief: "Build an internal ops assistant.",
    questions: [
      {
        id: "question-1",
        category: "success_metrics",
        prompt: "How will we measure success?",
        required: true,
        priority: "high",
        answer: "Reduce triage time by 40%.",
        status: "answered",
      },
    ],
    messages: [
      {
        id: "message-1",
        role: "assistant",
        content: "Let's confirm launch readiness.",
        created_at: "2026-03-20T10:05:00Z",
      },
    ],
    summary: {
      readiness_score: 92,
      ready_for_pipeline: true,
      blockers: [],
      recommended_preset: "quick",
      recommended_next_step: "launch_pipeline",
      open_questions: 0,
      answered_questions: 1,
      required_questions_remaining: 0,
    },
    source_context: null,
    agent_output: null,
    ...overrides,
  };
}

function makePipeline(overrides: Partial<Pipeline> = {}): Pipeline {
  return {
    id: "pipe-1",
    project_id: "project-1",
    mode: "quick",
    status: "running",
    current_phase: "planning",
    total_stages: 3,
    stages: [],
    config: null,
    started_at: null,
    completed_at: null,
    total_tokens_used: 0,
    total_cost_usd: 0,
    error_message: null,
    ...overrides,
  };
}

describe("BrainstormPanel", () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.clearAllMocks();
    consoleErrorSpy = vi
      .spyOn(console, "error")
      .mockImplementation((message?: unknown, ...args: unknown[]) => {
        const text = [message, ...args].map((part) => String(part ?? "")).join(" ");
        if (text.includes("not wrapped in act")) {
          return;
        }
        originalConsoleError(message, ...args);
      });
    localStorage.clear();
    usePipelineStore.getState().reset();
    useProjectStore.setState({
      projects: [
        {
          id: "project-1",
          name: "Ops Copilot",
          description: "Internal workflow automation",
          status: "brainstorming",
          project_type: "greenfield",
          prd_format: "markdown",
          tech_stack: {},
          created_at: "2026-03-20T10:00:00Z",
          updated_at: "2026-03-20T10:05:00Z",
        },
      ],
      openProjectIds: ["project-1"],
      activeProjectId: "project-1",
    });
    useUiStore.setState({
      sidebarOpen: true,
      activePanel: "brainstorm",
      theme: "light",
    });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    usePipelineStore.getState().reset();
    useProjectStore.setState({
      projects: [],
      openProjectIds: [],
      activeProjectId: null,
    });
    useUiStore.setState({
      sidebarOpen: true,
      activePanel: "pipeline",
      theme: "light",
    });
  });

  it("shows the execution summary when the user reviews the launch plan", async () => {
    vi.mocked(brainstormApi.start).mockResolvedValue({
      status: "success",
      data: makeSession(),
      meta: { request_id: "req-1", timestamp: "2026-03-20T10:05:00Z" },
    });

    render(<BrainstormPanel />);

    await waitFor(() => {
      expect(screen.getByText("Ops Copilot brainstorm")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Review execution plan" }));

    await waitFor(() => {
      expect(screen.getByText("Execution summary")).toBeInTheDocument();
      expect(screen.getByText("Ready to launch")).toBeInTheDocument();
      expect(screen.getByText("Initialize")).toBeInTheDocument();
    });
  });

  it("finalizes brainstorm and routes into the created pipeline", async () => {
    const activeSession = makeSession();
    const finalizedSession = makeSession({ status: "finalized" });
    const detailedPipeline = makePipeline();

    vi.mocked(brainstormApi.start).mockResolvedValue({
      status: "success",
      data: activeSession,
      meta: { request_id: "req-1", timestamp: "2026-03-20T10:05:00Z" },
    });
    vi.mocked(brainstormApi.finalize).mockResolvedValue({
      status: "success",
      data: finalizedSession,
      meta: { request_id: "req-2", timestamp: "2026-03-20T10:06:00Z" },
    });
    vi.mocked(pipelineApi.create).mockResolvedValue({
      status: "success",
      data: { id: "pipe-1" } as never,
      meta: { request_id: "req-3", timestamp: "2026-03-20T10:06:10Z" },
    });
    vi.mocked(pipelineApi.start).mockResolvedValue({
      status: "success",
      data: { id: "pipe-1", status: "running", timestamp: "2026-03-20T10:06:12Z" },
      meta: { request_id: "req-4", timestamp: "2026-03-20T10:06:12Z" },
    });
    vi.mocked(pipelineApi.get).mockResolvedValue({
      status: "success",
      data: detailedPipeline,
      meta: { request_id: "req-5", timestamp: "2026-03-20T10:06:15Z" },
    });

    render(<BrainstormPanel />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Review execution plan" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Review execution plan" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Launch pipeline" })).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Launch pipeline" }));
    });

    await waitFor(() => {
      expect(brainstormApi.finalize).toHaveBeenCalledWith("project-1");
      expect(pipelineApi.create).toHaveBeenCalledWith("project-1", "quick");
      expect(pipelineApi.start).toHaveBeenCalledWith("pipe-1");
      expect(pipelineApi.get).toHaveBeenCalledWith("pipe-1");
    });

    expect(useUiStore.getState().activePanel).toBe("pipeline");
    expect(usePipelineStore.getState().activePipelineId).toBe("pipe-1");
    expect(useProjectStore.getState().projects[0]?.status).toBe("planning");
  });
});