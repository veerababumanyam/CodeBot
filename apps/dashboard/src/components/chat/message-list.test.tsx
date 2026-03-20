import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useChatStore } from "@/stores/chat-store";
import { useProjectStore } from "@/stores/project-store";
import { useSocketStore } from "@/stores/socket-store";
import { MessageList } from "./message-list";

vi.mock("./message-bubble", () => ({
  MessageBubble: ({
    message,
    compact,
    showIdentity,
    showTimestamp,
  }: {
    message: { id: string; content: string };
    compact?: boolean;
    showIdentity?: boolean;
    showTimestamp?: boolean;
  }) => (
    <div data-testid={message.id} data-compact={String(Boolean(compact))} data-show-identity={String(Boolean(showIdentity))} data-show-timestamp={String(Boolean(showTimestamp))}>
      {message.content}
    </div>
  ),
}));

describe("MessageList", () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      drawerOpen: true,
      sidebarWidth: 400,
      isTyping: false,
      activeAgent: null,
    });
    useProjectStore.setState({
      projects: [],
      openProjectIds: [],
      activeProjectId: null,
    });
    useSocketStore.setState({ isConnected: true });
  });

  it("shows a project-selection empty state when no project is active", () => {
    render(<MessageList />);

    expect(
      screen.getByText(/choose a project to start collaborating/i),
    ).toBeInTheDocument();
  });

  it("shows a reconnecting empty state when the socket is offline", () => {
    useProjectStore.setState({
      activeProjectId: "proj-1",
      projects: [],
      openProjectIds: [],
    });
    useSocketStore.setState({ isConnected: false });

    render(<MessageList />);

    expect(
      screen.getByText(/reconnecting to the coordination stream/i),
    ).toBeInTheDocument();
  });

  it("renders messages when the conversation has content", () => {
    useChatStore.setState({
      messages: [
        {
          id: "msg-1",
          type: "agent",
          content: "Architecture review ready",
          timestamp: "2026-03-20T10:00:00Z",
        },
      ],
    });

    render(<MessageList />);

    expect(screen.getByText("Architecture review ready")).toBeInTheDocument();
  });

  it("groups consecutive messages from the same agent", () => {
    useProjectStore.setState({
      activeProjectId: "proj-1",
      projects: [],
      openProjectIds: [],
    });
    useChatStore.setState({
      messages: [
        {
          id: "msg-1",
          type: "agent",
          agent: "Architect",
          content: "First update",
          timestamp: "2026-03-20T10:00:00Z",
        },
        {
          id: "msg-2",
          type: "approval",
          agent: "Architect",
          content: "Need approval",
          timestamp: "2026-03-20T10:01:00Z",
        },
        {
          id: "msg-3",
          type: "user",
          content: "Ship it",
          timestamp: "2026-03-20T10:02:00Z",
        },
      ],
    });

    render(<MessageList />);

    expect(screen.getByTestId("msg-1")).toHaveAttribute("data-compact", "false");
    expect(screen.getByTestId("msg-1")).toHaveAttribute("data-show-identity", "true");
    expect(screen.getByTestId("msg-1")).toHaveAttribute("data-show-timestamp", "false");
    expect(screen.getByTestId("msg-2")).toHaveAttribute("data-compact", "true");
    expect(screen.getByTestId("msg-2")).toHaveAttribute("data-show-identity", "false");
    expect(screen.getByTestId("msg-2")).toHaveAttribute("data-show-timestamp", "true");
    expect(screen.getByTestId("msg-3")).toHaveAttribute("data-compact", "false");
  });
});