import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Message } from "@/stores/chat-store";
import { MessageBubble } from "./message-bubble";

const approveGate = vi.fn();
const sendMessage = vi.fn();

vi.mock("@/hooks/use-chat", () => ({
  useChat: () => ({
    approveGate,
    sendMessage,
  }),
}));

function makeMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: "msg-1",
    type: "agent",
    content: "Pipeline review is ready.",
    agent: "Architect",
    timestamp: "2026-03-20T10:00:00Z",
    ...overrides,
  };
}

describe("MessageBubble", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders system messages as status pills", () => {
    render(
      <MessageBubble
        message={makeMessage({ type: "system", content: "Pipeline paused" })}
      />,
    );

    expect(screen.getByText("Pipeline paused")).toBeInTheDocument();
  });

  it("renders attachments and approval actions", () => {
    render(
      <MessageBubble
        message={makeMessage({
          type: "approval",
          meta: { gateId: "gate-1" },
          attachments: [
            {
              type: "file",
              url: "data:text/plain;base64,SGVsbG8=",
              name: "notes.txt",
              size: 2048,
            },
          ],
        })}
      />,
    );

    expect(screen.getByText("Architect")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /notes.txt/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
    fireEvent.click(screen.getByRole("button", { name: "Reject" }));

    expect(approveGate).toHaveBeenNthCalledWith(1, "gate-1", true);
    expect(approveGate).toHaveBeenNthCalledWith(2, "gate-1", false);
  });

  it("sends quick replies for clarification options", () => {
    render(
      <MessageBubble
        message={makeMessage({
          type: "clarification",
          meta: { options: ["Use React", "Use FastAPI"] },
        })}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Use React" }));

    expect(sendMessage).toHaveBeenCalledWith("Use React");
  });

  it("renders deterministic initials for named agents", () => {
    render(
      <MessageBubble
        message={makeMessage({
          agent: "Architecture Reviewer",
        })}
      />,
    );

    expect(screen.getByText("AR")).toBeInTheDocument();
    expect(screen.getByText("Architecture Reviewer")).toBeInTheDocument();
    expect(screen.getByText("Agent")).toBeInTheDocument();
  });

  it("disables approval actions when gate metadata is missing", () => {
    render(
      <MessageBubble
        message={makeMessage({
          type: "approval",
        })}
      />,
    );

    expect(screen.getByRole("button", { name: "Approve" })).toBeDisabled();
    expect(screen.getByText(/waiting for gate metadata/i)).toBeInTheDocument();
  });

  it("can hide repeated identity details for grouped messages", () => {
    render(
      <MessageBubble
        message={makeMessage()}
        compact
        showIdentity={false}
        showTimestamp={false}
      />,
    );

    expect(screen.queryByText("Architect")).not.toBeInTheDocument();
    expect(screen.queryByText(/10:00/i)).not.toBeInTheDocument();
    expect(screen.getByText("Pipeline review is ready.")).toBeInTheDocument();
  });
});