import { useEffect } from "react";
import { useSocketStore } from "@/stores/socket-store";
import { useChatStore } from "@/stores/chat-store";
import type { Message } from "@/stores/chat-store";
import { useProjectStore } from "@/stores/project-store";

export function useChat() {
  const socket = useSocketStore((s: any) => s.socket);
  const activeProjectId = useProjectStore((s: any) => s.activeProjectId);
  const { addMessage, setTyping } = useChatStore();

  useEffect(() => {
    if (!socket || !activeProjectId) return;

    const handleMessage = (message: Message) => {
      addMessage(message);
    };

    const handleTyping = (data: { agent: string; typing: boolean }) => {
      setTyping(data.typing, data.agent);
    };

    // We assume the socket room joining is handled in useSocket based on activeProjectId
    socket.on("chat.message", handleMessage);
    socket.on("chat.typing", handleTyping);

    return () => {
      socket.off("chat.message", handleMessage);
      socket.off("chat.typing", handleTyping);
    };
  }, [socket, activeProjectId, addMessage, setTyping]);

  const sendMessage = (content: string) => {
    if (!socket || !activeProjectId) return;
    socket.emit("chat.send", { project_id: activeProjectId, content });
  };

  const approveGate = (gateId: string, approved: boolean) => {
    if (!socket || !activeProjectId) return;
    socket.emit("chat.approve", { project_id: activeProjectId, gate_id: gateId, approved });
  };

  return { sendMessage, approveGate };
}
