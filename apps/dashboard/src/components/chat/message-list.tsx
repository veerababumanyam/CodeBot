import React, { useEffect, useRef } from "react";
import { MessageBubble } from "./message-bubble";
import { useChatStore } from "@/stores/chat-store";

export function MessageList() {
  const messages = useChatStore((s) => s.messages);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div 
      ref={scrollRef}
      className="flex-1 overflow-y-auto px-4 py-6 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent custom-scrollbar"
    >
      <div className="flex flex-col min-h-full">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center opacity-30 grayscale pointer-events-none">
            <div className="w-16 h-16 bg-gray-200 rounded-full mb-4 animate-pulse" />
            <p className="text-sm font-medium">Listening for project updates...</p>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))
        )}
      </div>
    </div>
  );
}
