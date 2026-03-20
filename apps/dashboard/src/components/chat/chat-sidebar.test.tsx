import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useChatStore } from "@/stores/chat-store";
import { useSocketStore } from "@/stores/socket-store";
import { ChatSidebar } from "./chat-sidebar";

vi.mock("./message-list", () => ({
  MessageList: () => <div>Message list</div>,
}));

vi.mock("./chat-input", () => ({
  ChatInput: () => <div>Chat input</div>,
}));

describe("ChatSidebar", () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      drawerOpen: true,
      sidebarWidth: 400,
      isTyping: false,
      activeAgent: null,
    });
    useSocketStore.setState({ isConnected: true });
  });

  it("shows the collaboration header and can close and reopen the drawer", () => {
    render(<ChatSidebar />);

    expect(screen.getByText("Team Coordination")).toBeInTheDocument();
    expect(screen.getByText("Message list")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /close chat sidebar/i }));

    expect(screen.getByRole("button", { name: /open chat sidebar/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /open chat sidebar/i }));

    expect(screen.getByText("Team Coordination")).toBeInTheDocument();
  });

  it("renders typing status with the active agent name", () => {
    useChatStore.setState({ isTyping: true, activeAgent: "Architect" });

    render(<ChatSidebar />);

    expect(screen.getByText(/architect is typing/i)).toBeInTheDocument();
  });

  it("shows reconnecting status when the socket is offline", () => {
    useSocketStore.setState({ isConnected: false });

    render(<ChatSidebar />);

    expect(screen.getByText("Reconnecting")).toBeInTheDocument();
  });

  it("shows a clear conversation action when messages exist", () => {
    useChatStore.setState({
      messages: [
        {
          id: "msg-1",
          type: "agent",
          content: "Hello",
          timestamp: "2026-03-20T10:00:00Z",
        },
      ],
    });

    render(<ChatSidebar />);

    fireEvent.click(screen.getByRole("button", { name: /clear conversation/i }));

    expect(useChatStore.getState().messages).toEqual([]);
  });
});