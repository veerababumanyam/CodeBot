import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { AgentNode, type AgentNodeData } from "./agent-node";
import { edgeTypes } from "./edge-types";
import {
  usePipelineStore,
  selectActivePipeline,
} from "@/stores/pipeline-store";
import { useAgentStore } from "@/stores/agent-store";
import { usePipelineEvents } from "@/hooks/use-pipeline-events";
import { useAgentStatus } from "@/hooks/use-agent-status";

const nodeTypes = { agent: AgentNode } as const;

const STAGE_Y_GAP = 180;
const AGENT_X_GAP = 200;

export function PipelineView(): React.JSX.Element {
  const pipeline = usePipelineStore(selectActivePipeline);
  const agents = useAgentStore((s) => s.agents);

  usePipelineEvents(pipeline?.id ?? null);
  useAgentStatus(pipeline?.id ?? null);

  const { nodes, edges } = useMemo(() => {
    if (!pipeline) return { nodes: [] as Node[], edges: [] as Edge[] };

    const builtNodes: Node<AgentNodeData>[] = [];
    const builtEdges: Edge[] = [];

    for (const stage of pipeline.stages) {
      const stageAgents = stage.agents
        .map((agentId) => agents[agentId])
        .filter((a) => a !== undefined);

      const startX =
        stageAgents.length > 1
          ? -((stageAgents.length - 1) * AGENT_X_GAP) / 2
          : 0;

      stageAgents.forEach((agent, idx) => {
        builtNodes.push({
          id: agent.id,
          type: "agent",
          position: {
            x: startX + idx * AGENT_X_GAP,
            y: stage.stage_number * STAGE_Y_GAP,
          },
          data: {
            label: agent.name,
            agentType: agent.agent_type,
            status: agent.status,
            stageNumber: stage.stage_number,
          },
        });
      });
    }

    // Build sequential stage connection edges
    const sortedStages = [...pipeline.stages].sort(
      (a, b) => a.stage_number - b.stage_number,
    );

    for (let i = 0; i < sortedStages.length - 1; i++) {
      const currentStage = sortedStages[i];
      const nextStage = sortedStages[i + 1];

      if (!currentStage || !nextStage) continue;

      const currentAgents = currentStage.agents;
      const nextAgents = nextStage.agents;

      // Connect last agent of current stage to first agent of next stage
      const sourceId = currentAgents[currentAgents.length - 1];
      const targetId = nextAgents[0];

      if (sourceId && targetId) {
        builtEdges.push({
          id: `edge-s${String(currentStage.stage_number)}-s${String(nextStage.stage_number)}`,
          source: sourceId,
          target: targetId,
          type: "control",
        });
      }
    }

    return { nodes: builtNodes, edges: builtEdges };
  }, [pipeline, agents]);

  if (!pipeline) {
    return (
      <div className="flex h-full items-center justify-center text-gray-400">
        Select a pipeline to view its execution graph
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
