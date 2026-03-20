import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useProjectStore } from "@/stores/project-store";
import { useSocketStore } from "@/stores/socket-store";
import { ChatInput } from "./chat-input";

const sendMessage = vi.fn();

vi.mock("@/hooks/use-chat", () => ({
  useChat: () => ({
    sendMessage,
  }),
}));

describe("ChatInput", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useProjectStore.setState({
      projects: [],
      openProjectIds: ["proj-1"],
      activeProjectId: "proj-1",
    });
    useSocketStore.setState({ isConnected: true });
  });

  it("shows slash command suggestions and inserts a selected prompt", () => {
    render(<ChatInput />);

    const input = screen.getByPlaceholderText("Ask Architect...");
    fireEvent.change(input, { target: { value: "/" } });

    expect(screen.getByText("Quick prompts")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /insert status update prompt/i }));

    expect(screen.getByDisplayValue(/give me a concise status update/i)).toBeInTheDocument();
  });

  it("uses the top slash command on Enter and sends on the next Enter", () => {
    render(<ChatInput />);

    const input = screen.getByPlaceholderText("Ask Architect...");
    fireEvent.change(input, { target: { value: "/ris" } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(screen.getByDisplayValue(/list the current risks, approvals/i)).toBeInTheDocument();
    expect(sendMessage).not.toHaveBeenCalled();

    fireEvent.keyDown(input, { key: "Enter" });

    expect(sendMessage).toHaveBeenCalledWith(
      "List the current risks, approvals, or missing inputs that could slow this project down.",
      [],
    );
  });
});