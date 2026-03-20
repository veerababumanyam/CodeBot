import { useEffect } from "react";
import { agentSocket } from "@/lib/socket";
import { useOperatorStore } from "@/stores/operator-store";

/**
 * Subscribes to operator events and pushes data to the operator store.
 * Handles operator:action and operator:status events.
 * Cleans up listeners on unmount.
 */
export function useOperatorSocket(projectId: string) {
  const addAction = useOperatorStore((s) => s.addAction);
  const setStatus = useOperatorStore((s) => s.setStatus);

  useEffect(() => {
    if (!projectId) return;
    const handleAction = (data: { action: string; payload: any }) => {
      addAction(projectId, data.action, data.payload);
    };
    const handleStatus = (data: { status: string; detail?: string }) => {
      setStatus(projectId, data.status, data.detail);
    };
    agentSocket.on("operator:action", handleAction);
    agentSocket.on("operator:status", handleStatus);
    return () => {
      agentSocket.off("operator:action", handleAction);
      agentSocket.off("operator:status", handleStatus);
    };
  }, [projectId, addAction, setStatus]);
}
