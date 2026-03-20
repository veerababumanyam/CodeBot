import React, { useState, useCallback, useEffect } from "react";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";
import { useChatStore } from "@/stores/chat-store";
import { ChevronRight, ChevronLeft, MessageSquare, X, GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

export function ChatSidebar() {
  const { drawerOpen, setDrawerOpen, isTyping, activeAgent, sidebarWidth, setSidebarWidth } = useChatStore();
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
        "fixed top-0 right-0 bottom-0 z-50 transition-all duration-300 ease-in-out border-l border-gray-100/10 shadow-2xl overflow-visible",
        !drawerOpen && "border-none"
      )}
    >
      {/* Resize Handle */}
      {drawerOpen && (
        <div
          onMouseDown={startResizing}
          className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize group z-50 hover:bg-blue-500/50 transition-colors"
        >
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                <GripVertical size={16} className="text-blue-400" />
            </div>
        </div>
      )}

      {/* Glass Background */}
      <div className={cn(
          "absolute inset-0 bg-gray-900/85 backdrop-blur-2xl transition-opacity duration-300",
          drawerOpen ? "opacity-100" : "opacity-0 pointer-events-none"
      )} />

      {/* Content Container */}
      <div className={cn(
          "relative h-full flex flex-col transition-transform duration-300",
          drawerOpen ? "translate-x-0" : "translate-x-full"
      )}>
        {/* Header */}
        <div className="h-14 px-6 flex items-center justify-between border-b border-white/5 bg-white/5">
          <div className="flex items-center gap-3">
            <MessageSquare size={18} className="text-blue-400" />
            <span className="text-xs font-semibold tracking-widest text-gray-100 uppercase">
              Team Coordination
            </span>
          </div>
          <button 
            onClick={() => setDrawerOpen(false)}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white"
          >
            <X size={18} />
          </button>
        </div>

        {/* Status Bar */}
        {isTyping && (
          <div className="px-6 py-2 bg-blue-500/10 border-b border-blue-500/20">
            <span className="text-[10px] text-blue-400 font-medium animate-pulse flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-ping" />
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
          className="fixed bottom-6 right-6 w-12 h-12 bg-blue-600 text-white rounded-full shadow-xl hover:bg-blue-500 hover:scale-110 active:scale-95 transition-all z-50 flex items-center justify-center group"
          title="Open Chat"
        >
          <MessageSquare size={20} className="group-hover:rotate-12 transition-transform" />
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-gray-900 animate-pulse" />
        </button>
      )}
    </div>
  );
}
