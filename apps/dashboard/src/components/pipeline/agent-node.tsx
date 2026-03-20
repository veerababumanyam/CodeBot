import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import type { AgentStatus } from "@/types/agent";

export interface AgentNodeData {
  label: string;
  agentType: string;
  status: AgentStatus;
  stageNumber: number;
  [key: string]: unknown;
}

const STATUS_COLORS: Record<AgentStatus, string> = {
  idle: "border-gray-300 bg-gray-50",
  initializing: "border-blue-300 bg-blue-50",
  executing: "border-blue-500 bg-blue-100 animate-pulse",
  reviewing: "border-amber-400 bg-amber-50",
  completed: "border-green-500 bg-green-100",
  failed: "border-red-500 bg-red-100",
  recovering: "border-orange-400 bg-orange-50 animate-pulse",
  terminated: "border-gray-500 bg-gray-200",
};

const STATUS_DOT: Record<AgentStatus, string> = {
  idle: "bg-gray-400",
  initializing: "bg-blue-400",
  executing: "bg-blue-600 animate-pulse",
  reviewing: "bg-amber-500",
  completed: "bg-green-500",
  failed: "bg-red-500",
  recovering: "bg-orange-500 animate-pulse",
  terminated: "bg-gray-500",
};

type AgentFlowNode = Node<AgentNodeData, "agent">;

export function AgentNode({
  data,
}: NodeProps<AgentFlowNode>): React.JSX.Element {
  const status = data.status;
  const colorClasses = STATUS_COLORS[status] ?? STATUS_COLORS.idle;
  const dotClasses = STATUS_DOT[status] ?? STATUS_DOT.idle;

  return (
    <div
      className={`min-w-[160px] rounded-lg border-2 bg-white p-3 shadow-sm ${colorClasses}`}
    >
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center gap-2">
        <div className={`h-2 w-2 rounded-full ${dotClasses}`} />
        <span className="text-sm font-medium text-gray-900">{data.label}</span>
      </div>
      <div className="mt-1 text-xs text-gray-500">{data.agentType}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
