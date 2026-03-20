import React, { useState, useCallback, useEffect } from "react";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";
import { useChatStore } from "@/stores/chat-store";
import { useChatSocket } from "@/hooks/use-chat-socket";
import { useSocketStore } from "@/stores/socket-store";
import { MessageSquare, RotateCcw, X, GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

export function ChatSidebar() {
  useChatSocket();
  const {
    drawerOpen,
    setDrawerOpen,
    isTyping,
    activeAgent,
    sidebarWidth,
    setSidebarWidth,
    clearMessages,
    messages,
  } = useChatStore();
  const isConnected = useSocketStore((s) => s.isConnected);
  const [isResizing, setIsResizing] = useState(false);

  const startResizing = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback(
    (e: MouseEvent) => {
      if (isResizing) {
        const newWidth = window.innerWidth - e.clientX;
        if (newWidth >= 300 && newWidth <= 800) {
          setSidebarWidth(newWidth);
        }
      }
    },
    [isResizing, setSidebarWidth]
  );

  useEffect(() => {
    if (isResizing) {
      window.addEventListener("mousemove", resize);
      window.addEventListener("mouseup", stopResizing);
    } else {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    }
    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  return (
    <div
      style={{ width: drawerOpen ? sidebarWidth : 0 }}
      className={cn(
        "fixed top-0 right-0 bottom-0 z-50 overflow-visible border-l border-border transition-all duration-300 ease-in-out",
        !drawerOpen && "border-none"
      )}
    >
      {/* Resize Handle */}
      {drawerOpen && (
        <div
          onMouseDown={startResizing}
          className="group absolute left-0 top-0 bottom-0 z-50 w-1 cursor-col-resize transition-colors hover:bg-accent/40"
        >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                <GripVertical size={16} className="text-accent" />
            </div>
        </div>
      )}

      {/* Glass Background */}
      <div className={cn(
          "absolute inset-0 bg-panel-strong/95 backdrop-blur-2xl transition-opacity duration-300 dark:bg-panel-strong/90",
          drawerOpen ? "opacity-100" : "opacity-0 pointer-events-none"
      )} />

      {/* Content Container */}
      <div className={cn(
          "relative h-full flex flex-col transition-transform duration-300",
          drawerOpen ? "translate-x-0" : "translate-x-full"
      )}>
        {/* Header */}
        <div className="flex h-16 items-center justify-between border-b border-border bg-panel-muted px-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-accent-muted text-accent shadow-[var(--theme-shadow-panel)]">
              <MessageSquare size={18} />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                Collaboration lane
              </p>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-foreground">
              Team Coordination
                </span>
                <span
                  className={cn(
                    "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold",
                    isConnected
                      ? "bg-success-muted text-success"
                      : "bg-warning-muted text-warning",
                  )}
                  aria-live="polite"
                >
                  {isConnected ? "Live" : "Reconnecting"}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                type="button"
                onClick={clearMessages}
                aria-label="Clear conversation"
                className="rounded-full border border-border bg-panel p-2 text-muted-foreground transition-colors hover:border-border-strong hover:bg-panel-muted hover:text-foreground"
              >
                <RotateCcw size={16} />
              </button>
            )}
            <button 
              onClick={() => setDrawerOpen(false)}
              aria-label="Close chat sidebar"
              className="rounded-full border border-border bg-panel p-2 text-muted-foreground transition-colors hover:border-border-strong hover:bg-panel-muted hover:text-foreground"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Status Bar */}
        {isTyping && (
          <div className="border-b border-border bg-accent-muted px-5 py-2.5">
            <span className="flex items-center gap-2 text-[11px] font-medium text-accent animate-pulse">
              <span className="h-1.5 w-1.5 rounded-full bg-accent animate-ping" />
              {activeAgent || "Agent"} is typing...
            </span>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <MessageList />
          <ChatInput />
        </div>
      </div>

      {/* Floating Toggle Button (Visible when closed) */}
      {!drawerOpen && (
        <button
          onClick={() => setDrawerOpen(true)}
          aria-label="Open chat sidebar"
          className="group fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full bg-accent text-accent-foreground shadow-[var(--theme-shadow-floating)] transition-all hover:scale-110 hover:brightness-105 active:scale-95"
          title="Open Chat"
        >
          <MessageSquare size={20} className="group-hover:rotate-12 transition-transform" />
          <div className="absolute -top-1 -right-1 h-3 w-3 rounded-full border-2 border-panel-strong bg-danger animate-pulse" />
        </button>
      )}
    </div>
  );
}
