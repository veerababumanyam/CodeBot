import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { brainstormApi, type BrainstormSession } from "@/api/brainstorm";
import { pipelineApi } from "@/api/pipelines";
import { projectApi } from "@/api/projects";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useProjectStore } from "@/stores/project-store";
import { useUiStore } from "@/stores/ui-store";
import type { Pipeline } from "@/types/pipeline";
import { App } from "./app";

type ProjectCreateResponse = Awaited<ReturnType<typeof projectApi.create>>;
type BrainstormStartResponse = Awaited<ReturnType<typeof brainstormApi.start>>;
type BrainstormFinalizeResponse = Awaited<ReturnType<typeof brainstormApi.finalize>>;
type PipelineCreateResponse = Awaited<ReturnType<typeof pipelineApi.create>>;
type PipelineStartResponse = Awaited<ReturnType<typeof pipelineApi.start>>;
type PipelineGetResponse = Awaited<ReturnType<typeof pipelineApi.get>>;

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

vi.mock("@/hooks/use-socket", () => ({
  useSocket: vi.fn(),
}));

vi.mock("@/hooks/use-theme-sync", () => ({
  useThemeSync: vi.fn(),
}));

vi.mock("@/components/layout/main-layout", () => ({
  MainLayout: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="main-layout">{children}</div>
  ),
}));

vi.mock("@/components/chat/chat-sidebar", () => ({
  ChatSidebar: () => null,
}));

vi.mock("@/components/monitoring/agent-panel", () => ({
  AgentPanel: () => <div>Agent panel</div>,
}));

vi.mock("@/components/monitoring/cost-breakdown", () => ({
  CostBreakdown: () => <div>Cost breakdown</div>,
}));

vi.mock("@/components/editor/code-editor", () => ({
  CodeEditor: () => <div>Code editor</div>,
}));

vi.mock("@/components/editor/file-tree", () => ({
  FileTree: () => <div>File tree</div>,
}));

vi.mock("@/components/terminal/terminal-panel", () => ({
  TerminalPanel: () => <div>Terminal panel</div>,
}));

vi.mock("@/components/preview/preview-frame", () => ({
  PreviewFrame: () => <div>Preview frame</div>,
}));

vi.mock("@/components/pipeline/pipeline-view", () => ({
  PipelineView: () => <div>Pipeline workspace</div>,
}));

vi.mock("@/api/projects", () => ({
  projectApi: {
    list: vi.fn(),
    create: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("@/api/brainstorm", () => ({
  brainstormApi: {
    start: vi.fn(),
    respond: vi.fn(),
    finalize: vi.fn(),
  },
}));

vi.mock("@/api/pipelines", () => ({
  pipelineApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    start: vi.fn(),
    approvePhase: vi.fn(),
  },
}));

function makeProject(overrides: Partial<ReturnType<typeof baseProject>> = {}) {
  return { ...baseProject(), ...overrides };
}

function baseProject() {
  return {
    id: "project-1",
    name: "Ops Copilot",
    description: "Internal workflow automation",
    status: "brainstorming" as const,
    project_type: "greenfield",
    prd_format: "markdown",
    tech_stack: {},
    created_at: "2026-03-20T10:00:00Z",
    updated_at: "2026-03-20T10:00:00Z",
  };
}

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

async function resolveBrainstormAndLaunchFlow(options: {
  startDeferred: ReturnType<typeof createDeferred<BrainstormStartResponse>>;
  finalizeDeferred: ReturnType<typeof createDeferred<BrainstormFinalizeResponse>>;
  pipelineCreateDeferred: ReturnType<typeof createDeferred<PipelineCreateResponse>>;
  pipelineStartDeferred: ReturnType<typeof createDeferred<PipelineStartResponse>>;
  pipelineGetDeferred: ReturnType<typeof createDeferred<PipelineGetResponse>>;
  createdProjectId: string;
  pipelineId: string;
  projectName: string;
}): Promise<void> {
  await act(async () => {
    options.startDeferred.resolve({
      status: "success",
      data: makeSession({ project_id: options.createdProjectId }),
      meta: { request_id: "brainstorm-start", timestamp: "2026-03-20T10:05:00Z" },
    });
    await options.startDeferred.promise;
  });

  await waitFor(() => {
    expect(screen.getByText(`${options.projectName} brainstorm`)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Review execution plan" })).toBeInTheDocument();
  });

  fireEvent.click(screen.getByRole("button", { name: "Review execution plan" }));

  await waitFor(() => {
    expect(screen.getByText("Execution summary")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Launch pipeline" })).toBeInTheDocument();
  });

  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name: "Launch pipeline" }));
    options.finalizeDeferred.resolve({
      status: "success",
      data: makeSession({ status: "finalized", project_id: options.createdProjectId }),
      meta: { request_id: "brainstorm-finalize", timestamp: "2026-03-20T10:06:00Z" },
    });
    options.pipelineCreateDeferred.resolve({
      status: "success",
      data: makePipeline({ id: options.pipelineId, project_id: options.createdProjectId }),
      meta: { request_id: "pipeline-create", timestamp: "2026-03-20T10:06:05Z" },
    });
    options.pipelineStartDeferred.resolve({
      status: "success",
      data: {
        id: options.pipelineId,
        status: "running",
        timestamp: "2026-03-20T10:06:08Z",
      },
      meta: { request_id: "pipeline-start", timestamp: "2026-03-20T10:06:08Z" },
    });
    options.pipelineGetDeferred.resolve({
      status: "success",
      data: makePipeline({ id: options.pipelineId, project_id: options.createdProjectId }),
      meta: { request_id: "pipeline-get", timestamp: "2026-03-20T10:06:10Z" },
    });
    await options.finalizeDeferred.promise;
    await options.pipelineCreateDeferred.promise;
    await options.pipelineStartDeferred.promise;
    await options.pipelineGetDeferred.promise;
  });

  await waitFor(() => {
    expect(screen.getByText("Pipeline workspace")).toBeInTheDocument();
  });
}

describe("App golden path", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    usePipelineStore.getState().reset();
    useProjectStore.setState({
      projects: [],
      openProjectIds: [],
      activeProjectId: null,
    });
    useUiStore.setState({ sidebarOpen: true, activePanel: "projects", theme: "light" });

    vi.mocked(projectApi.list).mockResolvedValue({
      status: "success",
      data: [],
      meta: { request_id: "projects-list", timestamp: "2026-03-20T10:00:00Z" },
      pagination: null,
    });
    vi.mocked(pipelineApi.list).mockResolvedValue({
      status: "success",
      data: [],
      meta: { request_id: "pipelines-list", timestamp: "2026-03-20T10:00:00Z" },
      pagination: null,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    usePipelineStore.getState().reset();
    useProjectStore.setState({
      projects: [],
      openProjectIds: [],
      activeProjectId: null,
    });
    useUiStore.setState({ sidebarOpen: true, activePanel: "projects", theme: "light" });
  });

  it("supports the new-project golden path from creation through pipeline launch", async () => {
    const projectCreateDeferred = createDeferred<ProjectCreateResponse>();
    const startDeferred = createDeferred<BrainstormStartResponse>();
    const finalizeDeferred = createDeferred<BrainstormFinalizeResponse>();
    const pipelineCreateDeferred = createDeferred<PipelineCreateResponse>();
    const pipelineStartDeferred = createDeferred<PipelineStartResponse>();
    const pipelineGetDeferred = createDeferred<PipelineGetResponse>();

    vi.mocked(projectApi.create).mockReturnValue(projectCreateDeferred.promise);
    vi.mocked(brainstormApi.start).mockReturnValue(startDeferred.promise);
    vi.mocked(brainstormApi.finalize).mockReturnValue(finalizeDeferred.promise);
    vi.mocked(pipelineApi.create).mockReturnValue(pipelineCreateDeferred.promise);
    vi.mocked(pipelineApi.start).mockReturnValue(pipelineStartDeferred.promise);
    vi.mocked(pipelineApi.get).mockReturnValue(pipelineGetDeferred.promise);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("No projects yet")).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: /new project/i })[0]!);
    fireEvent.change(screen.getByLabelText(/project name/i), {
      target: { value: "Ops Copilot" },
    });
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: "Internal workflow automation" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.change(screen.getByLabelText(/product requirements/i), {
      target: { value: "Build an internal assistant for ops triage." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.click(screen.getByRole("button", { name: /quick build/i }));

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Create Project" }));
      projectCreateDeferred.resolve({
        status: "success",
        data: makeProject({ id: "project-new", name: "Ops Copilot" }),
        meta: { request_id: "project-create", timestamp: "2026-03-20T10:03:00Z" },
      });
      await projectCreateDeferred.promise;
    });

    await resolveBrainstormAndLaunchFlow({
      startDeferred,
      finalizeDeferred,
      pipelineCreateDeferred,
      pipelineStartDeferred,
      pipelineGetDeferred,
      createdProjectId: "project-new",
      pipelineId: "pipe-new",
      projectName: "Ops Copilot",
    });

    expect(useUiStore.getState().activePanel).toBe("pipeline");
    expect(useProjectStore.getState().activeProjectId).toBe("project-new");
    expect(usePipelineStore.getState().activePipelineId).toBe("pipe-new");
    expect(projectApi.create).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Ops Copilot",
        prd_source: "text",
        prd_content: "Build an internal assistant for ops triage.",
        settings: expect.objectContaining({ kickoff_flow: "brainstorm", pipeline_preset: "quick" }),
      }),
    );
  });

  it("supports the import golden path from repository analysis through pipeline launch", async () => {
    const projectCreateDeferred = createDeferred<ProjectCreateResponse>();
    const startDeferred = createDeferred<BrainstormStartResponse>();
    const finalizeDeferred = createDeferred<BrainstormFinalizeResponse>();
    const pipelineCreateDeferred = createDeferred<PipelineCreateResponse>();
    const pipelineStartDeferred = createDeferred<PipelineStartResponse>();
    const pipelineGetDeferred = createDeferred<PipelineGetResponse>();

    vi.mocked(projectApi.create).mockReturnValue(projectCreateDeferred.promise);
    vi.mocked(brainstormApi.start).mockReturnValue(startDeferred.promise);
    vi.mocked(brainstormApi.finalize).mockReturnValue(finalizeDeferred.promise);
    vi.mocked(pipelineApi.create).mockReturnValue(pipelineCreateDeferred.promise);
    vi.mocked(pipelineApi.start).mockReturnValue(pipelineStartDeferred.promise);
    vi.mocked(pipelineApi.get).mockReturnValue(pipelineGetDeferred.promise);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("No projects yet")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /import existing/i }));
    fireEvent.change(screen.getByLabelText(/project path/i), {
      target: { value: "/Users/demo/existing-app" },
    });

    vi.useFakeTimers();
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Analyze Project" }));
      await vi.advanceTimersByTimeAsync(1500);
    });
    vi.useRealTimers();

    await waitFor(() => {
      expect(screen.getByDisplayValue("existing-app")).toBeInTheDocument();
      expect(screen.getByText("Detected Stack")).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Import Project" }));
      projectCreateDeferred.resolve({
        status: "success",
        data: makeProject({
          id: "project-import",
          name: "existing-app",
          project_type: "brownfield",
        }),
        meta: { request_id: "project-import", timestamp: "2026-03-20T10:04:00Z" },
      });
      await projectCreateDeferred.promise;
    });

    await resolveBrainstormAndLaunchFlow({
      startDeferred,
      finalizeDeferred,
      pipelineCreateDeferred,
      pipelineStartDeferred,
      pipelineGetDeferred,
      createdProjectId: "project-import",
      pipelineId: "pipe-import",
      projectName: "existing-app",
    });

    expect(useUiStore.getState().activePanel).toBe("pipeline");
    expect(useProjectStore.getState().activeProjectId).toBe("project-import");
    expect(usePipelineStore.getState().activePipelineId).toBe("pipe-import");
    expect(projectApi.create).toHaveBeenCalledWith(
      expect.objectContaining({
        project_type: "brownfield",
        repository_path: "/Users/demo/existing-app",
        settings: expect.objectContaining({ kickoff_flow: "brainstorm", import_source: "local" }),
      }),
    );
  });
});