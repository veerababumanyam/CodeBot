import { useEffect } from "react";
import { agentSocket } from "@/lib/socket";
import { useTerminalStore } from "@/stores/terminal-store";

/**
 * Subscribes to terminal events and pushes data to the terminal store.
 * Handles terminal:data and terminal:resize, emits terminal:input.
 * Cleans up listeners on unmount.
 */
export function useTerminalSocket(sessionId: string) {
  const writeData = useTerminalStore((s) => s.writeData);
  const setResize = useTerminalStore((s) => s.setResize);

  useEffect(() => {
    const handleData = (data: { data: string }) => {
      writeData(sessionId, data.data);
    };
    const handleResize = (resize: { cols: number; rows: number }) => {
      setResize(sessionId, resize.cols, resize.rows);
    };
    agentSocket.on("terminal:data", handleData);
    agentSocket.on("terminal:resize", handleResize);
    return () => {
      agentSocket.off("terminal:data", handleData);
      agentSocket.off("terminal:resize", handleResize);
    };
  }, [sessionId, writeData, setResize]);
}
