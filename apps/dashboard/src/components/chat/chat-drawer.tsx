import React from "react";
import { MessageList } from "./message-list";
import { ChatInput } from "./chat-input";
import { useChatStore } from "@/stores/chat-store";
import { ChevronDown, ChevronUp, MessageSquare, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";

export function ChatDrawer() {
  const { drawerOpen, setDrawerOpen, isTyping, activeAgent } = useChatStore();

  return (
    <div 
      className={cn(
        "fixed bottom-0 left-0 right-0 z-50 transition-all duration-500 cubic-bezier(0.4, 0, 0.2, 1) border-t border-gray-100/10 shadow-2xl",
        drawerOpen ? "h-[450px]" : "h-12"
      )}
    >
      {/* Glass Background */}
      <div className="absolute inset-0 bg-gray-900/85 backdrop-blur-2xl" />

      {/* Header / Toggle */}
      <div 
        onClick={() => setDrawerOpen(!drawerOpen)}
        className="relative h-12 px-6 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors group select-none"
      >
        <div className="flex items-center gap-3">
          <div className="relative">
            <MessageSquare size={18} className="text-blue-400 group-hover:scale-110 transition-transform" />
            {isTyping && (
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-ping" />
            )}
          </div>
          <span className="text-xs font-semibold tracking-widest text-gray-400 uppercase">
            Team Coordination
          </span>
          {isTyping && (
            <span className="text-[10px] text-green-400/80 font-medium animate-pulse flex items-center gap-1.5 ml-2">
              <span className="w-1 h-1 bg-green-400 rounded-full" />
              {activeAgent || "Agent"} is thinking...
            </span>
          )}
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex gap-1">
             <div className="w-2 h-2 rounded-full bg-red-500/20 group-hover:bg-red-500/40 transition-colors" />
             <div className="w-2 h-2 rounded-full bg-yellow-500/20 group-hover:bg-yellow-500/40 transition-colors" />
             <div className="w-2 h-2 rounded-full bg-green-500/20 group-hover:bg-green-500/40 transition-colors" />
          </div>
          {drawerOpen ? <ChevronDown size={18} className="text-gray-500" /> : <ChevronUp size={18} className="text-gray-500" />}
        </div>
      </div>

      {/* Content */}
      {drawerOpen && (
        <div className="relative h-[calc(450px-48px)] flex flex-col">
          <MessageList />
          <ChatInput />
        </div>
      )}
    </div>
  );
}
