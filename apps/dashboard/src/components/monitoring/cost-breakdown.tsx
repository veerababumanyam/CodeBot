import { useMemo } from "react";
import { useShallow } from "zustand/react/shallow";
import { useAgentStore } from "@/stores/agent-store";
import type { Agent } from "@/types/agent";

function formatTokens(n: number): string {
  return n.toLocaleString();
}

function formatCost(usd: number): string {
  return `$${usd.toFixed(4)}`;
}

const STAGE_NAMES: Record<number, string> = {
  0: "S0 - Init",
  1: "S1 - Brainstorm",
  2: "S2 - Research",
  3: "S3 - Architecture",
  4: "S4 - Planning",
  5: "S5 - Implementation",
  6: "S6 - QA",
  7: "S7 - Testing",
  8: "S8 - Debug",
  9: "S9 - Docs",
  10: "S10 - Deploy",
};

interface GroupSummary {
  label: string;
  tokens: number;
  cost: number;
}

function groupBy(
  agents: Agent[],
  keyFn: (a: Agent) => string,
): GroupSummary[] {
  const map = new Map<string, { tokens: number; cost: number }>();
  for (const agent of agents) {
    const key = keyFn(agent);
    const existing = map.get(key);
    if (existing) {
      existing.tokens += agent.tokens_used;
      existing.cost += agent.cost_usd;
    } else {
      map.set(key, { tokens: agent.tokens_used, cost: agent.cost_usd });
    }
  }
  return Array.from(map.entries())
    .map(([label, data]) => ({ label, ...data }))
    .sort((a, b) => b.cost - a.cost);
}

function PerAgentTable({ agents }: { agents: Agent[] }): React.JSX.Element {
  const sorted = useMemo(
    () => [...agents].sort((a, b) => b.cost_usd - a.cost_usd),
    [agents],
  );
  const totalTokens = sorted.reduce((sum, a) => sum + a.tokens_used, 0);
  const totalCost = sorted.reduce((sum, a) => sum + a.cost_usd, 0);

  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-gray-700">Per Agent</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs font-medium text-gray-500">
            <th className="pb-2 pr-4">Agent Name</th>
            <th className="pb-2 pr-4 text-right">Tokens</th>
            <th className="pb-2 pr-4 text-right">Cost ($)</th>
            <th className="pb-2 text-right">Status</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((agent) => (
            <tr
              key={agent.id}
              className="border-b border-gray-100 hover:bg-gray-50"
            >
              <td className="py-2 pr-4">{agent.name}</td>
              <td className="py-2 pr-4 text-right font-mono">
                {formatTokens(agent.tokens_used)}
              </td>
              <td className="py-2 pr-4 text-right font-mono">
                {formatCost(agent.cost_usd)}
              </td>
              <td className="py-2 text-right capitalize">{agent.status}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t-2 border-gray-300 font-semibold">
            <td className="py-2 pr-4">Total</td>
            <td className="py-2 pr-4 text-right font-mono">
              {formatTokens(totalTokens)}
            </td>
            <td className="py-2 pr-4 text-right font-mono">
              {formatCost(totalCost)}
            </td>
            <td />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

function StageSummary({ agents }: { agents: Agent[] }): React.JSX.Element {
  const groups = useMemo(
    () =>
      groupBy(agents, (a) => {
        const name = STAGE_NAMES[a.stage_number];
        return name ?? `S${String(a.stage_number)}`;
      }),
    [agents],
  );

  const maxCost = Math.max(...groups.map((g) => g.cost), 0.0001);
  const totalTokens = groups.reduce((sum, g) => sum + g.tokens, 0);
  const totalCost = groups.reduce((sum, g) => sum + g.cost, 0);

  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-gray-700">Per Stage</h3>
      <div className="space-y-2">
        {groups.map((g) => (
          <div key={g.label} className="flex items-center gap-3">
            <span className="w-36 shrink-0 text-xs text-gray-600">
              {g.label}
            </span>
            <div className="flex-1">
              <div
                className="h-5 rounded bg-blue-500 transition-all"
                style={{ width: `${String((g.cost / maxCost) * 100)}%` }}
              />
            </div>
            <span className="w-20 shrink-0 text-right font-mono text-xs">
              {formatTokens(g.tokens)}
            </span>
            <span className="w-20 shrink-0 text-right font-mono text-xs">
              {formatCost(g.cost)}
            </span>
          </div>
        ))}
        <div className="flex items-center gap-3 border-t-2 border-gray-300 pt-2 font-semibold">
          <span className="w-36 shrink-0 text-xs">Total</span>
          <div className="flex-1" />
          <span className="w-20 shrink-0 text-right font-mono text-xs">
            {formatTokens(totalTokens)}
          </span>
          <span className="w-20 shrink-0 text-right font-mono text-xs">
            {formatCost(totalCost)}
          </span>
        </div>
      </div>
    </div>
  );
}

function ModelSummary({ agents }: { agents: Agent[] }): React.JSX.Element {
  const groups = useMemo(
    () => groupBy(agents, (a) => a.model ?? "unknown"),
    [agents],
  );
  const totalTokens = groups.reduce((sum, g) => sum + g.tokens, 0);
  const totalCost = groups.reduce((sum, g) => sum + g.cost, 0);

  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold text-gray-700">Per Model</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs font-medium text-gray-500">
            <th className="pb-2 pr-4">Model</th>
            <th className="pb-2 pr-4 text-right">Tokens</th>
            <th className="pb-2 text-right">Cost ($)</th>
          </tr>
        </thead>
        <tbody>
          {groups.map((g) => (
            <tr
              key={g.label}
              className="border-b border-gray-100 hover:bg-gray-50"
            >
              <td className="py-2 pr-4 font-mono">{g.label}</td>
              <td className="py-2 pr-4 text-right font-mono">
                {formatTokens(g.tokens)}
              </td>
              <td className="py-2 text-right font-mono">
                {formatCost(g.cost)}
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t-2 border-gray-300 font-semibold">
            <td className="py-2 pr-4">Total</td>
            <td className="py-2 pr-4 text-right font-mono">
              {formatTokens(totalTokens)}
            </td>
            <td className="py-2 text-right font-mono">
              {formatCost(totalCost)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

export function CostBreakdown(): React.JSX.Element {
  const agents = useAgentStore(useShallow((s) => Object.values(s.agents)));

  if (agents.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-400">
        No cost data available. Start a pipeline to see cost breakdown.
      </div>
    );
  }

  return (
    <div className="space-y-8 overflow-y-auto p-6">
      <h2 className="text-lg font-semibold text-gray-800">Cost Breakdown</h2>
      <PerAgentTable agents={agents} />
      <StageSummary agents={agents} />
      <ModelSummary agents={agents} />
    </div>
  );
}
