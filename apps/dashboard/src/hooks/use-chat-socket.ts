import { useEffect } from "react";
import { useSocketStore } from "@/stores/socket-store";
import { useChatStore } from "@/stores/chat-store";
import type { Message } from "@/stores/chat-store";
import { useProjectStore } from "@/stores/project-store";

/**
 * Subscribes to all chat-related socket events for the active project.
 * Handles chat.message, chat.typing, chat.approval, and cleans up listeners on unmount.
 * Scopes events by project ID to avoid cross-project bleed.
 */
export function useChatSocket() {
  const socket = useSocketStore((s) => s.socket);
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const { addMessage, setTyping, setApproval } = useChatStore();

  useEffect(() => {
    if (!socket || !activeProjectId) return;

    const handleMessage = (message: Message) => {
      addMessage(message);
    };

    const handleTyping = (data: { agent: string; typing: boolean }) => {
      setTyping(data.typing, data.agent);
    };

    const handleApproval = (data: { gate_id: string; stage: string; description: string }) => {
      setApproval?.(data.gate_id, data.stage, data.description);
    };

    socket.on("chat.message", handleMessage);
    socket.on("chat.typing", handleTyping);
    socket.on("chat.approval", handleApproval);

    return () => {
      socket.off("chat.message", handleMessage);
      socket.off("chat.typing", handleTyping);
      socket.off("chat.approval", handleApproval);
    };
  }, [socket, activeProjectId, addMessage, setTyping, setApproval]);
}
