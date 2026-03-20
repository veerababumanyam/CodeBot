import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { pipelineApi } from "@/api/pipelines";
import { projectApi } from "@/api/projects";
import { useProjectStore } from "@/stores/project-store";
import { usePipelineStore } from "@/stores/pipeline-store";
import { useUiStore } from "@/stores/ui-store";
import type { Pipeline } from "@/types/pipeline";
import { ProjectHub } from "./project-hub";

vi.mock("@/api/projects", () => ({
  projectApi: {
    list: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("@/api/pipelines", () => ({
  pipelineApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    start: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    cancel: vi.fn(),
  },
}));

vi.mock("./new-project-wizard", () => ({
  NewProjectWizard: () => <div>New project wizard</div>,
}));

vi.mock("./import-project-wizard", () => ({
  ImportProjectWizard: () => <div>Import project wizard</div>,
}));

const projects = [
  {
    id: "proj-1",
    name: "Alpha Platform",
    description: "Customer onboarding automation",
    status: "in_progress",
    project_type: "greenfield",
    prd_format: "markdown",
    tech_stack: { frontend: "React" },
    created_at: "2026-03-18T10:00:00Z",
    updated_at: "2026-03-20T10:00:00Z",
  },
  {
    id: "proj-2",
    name: "Bravo Insights",
    description: "Analytics dashboard and reporting",
    status: "completed",
    project_type: "improve",
    prd_format: "markdown",
    tech_stack: { backend: "FastAPI" },
    created_at: "2026-03-19T10:00:00Z",
    updated_at: "2026-03-19T12:00:00Z",
  },
  {
    id: "proj-3",
    name: "Charlie Ops",
    description: "Runbooks for incident response",
    status: "failed",
    project_type: "brownfield",
    prd_format: "pdf",
    tech_stack: { infra: "Terraform" },
    created_at: "2026-03-17T10:00:00Z",
    updated_at: "2026-03-18T09:00:00Z",
  },
] as const;

describe("ProjectHub", () => {
  let pipelineStatusByProject: Record<string, Pipeline["status"]>;

  beforeEach(() => {
    vi.clearAllMocks();
    pipelineStatusByProject = {
      "proj-1": "running",
      "proj-2": "completed",
      "proj-3": "failed",
    };
    useProjectStore.setState({
      projects: [],
      openProjectIds: ["proj-2"],
      activeProjectId: null,
    });
    usePipelineStore.getState().reset();
    useUiStore.setState({ sidebarOpen: true, activePanel: "projects", theme: "light" });

    vi.mocked(projectApi.list).mockResolvedValue({
      status: "success",
      data: [...projects],
      meta: { request_id: "req-1", timestamp: "2026-03-20T10:00:00Z" },
      pagination: null,
    });
    vi.mocked(pipelineApi.list).mockImplementation(async (projectId: string) => {
      const projectStatus = pipelineStatusByProject[projectId] ?? "running";

      return {
      status: "success",
      data:
        projectId === "proj-1"
          ? [
              {
                id: "pipe-1",
                project_id: "proj-1",
                mode: "quick",
                status: projectStatus,
                current_phase: "implementation",
                total_stages: 2,
                stages: [],
                config: null,
                started_at: "2026-03-20T09:55:00Z",
                completed_at: null,
                total_tokens_used: 1200,
                total_cost_usd: 0.42,
                error_message: null,
              },
            ]
          : projectId === "proj-2"
            ? [
                {
                  id: "pipe-2",
                  project_id: "proj-2",
                  mode: "full",
                  status: "completed",
                  current_phase: "review",
                  total_stages: 3,
                  stages: [],
                  config: null,
                  started_at: "2026-03-19T09:00:00Z",
                  completed_at: "2026-03-19T10:00:00Z",
                  total_tokens_used: 3000,
                  total_cost_usd: 1.24,
                  error_message: null,
                },
              ]
            : projectId === "proj-3"
              ? [
                  {
                    id: "pipe-3",
                    project_id: "proj-3",
                    mode: "full",
                    status: "failed",
                    current_phase: "testing",
                    total_stages: 3,
                    stages: [
                      {
                        id: "stage-3",
                        name: "integration_testing",
                        stage_number: 2,
                        status: "failed",
                        started_at: "2026-03-18T08:20:00Z",
                        completed_at: "2026-03-18T08:30:00Z",
                        agents: [],
                        error_message: "Payments integration timed out",
                      },
                    ],
                    config: null,
                    started_at: "2026-03-18T08:00:00Z",
                    completed_at: "2026-03-18T08:30:00Z",
                    total_tokens_used: 2200,
                    total_cost_usd: 0.93,
                    error_message: "Integration tests failed",
                  },
                ]
            : [],
      meta: { request_id: `req-${projectId}`, timestamp: "2026-03-20T10:00:00Z" },
      pagination: null,
      };
    });
  });

  afterEach(() => {
    useProjectStore.setState({
      projects: [],
      openProjectIds: [],
      activeProjectId: null,
    });
    usePipelineStore.getState().reset();
  });

  it("filters projects by search text and status", async () => {
    render(<ProjectHub />);

    await screen.findByText("Alpha Platform");

    fireEvent.change(screen.getByPlaceholderText(/search by name, description, or stack/i), {
      target: { value: "analytics" },
    });

    await waitFor(() => {
      expect(screen.getByText("Bravo Insights")).toBeInTheDocument();
    });

    expect(screen.queryByText("Alpha Platform")).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Status"), {
      target: { value: "completed" },
    });

    expect(screen.getByText("Bravo Insights")).toBeInTheDocument();
    expect(screen.queryByText("Charlie Ops")).not.toBeInTheDocument();
    expect(screen.getByText("Showing 1 of 3 projects")).toBeInTheDocument();
  });

  it("shows only open projects when requested and can reset filters", async () => {
    render(<ProjectHub />);

    await screen.findByText("Alpha Platform");

    fireEvent.click(screen.getByLabelText(/open projects only/i));

    await waitFor(() => {
      expect(screen.getByText("Bravo Insights")).toBeInTheDocument();
    });

    expect(screen.queryByText("Alpha Platform")).not.toBeInTheDocument();
    expect(screen.queryByText("Charlie Ops")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /clear filters/i }));

    await waitFor(() => {
      expect(screen.getByText("Alpha Platform")).toBeInTheDocument();
      expect(screen.getByText("Bravo Insights")).toBeInTheDocument();
      expect(screen.getByText("Charlie Ops")).toBeInTheDocument();
    });
  });

  it("shows a filtered empty state and restores results after reset", async () => {
    render(<ProjectHub />);

    await screen.findByText("Alpha Platform");

    fireEvent.change(screen.getByPlaceholderText(/search by name, description, or stack/i), {
      target: { value: "nope" },
    });

    await waitFor(() => {
      expect(screen.getByText("No matching projects")).toBeInTheDocument();
    });

    const discoveryRegion = screen.getByText("No matching projects").closest("div");
    expect(discoveryRegion).not.toBeNull();
    expect(within(discoveryRegion as HTMLElement).getByRole("button", { name: /reset project discovery/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /reset project discovery/i }));

    await waitFor(() => {
      expect(screen.getByText("Alpha Platform")).toBeInTheDocument();
      expect(screen.queryByText("No matching projects")).not.toBeInTheDocument();
    });
  });

  it("shows latest run details and can pause a project run from the card", async () => {
    vi.mocked(pipelineApi.pause).mockResolvedValue({
      status: "success",
      data: { id: "pipe-1", status: "paused", timestamp: "2026-03-20T10:02:00Z" },
      meta: { request_id: "req-pause", timestamp: "2026-03-20T10:02:00Z" },
    });
    vi.mocked(pipelineApi.get).mockResolvedValue({
      status: "success",
      data: {
        id: "pipe-1",
        project_id: "proj-1",
        mode: "quick",
        status: "paused",
        current_phase: "implementation",
        total_stages: 2,
        stages: [],
        config: null,
        started_at: "2026-03-20T09:55:00Z",
        completed_at: null,
        total_tokens_used: 1200,
        total_cost_usd: 0.42,
        error_message: null,
      },
      meta: { request_id: "req-get", timestamp: "2026-03-20T10:02:01Z" },
    });

    render(<ProjectHub />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /pause latest run for alpha platform/i })).toBeInTheDocument();
    });

    const alphaCard = screen.getByRole("button", { name: /pause latest run for alpha platform/i }).closest("div.group");
    expect(alphaCard).not.toBeNull();
    expect(within(alphaCard as HTMLElement).getByText("Latest run")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /pause latest run for alpha platform/i }));

    await waitFor(() => {
      expect(pipelineApi.pause).toHaveBeenCalledWith("pipe-1");
      expect(pipelineApi.get).toHaveBeenCalledWith("pipe-1");
      expect(screen.getByRole("button", { name: /resume latest run for alpha platform/i })).toBeInTheDocument();
    });
  });

  it("retries the failed latest run for a project and opens the new pipeline", async () => {
    vi.mocked(pipelineApi.create).mockResolvedValue({
      status: "success",
      data: {
        id: "pipe-3-retry",
        project_id: "proj-3",
        mode: "full",
        status: "pending",
        current_phase: "planning",
        total_stages: 0,
        stages: [],
        config: null,
        started_at: null,
        completed_at: null,
        total_tokens_used: 0,
        total_cost_usd: 0,
        error_message: null,
      },
      meta: { request_id: "req-create", timestamp: "2026-03-20T10:03:00Z" },
    });
    vi.mocked(pipelineApi.start).mockResolvedValue({
      status: "success",
      data: { id: "pipe-3-retry", status: "running", timestamp: "2026-03-20T10:03:01Z" },
      meta: { request_id: "req-start", timestamp: "2026-03-20T10:03:01Z" },
    });
    vi.mocked(pipelineApi.get).mockResolvedValue({
      status: "success",
      data: {
        id: "pipe-3-retry",
        project_id: "proj-3",
        mode: "full",
        status: "running",
        current_phase: "planning",
        total_stages: 2,
        stages: [],
        config: null,
        started_at: "2026-03-20T10:03:00Z",
        completed_at: null,
        total_tokens_used: 0,
        total_cost_usd: 0,
        error_message: null,
      },
      meta: { request_id: "req-get", timestamp: "2026-03-20T10:03:02Z" },
    });

    render(<ProjectHub />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /retry latest run for charlie ops/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /retry latest run for charlie ops/i }));

    await waitFor(() => {
      expect(pipelineApi.create).toHaveBeenCalledWith("proj-3", "full");
      expect(pipelineApi.start).toHaveBeenCalledWith("pipe-3-retry");
      expect(pipelineApi.get).toHaveBeenCalledWith("pipe-3-retry");
      expect(useUiStore.getState().activePanel).toBe("pipeline");
      expect(useProjectStore.getState().activeProjectId).toBe("proj-3");
      expect(usePipelineStore.getState().activePipelineId).toBe("pipe-3-retry");
    });
  });

  it("shows the latest run failure reason on project cards", async () => {
    render(<ProjectHub />);

    const retryButton = await screen.findByRole("button", {
      name: /retry latest run for charlie ops/i,
    });

    const charlieCard = retryButton.closest("div.group");
    expect(charlieCard).not.toBeNull();

    await waitFor(() => {
      expect(
        within(charlieCard as HTMLElement).getByText(/failure reason:/i),
      ).toBeInTheDocument();
      expect(
        within(charlieCard as HTMLElement).getByText(/integration tests failed/i),
      ).toBeInTheDocument();
      expect(
        within(charlieCard as HTMLElement).getByText(/failed stage:/i),
      ).toBeInTheDocument();
      expect(
        within(charlieCard as HTMLElement).getByText(/integration testing · payments integration timed out/i),
      ).toBeInTheDocument();
    });
  });

  it("refreshes latest run summaries from the hub controls", async () => {
    render(<ProjectHub />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /pause latest run for alpha platform/i })).toBeInTheDocument();
    });

    pipelineStatusByProject["proj-1"] = "completed";

    fireEvent.click(screen.getByRole("button", { name: /refresh runs/i }));

    await waitFor(() => {
      expect(pipelineApi.list).toHaveBeenCalledWith("proj-1");
      expect(screen.queryByRole("button", { name: /pause latest run for alpha platform/i })).not.toBeInTheDocument();
    });

    const alphaCardTitle = screen.getByText("Alpha Platform");
    const alphaCard = alphaCardTitle.closest("div.group");
    expect(alphaCard).not.toBeNull();
    expect(within(alphaCard as HTMLElement).getAllByText("Completed").length).toBeGreaterThan(0);
  });
});