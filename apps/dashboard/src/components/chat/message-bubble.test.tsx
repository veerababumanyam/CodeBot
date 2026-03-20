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
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
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
          meta: {
            gateId: "gate-1",
            stage_name: "architecture_review",
            stage_number: 2,
            phase_type: "design_review",
            approved_by: "Project Manager",
            review_note: "Please confirm the API boundaries before implementation.",
            agents: ["Architect", "Reviewer"],
          },
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
  expect(screen.getByText("Architecture Review")).toBeInTheDocument();
  expect(screen.getByText(/stage 3 • design review/i)).toBeInTheDocument();
  expect(screen.getByText(/requested by project manager/i)).toBeInTheDocument();
  expect(screen.getByText(/2 participating agents/i)).toBeInTheDocument();
  expect(screen.getByText(/please confirm the api boundaries/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Request changes" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Approve" }));
  fireEvent.click(screen.getByRole("button", { name: "Request changes" }));

    expect(approveGate).toHaveBeenNthCalledWith(1, "gate-1", true);
    expect(approveGate).toHaveBeenNthCalledWith(2, "gate-1", false);
  });

  it("copies message text and gate ids from the action strip", async () => {
    render(
      <MessageBubble
        message={makeMessage({
          type: "approval",
          meta: { gateId: "gate-1" },
        })}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Copy message text" }));
    fireEvent.click(screen.getByRole("button", { name: "Copy gate ID" }));

    const writeText = vi.mocked(navigator.clipboard.writeText);
    expect(writeText).toHaveBeenNthCalledWith(1, "Pipeline review is ready.");
    expect(writeText).toHaveBeenNthCalledWith(2, "gate-1");
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
    expect(screen.getByRole("button", { name: "Request changes" })).toBeDisabled();
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