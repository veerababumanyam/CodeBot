import { useEffect } from "react";
import { agentSocket } from "@/lib/socket";
import { useAgentStore } from "@/stores/agent-store";
import type {
  AgentStatusEvent,
  AgentLogEvent,
  AgentMetricsEvent,
} from "@/types/agent";

export function useAgentStatus(
  pipelineId: string | null,
  projectId: string | null,
): void {
  useEffect(() => {
    if (!pipelineId) return;

    const { updateAgentStatus, appendLog, updateAgentMetrics } =
      useAgentStore.getState();

    const channel = projectId ? `project:${projectId}` : null;

    if (channel) {
      agentSocket.emit("subscribe", { channels: [channel] });
    }

    const handleAgentStatus = (event: AgentStatusEvent): void => {
      updateAgentStatus(event.agent_id, event.status);
    };

    const handleAgentLog = (event: AgentLogEvent): void => {
      appendLog(event.agent_id, event);
    };

    const handleAgentMetrics = (event: AgentMetricsEvent): void => {
      updateAgentMetrics(event.agent_id, {
        tokens_used: event.tokens_used,
        cost_usd: event.cost_usd,
      });
    };

    agentSocket.on("agent:status", handleAgentStatus);
    agentSocket.on("agent:log", handleAgentLog);
    agentSocket.on("agent:metrics", handleAgentMetrics);

    return () => {
      if (channel) {
        agentSocket.emit("unsubscribe", { channels: [channel] });
      }
      agentSocket.off("agent:status", handleAgentStatus);
      agentSocket.off("agent:log", handleAgentLog);
      agentSocket.off("agent:metrics", handleAgentMetrics);
    };
  }, [pipelineId, projectId]);
}
