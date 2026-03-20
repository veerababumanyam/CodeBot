import React, { useEffect, useRef } from "react";
import { MessageBubble } from "./message-bubble";
import { useChatStore } from "@/stores/chat-store";
import type { Message } from "@/stores/chat-store";
import { useSocketStore } from "@/stores/socket-store";
import { useProjectStore } from "@/stores/project-store";

function getSenderKey(message: Message): string {
  if (message.type === "system") {
    return `system:${message.id}`;
  }

  if (message.type === "user") {
    return "user";
  }

  return `agent:${message.agent ?? message.type}`;
}

function shouldGroupMessages(previous: Message | undefined, current: Message | undefined): boolean {
  if (!previous || !current) {
    return false;
  }

  if (previous.type === "system" || current.type === "system") {
    return false;
  }

  return getSenderKey(previous) === getSenderKey(current);
}

export function MessageList() {
  const messages = useChatStore((s) => s.messages);
  const isConnected = useSocketStore((s) => s.isConnected);
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const emptyStateTitle = !activeProjectId
    ? "Choose a project to start collaborating"
    : !isConnected
      ? "Reconnecting to the coordination stream"
      : "Listening for project updates...";

  const emptyStateDescription = !activeProjectId
    ? "Open a project from the workspace to send messages, approvals, and clarifications here."
    : !isConnected
      ? "We’ll resume agent conversations as soon as the workspace connection is restored."
      : "Agent conversations, approvals, and clarifications will appear here as the run unfolds.";

  return (
    <div 
      ref={scrollRef}
      className="custom-scrollbar flex-1 overflow-y-auto px-4 py-6 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-border-strong"
    >
      <div className="flex flex-col min-h-full">
        {messages.length === 0 ? (
          <div className="pointer-events-none flex flex-1 flex-col items-center justify-center rounded-[1.75rem] border border-dashed border-border bg-panel-muted px-6 py-10 text-center opacity-70">
            <div className="mb-4 h-16 w-16 animate-pulse rounded-full bg-accent-muted" />
            <p className="text-sm font-medium text-foreground">{emptyStateTitle}</p>
            <p className="mt-2 max-w-xs text-xs text-muted-foreground">
              {emptyStateDescription}
            </p>
          </div>
        ) : (
          messages.map((msg, index) => {
            const previous = index > 0 ? messages[index - 1] : undefined;
            const next = index < messages.length - 1 ? messages[index + 1] : undefined;
            const compact = shouldGroupMessages(previous, msg);
            const showTimestamp = !shouldGroupMessages(msg, next);

            return (
              <MessageBubble
                key={msg.id}
                message={msg}
                compact={compact}
                showIdentity={!compact}
                showTimestamp={showTimestamp}
              />
            );
          })
        )}
      </div>
    </div>
  );
}
