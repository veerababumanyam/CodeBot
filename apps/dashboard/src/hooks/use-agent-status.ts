import { useEffect } from "react";
import { agentSocket } from "@/lib/socket";
import { useAgentStore } from "@/stores/agent-store";
import type {
  AgentStatusEvent,
  AgentLogEvent,
  AgentMetricsEvent,
} from "@/types/agent";

export function useAgentStatus(pipelineId: string | null): void {
  useEffect(() => {
    if (!pipelineId) return;

    const { updateAgentStatus, appendLog, updateAgentMetrics } =
      useAgentStore.getState();

    agentSocket.emit("subscribe", { pipeline_id: pipelineId });

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
      agentSocket.emit("unsubscribe", { pipeline_id: pipelineId });
      agentSocket.off("agent:status", handleAgentStatus);
      agentSocket.off("agent:log", handleAgentLog);
      agentSocket.off("agent:metrics", handleAgentMetrics);
    };
  }, [pipelineId]);
}
