import { useOperatorStore } from "@/stores/operator-store";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { pipelineApi } from "@/api/pipelines";
import { useAgentStore } from "@/stores/agent-store";
import { usePipelineStore } from "@/stores/pipeline-store";
import type { Pipeline } from "@/types/pipeline";
import { PipelineView } from "./pipeline-view";

const originalConsoleError = console.error;
const originalCreateObjectURL = URL.createObjectURL;
const originalRevokeObjectURL = URL.revokeObjectURL;
const originalBlob = globalThis.Blob;

class MockBlob {
  public readonly parts: BlobPart[];
  public readonly type: string;

  public constructor(parts: BlobPart[], options?: BlobPropertyBag) {
    this.parts = parts;
    this.type = options?.type ?? "";
  }
}

function asMockBlob(value: Blob | MediaSource | undefined): MockBlob {
  return value as unknown as MockBlob;
}

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

  it("reflects operator actions and status updates in the UI", async () => {
    const pipeline = makePipeline();
    usePipelineStore.getState().setPipelines([pipeline]);
    usePipelineStore.getState().setActivePipeline(pipeline.id);

    render(<PipelineView />);

    // Simulate operator action event
    act(() => {
      useOperatorStore.getState().addAction(pipeline.project_id, "run_started", { by: "operator-1" });
    });

    // Simulate operator status event
    act(() => {
      useOperatorStore.getState().setStatus(pipeline.project_id, "running", "Operator is running the pipeline");
    });

    // Assert that operator action and status are reflected in the UI
    await waitFor(() => {
      // You may need to adjust these selectors based on how operator info is rendered
      expect(screen.getByText(/operator is running the pipeline/i)).toBeInTheDocument();
      expect(screen.getByText(/run_started/i)).toBeInTheDocument();
      expect(screen.getByText(/operator-1/i)).toBeInTheDocument();
    });
  });
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;
  let anchorClickSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    vi.clearAllMocks();
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
    Object.defineProperty(globalThis, "Blob", {
      configurable: true,
      writable: true,
      value: MockBlob,
    });
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(() => "blob:diagnostics"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(() => {}),
    });
    anchorClickSpy = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});
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
    if (originalCreateObjectURL) {
      Object.defineProperty(URL, "createObjectURL", {
        configurable: true,
        writable: true,
        value: originalCreateObjectURL,
      });
    } else {
      Reflect.deleteProperty(URL, "createObjectURL");
    }

    if (originalRevokeObjectURL) {
      Object.defineProperty(URL, "revokeObjectURL", {
        configurable: true,
        writable: true,
        value: originalRevokeObjectURL,
      });
    } else {
      Reflect.deleteProperty(URL, "revokeObjectURL");
    }

    Object.defineProperty(globalThis, "Blob", {
      configurable: true,
      writable: true,
      value: originalBlob,
    });

    anchorClickSpy.mockRestore();
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

  it("keeps the active run history entry fresh when the active pipeline updates", async () => {
    const activePipeline = makePipeline({
      id: "pipe-live",
      status: "running",
      current_phase: "implementation",
      started_at: "2026-03-20T10:10:00Z",
      stages: [
        {
          id: "stage-1",
          name: "implementation",
          stage_number: 0,
          status: "running",
          started_at: "2026-03-20T10:10:00Z",
          completed_at: null,
          agents: [],
        },
      ],
    });
    const staleHistoryEntry = makePipeline({
      ...activePipeline,
      status: "running",
      error_message: null,
    });
    const refreshedPipeline = makePipeline({
      ...activePipeline,
      status: "failed",
      current_phase: "integration_testing",
      error_message: "Payments regression failed",
      stages: [
        {
          id: "stage-1",
          name: "implementation",
          stage_number: 0,
          status: "completed",
          started_at: "2026-03-20T10:10:00Z",
          completed_at: "2026-03-20T10:15:00Z",
          agents: [],
        },
        {
          id: "stage-2",
          name: "integration_testing",
          stage_number: 1,
          status: "failed",
          started_at: "2026-03-20T10:15:00Z",
          completed_at: "2026-03-20T10:18:00Z",
          agents: [],
          error_message: "payments.spec.ts exceeded timeout",
        },
      ],
    });

    usePipelineStore.getState().setPipelines([activePipeline]);
    usePipelineStore.getState().setActivePipeline(activePipeline.id);

    vi.mocked(pipelineApi.list).mockResolvedValue({
      status: "success",
      data: [staleHistoryEntry],
      meta: { request_id: "req-list", timestamp: "2026-03-20T10:11:00Z" },
      pagination: null,
    });

    render(<PipelineView />);

    await waitFor(() => {
      expect(screen.getByText("Run history")).toBeInTheDocument();
      expect(screen.getByText("Active run")).toBeInTheDocument();
    });

    act(() => {
      usePipelineStore.getState().upsertPipeline(refreshedPipeline);
    });

    const runHistory = screen.getByText("Run history").closest("div.rounded-2xl");

    await waitFor(() => {
      expect(runHistory).not.toBeNull();
      expect(
        within(runHistory as HTMLElement).getByText(/failure reason:/i),
      ).toBeInTheDocument();
      expect(
        within(runHistory as HTMLElement).getByText(/payments regression failed/i),
      ).toBeInTheDocument();
      expect(
        within(runHistory as HTMLElement).getByText(/failed stage:/i),
      ).toBeInTheDocument();
      expect(
        within(runHistory as HTMLElement).getByText(/integration testing · payments.spec.ts exceeded timeout/i),
      ).toBeInTheDocument();
    });
  });

  it("highlights the focused failed stage and supports jumping to it", async () => {
    const failedPipeline = makePipeline({
      id: "pipe-failed",
      status: "failed",
      current_phase: "testing",
      error_message: "Unit tests failed",
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
          started_at: null,
          completed_at: null,
          agents: [],
          error_message: "payments.spec.ts exceeded timeout",
        },
      ],
    });

    usePipelineStore.getState().setPipelines([failedPipeline]);
    usePipelineStore.getState().setActivePipeline(failedPipeline.id);
    usePipelineStore.getState().setFocusedStage("stage-2");

    render(<PipelineView />);

    await waitFor(() => {
      expect(screen.getByText(/focused failure/i)).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: /jump to stage/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /hide details for integration testing/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/awaiting reviewer decision|not required/i)).toBeInTheDocument();
    expect(usePipelineStore.getState().focusedStageId).toBe("stage-2");
  });

  it("lets operators expand and collapse stage details manually", async () => {
    const pipeline = makePipeline({
      stages: [
        {
          id: "stage-1",
          name: "implementation",
          stage_number: 0,
          status: "completed",
          started_at: "2026-03-20T09:00:00Z",
          completed_at: "2026-03-20T09:15:00Z",
          agents: ["agent-1", "agent-2"],
        },
        {
          id: "stage-2",
          name: "review",
          stage_number: 1,
          status: "completed",
          started_at: "2026-03-20T09:15:00Z",
          completed_at: "2026-03-20T09:25:00Z",
          agents: [],
        },
      ],
    });

    usePipelineStore.getState().setPipelines([pipeline]);
    usePipelineStore.getState().setActivePipeline(pipeline.id);

    render(<PipelineView />);

    const showDetailsButton = screen.getByRole("button", {
      name: /show details for implementation/i,
    });

    expect(screen.queryByText("agent-1, agent-2")).not.toBeInTheDocument();

    fireEvent.click(showDetailsButton);

    expect(
      await screen.findByRole("button", { name: /hide details for implementation/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("agent-1, agent-2")).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: /hide details for implementation/i }),
    );

    await waitFor(() => {
      expect(screen.queryByText("agent-1, agent-2")).not.toBeInTheDocument();
    });
  });

  it("copies diagnostics from the overview and run history", async () => {
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
      expect(screen.getByRole("button", { name: /copy pipeline diagnostics/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /copy diagnostics for run 1/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /copy pipeline diagnostics/i }));
    fireEvent.click(screen.getByRole("button", { name: /copy diagnostics for run 1/i }));

    await waitFor(() => {
      const writeText = vi.mocked(navigator.clipboard.writeText);
      expect(writeText).toHaveBeenCalledTimes(2);
      expect(writeText.mock.calls[0]?.[0]).toContain("Pipeline ID: pipe-failed");
      expect(writeText.mock.calls[0]?.[0]).toContain("Failure reason: Unit tests failed in payments.spec.ts");
      expect(writeText.mock.calls[0]?.[0]).toContain("Failed stage: Integration Testing");
      expect(writeText.mock.calls[1]?.[0]).toContain("Stage error: payments.spec.ts exceeded timeout");
      expect(screen.getAllByText(/diagnostics copied/i).length).toBeGreaterThan(0);
    });
  });

  it("exports diagnostics as JSON and Markdown", async () => {
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
          agents: ["agent-impl"],
        },
        {
          id: "stage-2",
          name: "integration_testing",
          stage_number: 1,
          status: "failed",
          started_at: "2026-03-20T10:11:00Z",
          completed_at: "2026-03-20T10:12:00Z",
          agents: ["agent-test"],
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
      expect(screen.getByRole("button", { name: "Export diagnostics as JSON" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Export diagnostics as Markdown" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Export diagnostics as JSON for run 1" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Export diagnostics as JSON" }));
    fireEvent.click(screen.getByRole("button", { name: "Export diagnostics as Markdown for run 1" }));

    await waitFor(async () => {
      const createObjectUrl = vi.mocked(URL.createObjectURL);
      const revokeObjectUrl = vi.mocked(URL.revokeObjectURL);

      expect(createObjectUrl).toHaveBeenCalledTimes(2);
      expect(anchorClickSpy).toHaveBeenCalledTimes(2);
      expect(revokeObjectUrl).toHaveBeenCalledTimes(2);

      const jsonBlob = createObjectUrl.mock.calls[0]?.[0];
      const markdownBlob = createObjectUrl.mock.calls[1]?.[0];

      expect(jsonBlob).toBeInstanceOf(MockBlob);
      expect(markdownBlob).toBeInstanceOf(MockBlob);

      const jsonText = String(asMockBlob(jsonBlob).parts[0] ?? "");
      const markdownText = String(asMockBlob(markdownBlob).parts[0] ?? "");

      expect(jsonText).toContain('"pipelineId": "pipe-failed"');
      expect(jsonText).toContain('"failureReason": "Unit tests failed in payments.spec.ts"');
      expect(jsonText).toContain('"name": "Integration Testing"');

      expect(markdownText).toContain("# Pipeline diagnostics");
      expect(markdownText).toContain("- Failed stage: Integration Testing");
      expect(markdownText).toContain("- Stage 2: Integration Testing — Status: failed");
    });
  });

  it("inspects a failed run from history and focuses its failed stage", async () => {
    const activePipeline = makePipeline({
      id: "pipe-active",
      status: "running",
      current_phase: "implementation",
      started_at: "2026-03-20T10:20:00Z",
      stages: [
        {
          id: "stage-active",
          name: "implementation",
          stage_number: 0,
          status: "running",
          started_at: "2026-03-20T10:20:00Z",
          completed_at: null,
          agents: [],
        },
      ],
    });
    const failedHistoryPipeline = makePipeline({
      id: "pipe-failed-history",
      status: "failed",
      current_phase: "integration_testing",
      started_at: "2026-03-20T09:00:00Z",
      completed_at: "2026-03-20T09:30:00Z",
      error_message: "Regression suite failed",
      stages: [
        {
          id: "stage-1",
          name: "implementation",
          stage_number: 0,
          status: "completed",
          started_at: "2026-03-20T09:00:00Z",
          completed_at: "2026-03-20T09:10:00Z",
          agents: [],
        },
        {
          id: "stage-failed-history",
          name: "integration_testing",
          stage_number: 1,
          status: "failed",
          started_at: "2026-03-20T09:10:00Z",
          completed_at: "2026-03-20T09:30:00Z",
          agents: [],
          error_message: "payments.spec.ts exceeded timeout",
        },
      ],
    });

    usePipelineStore.getState().setPipelines([activePipeline]);
    usePipelineStore.getState().setActivePipeline(activePipeline.id);

    vi.mocked(pipelineApi.list).mockResolvedValue({
      status: "success",
      data: [activePipeline, failedHistoryPipeline],
      meta: { request_id: "req-list", timestamp: "2026-03-20T10:40:00Z" },
      pagination: null,
    });
    vi.mocked(pipelineApi.get).mockResolvedValue({
      status: "success",
      data: failedHistoryPipeline,
      meta: { request_id: "req-get", timestamp: "2026-03-20T10:40:01Z" },
    });

    render(<PipelineView />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /inspect failure for run 2/i })).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /inspect failure for run 2/i }));
    });

    await waitFor(() => {
      expect(pipelineApi.get).toHaveBeenCalledWith("pipe-failed-history");
      expect(usePipelineStore.getState().activePipelineId).toBe("pipe-failed-history");
      expect(usePipelineStore.getState().focusedStageId).toBe("stage-failed-history");
      expect(screen.getByText(/focused failure/i)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /hide details for integration testing/i }),
      ).toBeInTheDocument();
    });
  });
});