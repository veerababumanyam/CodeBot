import type { StageStatus } from "@/types/pipeline";

interface StageGroupProps {
  label: string;
  stageNumber: number;
  status: StageStatus;
  children?: React.ReactNode;
}

const STATUS_BG: Record<StageStatus, string> = {
  idle: "bg-gray-50 border-gray-300",
  running: "bg-blue-50 border-blue-300",
  completed: "bg-green-50 border-green-300",
  failed: "bg-red-50 border-red-300",
  skipped: "bg-gray-50 border-gray-300",
  waiting: "bg-amber-50 border-amber-300",
};

const STATUS_DOT: Record<StageStatus, string> = {
  idle: "bg-gray-400",
  running: "bg-blue-500 animate-pulse",
  completed: "bg-green-500",
  failed: "bg-red-500",
  skipped: "bg-gray-400",
  waiting: "bg-amber-500",
};

export function StageGroup({
  label,
  stageNumber,
  status,
  children,
}: StageGroupProps): React.JSX.Element {
  const bgClasses = STATUS_BG[status] ?? STATUS_BG.idle;
  const dotClasses = STATUS_DOT[status] ?? STATUS_DOT.idle;

  return (
    <div className={`rounded-xl border-2 border-dashed p-4 ${bgClasses}`}>
      <div className="mb-3 flex items-center gap-2">
        <div className={`h-2 w-2 rounded-full ${dotClasses}`} />
        <span className="text-xs font-semibold text-gray-700">
          S{String(stageNumber)} {label}
        </span>
      </div>
      {children}
    </div>
  );
}
