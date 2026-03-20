import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { pipelineApi } from "@/api/pipelines";
import { useAgentStore } from "@/stores/agent-store";
import { usePipelineStore } from "@/stores/pipeline-store";
import type { Pipeline } from "@/types/pipeline";
import { PipelineView } from "./pipeline-view";

const originalConsoleError = console.error;

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

vi.mock("@xyflow/react", () => ({
  ReactFlow: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="react-flow">{children}</div>
  ),
  Background: () => <div data-testid="flow-background" />,
  Controls: () => <div data-testid="flow-controls" />,
  MiniMap: () => <div data-testid="flow-minimap" />,
  BackgroundVariant: { Dots: "dots" },
}));

vi.mock("@/hooks/use-pipeline-events", () => ({
  usePipelineEvents: vi.fn(),
}));

vi.mock("@/hooks/use-agent-status", () => ({
  useAgentStatus: vi.fn(),
}));

vi.mock("@/api/pipelines", () => ({
  pipelineApi: {
    approvePhase: vi.fn(),
    create: vi.fn(),
    start: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    cancel: vi.fn(),
    get: vi.fn(),
    list: vi.fn(),
  },
}));

function makePipeline(overrides: Partial<Pipeline> = {}): Pipeline {
  return {
    id: "pipe-1",
    project_id: "proj-1",
    mode: "full",
    status: "running",
    current_phase: "review",
    total_stages: 2,
    stages: [
      {
        id: "stage-1",
        name: "implementation",
        stage_number: 0,
        status: "completed",
        started_at: null,
        completed_at: null,
        agents: [],
      },
      {
        id: "stage-2",
        name: "review",
        stage_number: 1,
        status: "waiting",
        started_at: null,
        completed_at: null,
        agents: [],
        requires_approval: true,
        approved_by: null,
        error_message: null,
      },
    ],
    config: null,
    started_at: null,
    completed_at: null,
    total_tokens_used: 1200,
    total_cost_usd: 0.42,
    error_message: null,
    ...overrides,
  };
}

describe("PipelineView", () => {
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
    usePipelineStore.getState().reset();
    useAgentStore.getState().reset();
    vi.mocked(pipelineApi.list).mockResolvedValue({
      status: "success",
      data: [],
      meta: { request_id: "req-list", timestamp: "2026-03-20T10:00:00Z" },
      pagination: null,
    });
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    usePipelineStore.getState().reset();
    useAgentStore.getState().reset();
  });

  it("submits approval notes and refreshes the active pipeline", async () => {
    const initialPipeline = makePipeline();
    const approvedPipeline = makePipeline({
      stages: [
        initialPipeline.stages[0]!,
        {
          ...initialPipeline.stages[1]!,
          status: "completed",
          approved_by: "reviewer@example.com",
        },
      ],
    });

    usePipelineStore.getState().setPipelines([initialPipeline]);
    usePipelineStore.getState().setActivePipeline(initialPipeline.id);

    const approvalRequest = createDeferred<{
      status: "success";
      data: never;
      meta: { request_id: string; timestamp: string };
    }>();
    const refreshedPipeline = createDeferred<{
      status: "success";
      data: Pipeline;
      meta: { request_id: string; timestamp: string };
    }>();

    vi.mocked(pipelineApi.approvePhase).mockReturnValue(approvalRequest.promise);
    vi.mocked(pipelineApi.get).mockReturnValue(refreshedPipeline.promise);

    render(<PipelineView />);

    fireEvent.change(screen.getByLabelText("Review note for review"), {
      target: { value: "Ship it." },
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Approve review" }));
      approvalRequest.resolve({
        status: "success",
        data: {} as never,
        meta: { request_id: "req-1", timestamp: "2026-03-20T10:00:00Z" },
      });
      refreshedPipeline.resolve({
        status: "success",
        data: approvedPipeline,
        meta: { request_id: "req-2", timestamp: "2026-03-20T10:00:01Z" },
      });
      await approvalRequest.promise;
      await refreshedPipeline.promise;
    });

    await waitFor(() => {
      expect(pipelineApi.approvePhase).toHaveBeenCalledWith("pipe-1", "stage-2", {
        approved: true,
        comment: "Ship it.",
      });
    });

    await waitFor(() => {
      expect(pipelineApi.get).toHaveBeenCalledWith("pipe-1");
      expect(screen.getByText("Approved by reviewer@example.com")).toBeInTheDocument();
    });

    expect(
      usePipelineStore.getState().pipelines["pipe-1"]?.stages[1]?.status,
    ).toBe("completed");
  });

  it("shows an inline error when phase approval fails", async () => {
    const initialPipeline = makePipeline();
    usePipelineStore.getState().setPipelines([initialPipeline]);
    usePipelineStore.getState().setActivePipeline(initialPipeline.id);

    const rejection = createDeferred<never>();
    vi.mocked(pipelineApi.approvePhase).mockReturnValue(rejection.promise);

    render(<PipelineView />);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Request changes for review" }));
      rejection.reject(new Error("Approval service unavailable"));
      try {
        await rejection.promise;
      } catch {
        // expected in test
      }
    });

    await waitFor(() => {
      expect(
        screen.getByText("Approval service unavailable"),
      ).toBeInTheDocument();
    });

    expect(pipelineApi.get).not.toHaveBeenCalled();
  });

  it("loads run history and switches to a selected pipeline run", async () => {
    const activePipeline = makePipeline({ id: "pipe-2", started_at: "2026-03-20T10:00:00Z" });
    const olderPipeline = makePipeline({
      id: "pipe-1",
      status: "completed",
      current_phase: "implementation",
      total_tokens_used: 800,
      total_cost_usd: 0.21,
      started_at: "2026-03-19T08:00:00Z",
      completed_at: "2026-03-19T08:30:00Z",
    });
    const olderPipelineDetail = makePipeline({
      ...olderPipeline,
      stages: [
        {
          id: "stage-1",
          name: "implementation",
          stage_number: 0,
          status: "completed",
          started_at: olderPipeline.started_at,
          completed_at: olderPipeline.completed_at,
          agents: [],
        },
      ],
    });

    usePipelineStore.getState().setPipelines([activePipeline]);
    usePipelineStore.getState().setActivePipeline(activePipeline.id);

    vi.mocked(pipelineApi.list).mockResolvedValue({
      status: "success",
      data: [activePipeline, olderPipeline],
      meta: { request_id: "req-list", timestamp: "2026-03-20T10:00:00Z" },
      pagination: null,
    });
    vi.mocked(pipelineApi.get).mockResolvedValue({
      status: "success",
      data: olderPipelineDetail,
      meta: { request_id: "req-get", timestamp: "2026-03-20T10:00:01Z" },
    });

    render(<PipelineView />);

    await waitFor(() => {
      expect(pipelineApi.list).toHaveBeenCalledWith("proj-1");
      expect(screen.getByText("Run history")).toBeInTheDocument();
      expect(screen.getByText("Run 2")).toBeInTheDocument();
      expect(screen.getByText("Active run")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Open pipeline run 2" }));
    });

    await waitFor(() => {
      expect(pipelineApi.get).toHaveBeenCalledWith("pipe-1");
      expect(usePipelineStore.getState().activePipelineId).toBe("pipe-1");
      expect(screen.getByText(/execution overview/i)).toBeInTheDocument();
    });
  });

  it("pauses the active pipeline run and refreshes the view", async () => {
    const runningPipeline = makePipeline({ status: "running" });
    const pausedPipeline = makePipeline({ status: "paused" });

    usePipelineStore.getState().setPipelines([runningPipeline]);
    usePipelineStore.getState().setActivePipeline(runningPipeline.id);

    vi.mocked(pipelineApi.pause).mockResolvedValue({
      status: "success",
      data: { id: "pipe-1", status: "paused", timestamp: "2026-03-20T10:00:00Z" },
      meta: { request_id: "req-pause", timestamp: "2026-03-20T10:00:00Z" },
    });
    vi.mocked(pipelineApi.get).mockResolvedValue({
      status: "success",
      data: pausedPipeline,
      meta: { request_id: "req-get", timestamp: "2026-03-20T10:00:01Z" },
    });

    render(<PipelineView />);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Pause pipeline run" }));
    });

    await waitFor(() => {
      expect(pipelineApi.pause).toHaveBeenCalledWith("pipe-1");
      expect(pipelineApi.get).toHaveBeenCalledWith("pipe-1");
      expect(screen.getByRole("button", { name: "Resume pipeline run" })).toBeInTheDocument();
    });
  });

  it("shows an inline error when cancelling the run fails", async () => {
    const runningPipeline = makePipeline({ status: "running" });

    usePipelineStore.getState().setPipelines([runningPipeline]);
    usePipelineStore.getState().setActivePipeline(runningPipeline.id);

    const rejection = createDeferred<never>();
    vi.mocked(pipelineApi.cancel).mockReturnValue(rejection.promise);

    render(<PipelineView />);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Cancel pipeline run" }));
      rejection.reject(new Error("Cancellation service unavailable"));
      try {
        await rejection.promise;
      } catch {
        // expected in test
      }
    });

    await waitFor(() => {
      expect(screen.getByText("Cancellation service unavailable")).toBeInTheDocument();
    });

    expect(pipelineApi.get).not.toHaveBeenCalled();
  });

  it("retries a failed pipeline run by starting a new run and switching to it", async () => {
    const failedPipeline = makePipeline({
      id: "pipe-failed",
      status: "failed",
      mode: "quick",
      current_phase: "testing",
      error_message: "Unit tests failed",
    });
    const restartedPipeline = makePipeline({
      id: "pipe-retry",
      status: "running",
      mode: "quick",
      current_phase: "planning",
    });

    usePipelineStore.getState().setPipelines([failedPipeline]);
    usePipelineStore.getState().setActivePipeline(failedPipeline.id);

    vi.mocked(pipelineApi.create).mockResolvedValue({
      status: "success",
      data: restartedPipeline,
      meta: { request_id: "req-create", timestamp: "2026-03-20T10:10:00Z" },
    });
    vi.mocked(pipelineApi.start).mockResolvedValue({
      status: "success",
      data: { id: "pipe-retry", status: "running", timestamp: "2026-03-20T10:10:01Z" },
      meta: { request_id: "req-start", timestamp: "2026-03-20T10:10:01Z" },
    });
    vi.mocked(pipelineApi.get).mockResolvedValue({
      status: "success",
      data: restartedPipeline,
      meta: { request_id: "req-get", timestamp: "2026-03-20T10:10:02Z" },
    });

    render(<PipelineView />);

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Retry pipeline run" }));
    });

    await waitFor(() => {
      expect(pipelineApi.create).toHaveBeenCalledWith("proj-1", "quick");
      expect(pipelineApi.start).toHaveBeenCalledWith("pipe-retry");
      expect(pipelineApi.get).toHaveBeenCalledWith("pipe-retry");
      expect(usePipelineStore.getState().activePipelineId).toBe("pipe-retry");
      expect(screen.getByRole("button", { name: "Pause pipeline run" })).toBeInTheDocument();
    });
  });

  it("shows failure reasons in the execution overview and run history", async () => {
    const failedPipeline = makePipeline({
      id: "pipe-failed",
      status: "failed",
      current_phase: "testing",
      started_at: "2026-03-20T10:10:00Z",
      completed_at: "2026-03-20T10:12:00Z",
      error_message: "Unit tests failed in payments.spec.ts",
      stages: [
        {
          id: "stage-1",
          name: "implementation",
          stage_number: 0,
          status: "completed",
          started_at: null,
          completed_at: null,
          agents: [],
        },
        {
          id: "stage-2",
          name: "integration_testing",
          stage_number: 1,
          status: "failed",
          started_at: "2026-03-20T10:11:00Z",
          completed_at: "2026-03-20T10:12:00Z",
          agents: [],
          error_message: "payments.spec.ts exceeded timeout",
        },
      ],
    });

    usePipelineStore.getState().setPipelines([failedPipeline]);
    usePipelineStore.getState().setActivePipeline(failedPipeline.id);

    vi.mocked(pipelineApi.list).mockResolvedValue({
      status: "success",
      data: [failedPipeline],
      meta: { request_id: "req-list", timestamp: "2026-03-20T10:13:00Z" },
      pagination: null,
    });

    render(<PipelineView />);

    await waitFor(() => {
      expect(screen.getByText("Run history")).toBeInTheDocument();
    });

    const executionOverview = screen.getByText(/execution overview/i).closest("div.rounded-2xl");
    const runHistory = screen.getByText("Run history").closest("div.rounded-2xl");

    expect(executionOverview).not.toBeNull();
    expect(runHistory).not.toBeNull();

    expect(
      within(executionOverview as HTMLElement).getByText(/failure reason:/i),
    ).toBeInTheDocument();
    expect(
      within(executionOverview as HTMLElement).getByText(/unit tests failed in payments.spec.ts/i),
    ).toBeInTheDocument();
    expect(
      within(executionOverview as HTMLElement).getByText(/failed stage:/i),
    ).toBeInTheDocument();
    expect(
      within(executionOverview as HTMLElement).getByText(/integration testing · payments.spec.ts exceeded timeout/i),
    ).toBeInTheDocument();
    expect(
      within(runHistory as HTMLElement).getByText(/failure reason:/i),
    ).toBeInTheDocument();
    expect(
      within(runHistory as HTMLElement).getByText(/unit tests failed in payments.spec.ts/i),
    ).toBeInTheDocument();
    expect(
      within(runHistory as HTMLElement).getByText(/failed stage:/i),
    ).toBeInTheDocument();
    expect(
      within(runHistory as HTMLElement).getByText(/integration testing · payments.spec.ts exceeded timeout/i),
    ).toBeInTheDocument();
  });
});