import {
  getBezierPath,
  type EdgeProps,
  type Edge,
  BaseEdge,
} from "@xyflow/react";

type DataEdgeType = Edge<Record<string, unknown>, "data">;
type ControlEdgeType = Edge<Record<string, unknown>, "control">;
type ConditionalEdgeData = { condition?: string; [key: string]: unknown };
type ConditionalEdgeType = Edge<ConditionalEdgeData, "conditional">;

function DataEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style,
}: EdgeProps<DataEdgeType>): React.JSX.Element {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      style={{ ...style, stroke: "#9ca3af", strokeWidth: 2 }}
    />
  );
}

function ControlEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style,
}: EdgeProps<ControlEdgeType>): React.JSX.Element {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });

  return (
    <BaseEdge
      id={id}
      path={edgePath}
      style={{
        ...style,
        stroke: "#6b7280",
        strokeWidth: 2,
        strokeDasharray: "5 5",
      }}
    />
  );
}

function ConditionalEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style,
  data,
}: EdgeProps<ConditionalEdgeType>): React.JSX.Element {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          ...style,
          stroke: "#9ca3af",
          strokeWidth: 2,
          strokeDasharray: "2 4",
        }}
      />
      {data?.condition && (
        <foreignObject
          width={80}
          height={24}
          x={labelX - 40}
          y={labelY - 12}
        >
          <div className="flex items-center justify-center">
            <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600">
              {data.condition}
            </span>
          </div>
        </foreignObject>
      )}
    </>
  );
}

export const edgeTypes = {
  data: DataEdge,
  control: ControlEdge,
  conditional: ConditionalEdge,
} as const;
