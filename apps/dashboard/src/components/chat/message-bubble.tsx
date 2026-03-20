import React from "react";
import type { Message } from "@/stores/chat-store";
import { cn } from "@/lib/utils";
import { Bot, User, ShieldCheck, AlertCircle, HelpCircle } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.type === "user";
  const isSystem = message.type === "system";
  const isAgent = message.type === "agent";
  const isClarification = message.type === "clarification";
  const isApproval = message.type === "approval";
  const isError = message.type === "error";

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <span className="text-xs text-gray-400 uppercase tracking-widest bg-gray-100/10 px-3 py-1 rounded-full backdrop-blur-sm border border-gray-100/5">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div className={cn("flex w-full mb-6", isUser ? "justify-end" : "justify-start animate-in fade-in slide-in-from-left-4 duration-500")}>
      <div className={cn("flex max-w-[85%] gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
        {/* Avatar */}
        <div className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-lg",
          isUser ? "bg-blue-600" : isAgent ? "bg-purple-600" : isError ? "bg-red-600" : "bg-gray-700"
        )}>
          {isUser ? <User size={16} className="text-white" /> : <Bot size={16} className="text-white" />}
        </div>

        {/* Bubble */}
        <div className="flex flex-col gap-1">
          {!isUser && message.agent && (
            <span className="text-xs font-medium text-gray-400 ml-1">{message.agent}</span>
          )}
          <div className={cn(
            "px-4 py-3 rounded-2xl shadow-sm backdrop-blur-md border transition-all duration-300",
            isUser 
              ? "bg-blue-600/90 text-white rounded-tr-none border-blue-500/30" 
              : isAgent 
                ? "bg-gray-800/80 text-gray-100 rounded-tl-none border-gray-700/50 hover:border-gray-600"
                : isError
                  ? "bg-red-900/40 text-red-100 border-red-700/30"
                  : "bg-gray-800/60 text-gray-200"
          )}>
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
            
            {/* Interactive Cards */}
            {(isClarification || isApproval) && (
              <div className="mt-4 pt-3 border-t border-gray-100/10 flex flex-wrap gap-2">
                {isClarification && message.meta?.options?.map((opt: string) => (
                  <button key={opt} className="px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-xs font-medium transition-colors border border-white/5">
                    {opt}
                  </button>
                ))}
                {isApproval && (
                  <>
                    <button className="px-4 py-1.5 bg-green-600/80 hover:bg-green-600 rounded-lg text-xs font-semibold text-white transition-all shadow-md">
                      Approve
                    </button>
                    <button className="px-4 py-1.5 bg-red-600/80 hover:bg-red-600 rounded-lg text-xs font-semibold text-white transition-all shadow-md">
                      Reject
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
          <span className="text-[10px] text-gray-500 mt-1 self-end opacity-0 group-hover:opacity-100 transition-opacity">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      </div>
    </div>
  );
}
