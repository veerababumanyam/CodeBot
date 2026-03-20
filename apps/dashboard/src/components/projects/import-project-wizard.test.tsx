import { act, fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  pickLocalDirectory,
  supportsDirectoryPicker,
} from "@/lib/directory-picker";
import { useProjectStore } from "@/stores/project-store";
import { ImportProjectWizard } from "./import-project-wizard";

vi.mock("@/lib/directory-picker", () => ({
  pickLocalDirectory: vi.fn(),
  supportsDirectoryPicker: vi.fn(),
}));

vi.mock("@/api/projects", () => ({
  projectApi: {
    create: vi.fn(),
  },
}));

describe("ImportProjectWizard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useProjectStore.setState({
      projects: [],
      openProjectIds: [],
      activeProjectId: null,
    });
    vi.mocked(supportsDirectoryPicker).mockReturnValue(true);
  });

  it("shows local folder browsing controls only in local mode", () => {
    render(
      <ImportProjectWizard onComplete={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(
      screen.getByRole("button", { name: /browse folder/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/project path/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /git url/i }));

    expect(
      screen.queryByRole("button", { name: /browse folder/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText(/repository url/i)).toBeInTheDocument();
  });

  it("shows picker guidance when browser folder browsing is unavailable", () => {
    vi.mocked(supportsDirectoryPicker).mockReturnValue(false);

    render(
      <ImportProjectWizard onComplete={vi.fn()} onCancel={vi.fn()} />,
    );

    expect(screen.getByRole("button", { name: /browse folder/i })).toBeDisabled();
    expect(
      screen.getByText(/folder browsing is available in supported chromium-based browsers/i),
    ).toBeInTheDocument();
  });

  it("records the selected folder name and keeps analyze disabled until a full path is entered", async () => {
    vi.mocked(pickLocalDirectory).mockResolvedValue({
      name: "existing-app",
      source: "native-picker",
    });

    render(
      <ImportProjectWizard onComplete={vi.fn()} onCancel={vi.fn()} />,
    );

    const analyzeButton = screen.getByRole("button", {
      name: /analyze project/i,
    });

    expect(analyzeButton).toBeDisabled();

    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: /browse folder/i }));
    });

    expect(await screen.findByText(/selected folder:/i)).toBeInTheDocument();
    expect(screen.getByText("existing-app")).toBeInTheDocument();
    expect(analyzeButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/project path/i), {
      target: { value: "/Users/demo/existing-app" },
    });

    expect(analyzeButton).toBeEnabled();
  });

  it("requires an absolute local path but allows any non-empty git URL", () => {
    render(
      <ImportProjectWizard onComplete={vi.fn()} onCancel={vi.fn()} />,
    );

    const analyzeButton = screen.getByRole("button", {
      name: /analyze project/i,
    });

    fireEvent.change(screen.getByLabelText(/project path/i), {
      target: { value: "existing-app" },
    });

    expect(analyzeButton).toBeDisabled();
    expect(
      screen.getByText(/enter an absolute local path/i),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /git url/i }));
    fireEvent.change(screen.getByLabelText(/repository url/i), {
      target: { value: "https://github.com/org/repo.git" },
    });

    expect(analyzeButton).toBeEnabled();
  });
});