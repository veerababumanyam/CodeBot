import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { Agent, AgentLogEvent, AgentStatus } from "@/types/agent";

const MAX_LOGS_PER_AGENT = 500;

interface AgentState {
  agents: Record<string, Agent>;
  logs: Record<string, AgentLogEvent[]>;
  selectedAgentId: string | null;
  isLoading: boolean;
  error: string | null;
}

interface AgentActions {
  setAgents: (list: Agent[]) => void;
  upsertAgent: (agent: Agent) => void;
  selectAgent: (id: string | null) => void;
  appendLog: (agentId: string, log: AgentLogEvent) => void;
  updateAgentStatus: (agentId: string, status: AgentStatus) => void;
  updateAgentMetrics: (
    agentId: string,
    metrics: { tokens_used: number; cost_usd: number },
  ) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState: AgentState = {
  agents: {},
  logs: {},
  selectedAgentId: null,
  isLoading: false,
  error: null,
};

export const useAgentStore = create<AgentState & AgentActions>()(
  devtools(
    subscribeWithSelector(
      immer((set) => ({
        ...initialState,

        setAgents: (list: Agent[]) =>
          set((state) => {
            state.agents = {};
            for (const agent of list) {
              state.agents[agent.id] = agent;
            }
          }),

        upsertAgent: (agent: Agent) =>
          set((state) => {
            state.agents[agent.id] = agent;
          }),

        selectAgent: (id: string | null) =>
          set((state) => {
            state.selectedAgentId = id;
          }),

        appendLog: (agentId: string, log: AgentLogEvent) =>
          set((state) => {
            if (!state.logs[agentId]) {
              state.logs[agentId] = [];
            }
            const agentLogs = state.logs[agentId];
            if (agentLogs) {
              agentLogs.push(log);
              if (agentLogs.length > MAX_LOGS_PER_AGENT) {
                state.logs[agentId] = agentLogs.slice(-MAX_LOGS_PER_AGENT);
              }
            }
          }),

        updateAgentStatus: (agentId: string, status: AgentStatus) =>
          set((state) => {
            const agent = state.agents[agentId];
            if (agent) {
              agent.status = status;
            }
          }),

        updateAgentMetrics: (
          agentId: string,
          metrics: { tokens_used: number; cost_usd: number },
        ) =>
          set((state) => {
            const agent = state.agents[agentId];
            if (agent) {
              agent.tokens_used = metrics.tokens_used;
              agent.cost_usd = metrics.cost_usd;
            }
          }),

        setLoading: (loading: boolean) =>
          set((state) => {
            state.isLoading = loading;
          }),

        setError: (error: string | null) =>
          set((state) => {
            state.error = error;
          }),

        reset: () =>
          set((state) => {
            state.agents = initialState.agents;
            state.logs = initialState.logs;
            state.selectedAgentId = initialState.selectedAgentId;
            state.isLoading = initialState.isLoading;
            state.error = initialState.error;
          }),
      })),
    ),
    { name: "AgentStore" },
  ),
);
