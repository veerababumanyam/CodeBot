import React from "react";
import { useChat } from "@/hooks/use-chat";
import type { Message } from "@/stores/chat-store";
import { cn } from "@/lib/utils";
import { Bot, CircleAlert, FileText, HelpCircle, ShieldCheck, User } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
  compact?: boolean;
  showIdentity?: boolean;
  showTimestamp?: boolean;
}

const AGENT_IDENTITY_STYLES = [
  {
    avatarClassName: "bg-accent text-accent-foreground",
    labelClassName: "border border-accent/20 bg-accent-muted text-accent",
    bubbleClassName: "border-accent/20",
  },
  {
    avatarClassName: "bg-success text-white",
    labelClassName: "border border-success/20 bg-success-muted text-success",
    bubbleClassName: "border-success/20",
  },
  {
    avatarClassName: "bg-warning text-black",
    labelClassName: "border border-warning/20 bg-warning-muted text-warning",
    bubbleClassName: "border-warning/20",
  },
  {
    avatarClassName: "bg-danger text-white",
    labelClassName: "border border-danger/20 bg-danger-muted text-danger",
    bubbleClassName: "border-danger/20",
  },
  {
    avatarClassName: "bg-panel text-foreground border border-border",
    labelClassName: "border border-border bg-panel-muted text-foreground",
    bubbleClassName: "border-border-strong",
  },
] as const;

function hashString(value: string): number {
  return Array.from(value).reduce((hash, char) => hash + char.charCodeAt(0), 0);
}

function getAgentInitials(agentName?: string): string {
  if (!agentName) {
    return "AI";
  }

  const parts = agentName
    .split(/\s+/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length === 0) {
    return "AI";
  }

  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

function getAgentIdentityStyle(agentName?: string) {
  if (!agentName) {
    return AGENT_IDENTITY_STYLES[0];
  }

  return (
    AGENT_IDENTITY_STYLES[hashString(agentName) % AGENT_IDENTITY_STYLES.length] ??
    AGENT_IDENTITY_STYLES[0]
  );
}

function getMessageContext(message: Message): {
  label: string;
  icon: React.ReactNode;
  badgeClassName: string;
} | null {
  switch (message.type) {
    case "approval":
      return {
        label: "Approval",
        icon: <ShieldCheck size={12} />,
        badgeClassName: "bg-success-muted text-success",
      };
    case "clarification":
      return {
        label: "Clarification",
        icon: <HelpCircle size={12} />,
        badgeClassName: "bg-warning-muted text-warning",
      };
    case "error":
      return {
        label: "Issue",
        icon: <CircleAlert size={12} />,
        badgeClassName: "bg-danger-muted text-danger",
      };
    default:
      return null;
  }
}

export function MessageBubble({
  message,
  compact = false,
  showIdentity = true,
  showTimestamp = true,
}: MessageBubbleProps) {
  const { approveGate, sendMessage } = useChat();
  const isUser = message.type === "user";
  const isSystem = message.type === "system";
  const isAgent = message.type === "agent";
  const isClarification = message.type === "clarification";
  const isApproval = message.type === "approval";
  const isError = message.type === "error";
  const clarificationOptions = Array.isArray(message.meta?.options)
    ? (message.meta.options as string[])
    : [];
  const gateId =
    typeof message.meta?.gateId === "string"
      ? message.meta.gateId
      : typeof message.meta?.gate_id === "string"
        ? message.meta.gate_id
        : null;
  const context = getMessageContext(message);
  const agentInitials = getAgentInitials(message.agent);
  const agentIdentityStyle = getAgentIdentityStyle(message.agent);

  function handleQuickReply(option: string): void {
    sendMessage(option);
  }

  function handleApproval(approved: boolean): void {
    if (!gateId) {
      return;
    }

    approveGate(gateId, approved);
  }

  if (isSystem) {
    return (
      <div className="my-4 flex justify-center">
        <span className="rounded-full border border-border bg-panel-muted px-3 py-1 text-xs uppercase tracking-widest text-muted-foreground backdrop-blur-sm shadow-[var(--theme-shadow-panel)]">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "group flex w-full",
        compact ? "mb-2" : "mb-6",
        isUser ? "justify-end" : "justify-start animate-in fade-in slide-in-from-left-4 duration-500",
      )}
    >
      <div className={cn("flex max-w-[85%] gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
        {/* Avatar */}
        {showIdentity ? (
          <div
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-full shadow-[var(--theme-shadow-panel)]",
              isUser
                ? "bg-accent text-accent-foreground"
                : message.agent
                  ? agentIdentityStyle.avatarClassName
                  : isAgent
                    ? "bg-success text-white"
                    : isError
                      ? "bg-danger text-white"
                      : "bg-panel text-foreground",
            )}
            aria-hidden="true"
            title={message.agent ?? (isUser ? "You" : "Agent")}
          >
            {isUser ? (
              <User size={16} />
            ) : message.agent ? (
              <span className="text-[10px] font-semibold uppercase tracking-wide">{agentInitials}</span>
            ) : (
              <Bot size={16} />
            )}
          </div>
        ) : (
          <div className="w-8 shrink-0" aria-hidden="true" />
        )}

        {/* Bubble */}
        <div className="flex flex-col gap-1">
          {showIdentity && !isUser && message.agent && (
            <div className="ml-1 flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground">{message.agent}</span>
              <span
                className={cn(
                  "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                  agentIdentityStyle.labelClassName,
                )}
              >
                Agent
              </span>
            </div>
          )}
          <div
            className={cn(
              "rounded-2xl border px-4 py-3 shadow-[var(--theme-shadow-panel)] backdrop-blur-md transition-all duration-300",
              compact && (isUser ? "rounded-tr-xl" : "rounded-tl-xl"),
              isUser
                ? "rounded-tr-none border-transparent bg-accent text-accent-foreground shadow-[var(--theme-shadow-floating)]"
                : isAgent
                  ? ["rounded-tl-none bg-panel-strong text-foreground hover:border-border-strong", agentIdentityStyle.bubbleClassName]
                  : isError
                    ? "border-danger bg-danger-muted text-danger"
                    : "border-border bg-panel text-foreground",
            )}
          >
            {context && (
              <div className="mb-2 flex items-center gap-2">
                <span className={cn("inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide", context.badgeClassName)}>
                  {context.icon}
                  {context.label}
                </span>
              </div>
            )}
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>

            {/* Attachments */}
            {message.attachments && message.attachments.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {message.attachments.map((att, i) => (
                  <div key={i} className="max-w-full">
                    {att.type === "image" ? (
                      <div className="group/img relative cursor-pointer overflow-hidden rounded-xl border border-border bg-panel-muted shadow-inner backdrop-blur-sm">
                        <img src={att.url} alt={att.name} className="max-h-60 object-contain transition-transform hover:scale-[1.02]" />
                        <div className="absolute inset-0 flex items-center justify-center bg-background/45 opacity-0 transition-opacity group-hover/img:opacity-100">
                          <span className="rounded-full bg-panel-strong px-2 py-1 text-[10px] text-foreground backdrop-blur-md">View Original</span>
                        </div>
                      </div>
                    ) : (
                      <a 
                        href={att.url} 
                        download={att.name}
                        className="group/file flex items-center gap-2 rounded-xl border border-border bg-panel-muted px-3 py-2 transition-all hover:border-border-strong hover:bg-panel"
                      >
                        <div className="rounded-lg bg-accent-muted p-1.5 text-accent transition-colors group-hover/file:bg-accent-muted/80">
                          <FileText size={16} />
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="text-xs font-medium truncate max-w-[150px]">{att.name}</span>
                          {att.size && <span className="text-[10px] text-muted-foreground">{(att.size / 1024).toFixed(1)} KB</span>}
                        </div>
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
            
            {/* Interactive Cards */}
            {(isClarification || isApproval) && (
              <div className="mt-4 flex flex-wrap gap-2 border-t border-border pt-3">
                {isClarification && clarificationOptions.map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => handleQuickReply(opt)}
                    className="rounded-lg border border-border bg-panel-muted px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:border-border-strong hover:bg-panel"
                  >
                    {opt}
                  </button>
                ))}
                {isApproval && (
                  <>
                    <button
                      type="button"
                      onClick={() => handleApproval(true)}
                      disabled={!gateId}
                      className="rounded-lg bg-success px-4 py-1.5 text-xs font-semibold text-white transition-all shadow-[var(--theme-shadow-panel)] hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      onClick={() => handleApproval(false)}
                      disabled={!gateId}
                      className="rounded-lg bg-danger px-4 py-1.5 text-xs font-semibold text-white transition-all shadow-[var(--theme-shadow-panel)] hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Reject
                    </button>
                    {!gateId && (
                      <span className="self-center text-[10px] text-muted-foreground">
                        Waiting for gate metadata
                      </span>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
          {showTimestamp && (
            <span className="mt-1 self-end text-[10px] text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
