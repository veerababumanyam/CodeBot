import { useEffect } from "react";
import { connectSockets, disconnectSockets, socket } from "@/lib/socket";
import { useProjectStore } from "@/stores/project-store";

export function useSocket(): void {
  const activeProjectId = useProjectStore((s) => s.activeProjectId);

  useEffect(() => {
    connectSockets();
    return () => {
      disconnectSockets();
    };
  }, []);

  useEffect(() => {
    if (!activeProjectId) {
      return;
    }

    const channel = `project:${activeProjectId}`;
    socket.emit("subscribe", { channels: [channel] });

    return () => {
      socket.emit("unsubscribe", { channels: [channel] });
    };
  }, [activeProjectId]);
}
