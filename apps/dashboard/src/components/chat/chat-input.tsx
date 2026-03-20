import React, { useState, useRef, useEffect } from "react";
import { Send, Hash } from "lucide-react";
import { useChat } from "@/hooks/use-chat";
import { cn } from "@/lib/utils";

export function ChatInput() {
  const [content, setContent] = useState("");
  const { sendMessage } = useChat();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!content.trim()) return;
    sendMessage(content.trim());
    setContent("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [content]);

  return (
    <div className="p-4 bg-gray-900/50 backdrop-blur-xl border-t border-gray-100/10 transition-all duration-500">
      <div className="relative max-w-4xl mx-auto group">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Architect or give instructions..."
          rows={1}
          className={cn(
            "w-full bg-gray-800/80 text-gray-100 text-sm rounded-xl py-3 pl-4 pr-12 scrollbar-none",
            "border border-gray-700/50 focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/30 transition-all",
            "placeholder:text-gray-500 resize-none max-h-48 shadow-inner"
          )}
        />
        <div className="absolute right-2 bottom-1.5 flex items-center gap-2">
          <button
            onClick={handleSend}
            disabled={!content.trim()}
            className={cn(
              "p-2 rounded-lg transition-all transform hover:scale-105 active:scale-95 shadow-lg",
              content.trim() 
                ? "bg-blue-600 text-white hover:bg-blue-500 shadow-blue-900/40" 
                : "bg-gray-700/50 text-gray-500 cursor-not-allowed"
            )}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
