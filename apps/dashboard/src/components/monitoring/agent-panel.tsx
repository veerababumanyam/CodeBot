import { useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { useAgentStore } from "@/stores/agent-store";
import { LogViewer } from "./log-viewer";
import type { Agent, AgentStatus } from "@/types/agent";

const EMPTY_LOGS: never[] = [];

const STATUS_COLORS: Record<AgentStatus, string> = {
  idle: "bg-gray-400",
  initializing: "bg-yellow-400",
  executing: "bg-blue-400",
  reviewing: "bg-purple-400",
  completed: "bg-green-400",
  failed: "bg-red-400",
  recovering: "bg-orange-400",
  terminated: "bg-gray-600",
};

const STATUS_TEXT_COLORS: Record<AgentStatus, string> = {
  idle: "text-gray-600",
  initializing: "text-yellow-700",
  executing: "text-blue-700",
  reviewing: "text-purple-700",
  completed: "text-green-700",
  failed: "text-red-700",
  recovering: "text-orange-700",
  terminated: "text-gray-700",
};

type Tab = "status" | "logs" | "metrics";

function formatCost(usd: number): string {
  return `$${usd.toFixed(4)}`;
}

function formatTokens(n: number): string {
  return n.toLocaleString();
}

function AgentCard({
  agent,
  isSelected,
  onSelect,
}: {
  agent: Agent;
  isSelected: boolean;
  onSelect: () => void;
}): React.JSX.Element {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-lg border p-3 text-left transition-all hover:shadow-sm ${
        isSelected
          ? "ring-2 ring-blue-500 border-blue-300 bg-blue-50"
          : "border-gray-200 bg-white hover:border-gray-300"
      }`}
    >
      <div className="flex items-center justify-between">
        <span className="font-medium text-sm">{agent.name}</span>
        <span
          className={`flex items-center gap-1.5 text-xs ${STATUS_TEXT_COLORS[agent.status]}`}
        >
          <span
            className={`inline-block h-2 w-2 rounded-full ${STATUS_COLORS[agent.status]}`}
          />
          {agent.status}
        </span>
      </div>
      <div className="mt-1 flex items-center gap-3 text-xs text-gray-500">
        <span>{agent.agent_type}</span>
        <span>{formatTokens(agent.tokens_used)} tokens</span>
        <span>{formatCost(agent.cost_usd)}</span>
      </div>
    </button>
  );
}

function DetailPanel({
  agent,
  tab,
  onTabChange,
}: {
  agent: Agent;
  tab: Tab;
  onTabChange: (t: Tab) => void;
}): React.JSX.Element {
  const logs = useAgentStore((s) => s.logs[agent.id] ?? EMPTY_LOGS);

  const tabs: Tab[] = ["status", "logs", "metrics"];

  const executionTimeMs =
    agent.started_at && agent.completed_at
      ? new Date(agent.completed_at).getTime() -
        new Date(agent.started_at).getTime()
      : null;

  return (
    <div className="flex flex-col h-full">
      <div className="flex gap-1 border-b border-gray-200 px-4 pt-3">
        {tabs.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => onTabChange(t)}
            className={`rounded-t-md px-4 py-2 text-sm font-medium capitalize transition-colors ${
              tab === t
                ? "border-b-2 border-blue-500 text-blue-700"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-auto p-4">
        {tab === "status" && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <span className="text-xs font-medium text-gray-500">Name</span>
              <p className="text-sm">{agent.name}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500">Type</span>
              <p className="text-sm">{agent.agent_type}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500">Model</span>
              <p className="text-sm">{agent.model ?? "N/A"}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500">Status</span>
              <p className="flex items-center gap-1.5 text-sm">
                <span
                  className={`inline-block h-2 w-2 rounded-full ${STATUS_COLORS[agent.status]}`}
                />
                {agent.status}
              </p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500">
                Started At
              </span>
              <p className="text-sm">
                {agent.started_at
                  ? new Date(agent.started_at).toLocaleString()
                  : "N/A"}
              </p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500">
                Tokens Used
              </span>
              <p className="text-sm">{formatTokens(agent.tokens_used)}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500">Cost</span>
              <p className="text-sm">{formatCost(agent.cost_usd)}</p>
            </div>
            <div>
              <span className="text-xs font-medium text-gray-500">Stage</span>
              <p className="text-sm">S{String(agent.stage_number)}</p>
            </div>
          </div>
        )}

        {tab === "logs" && <LogViewer logs={logs} maxHeight="calc(100vh - 300px)" />}

        {tab === "metrics" && (
          <div className="grid grid-cols-3 gap-6">
            <div className="rounded-lg border border-gray-200 p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">
                {formatTokens(agent.tokens_used)}
              </p>
              <p className="mt-1 text-xs text-gray-500">Tokens Used</p>
            </div>
            <div className="rounded-lg border border-gray-200 p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">
                {formatCost(agent.cost_usd)}
              </p>
              <p className="mt-1 text-xs text-gray-500">Cost (USD)</p>
            </div>
            <div className="rounded-lg border border-gray-200 p-4 text-center">
              <p className="text-2xl font-bold text-gray-900">
                {executionTimeMs !== null
                  ? `${(executionTimeMs / 1000).toFixed(1)}s`
                  : "N/A"}
              </p>
              <p className="mt-1 text-xs text-gray-500">Execution Time</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function AgentPanel(): React.JSX.Element {
  const agents = useAgentStore(useShallow((s) => Object.values(s.agents)));
  const selectedAgentId = useAgentStore((s) => s.selectedAgentId);
  const selectAgent = useAgentStore((s) => s.selectAgent);
  const [activeTab, setActiveTab] = useState<Tab>("status");

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) ?? null;

  return (
    <div className="flex h-full">
      {/* Agent list */}
      <div className="w-80 shrink-0 overflow-y-auto border-r border-gray-200 p-3 space-y-2">
        <h2 className="mb-3 text-sm font-semibold text-gray-700">
          Agents ({String(agents.length)})
        </h2>
        {agents.length === 0 && (
          <p className="text-sm text-gray-400">No agents available</p>
        )}
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            isSelected={agent.id === selectedAgentId}
            onSelect={() => selectAgent(agent.id)}
          />
        ))}
      </div>

      {/* Detail panel */}
      <div className="flex-1">
        {selectedAgent ? (
          <DetailPanel
            agent={selectedAgent}
            tab={activeTab}
            onTabChange={setActiveTab}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">
            Select an agent to view details
          </div>
        )}
      </div>
    </div>
  );
}
