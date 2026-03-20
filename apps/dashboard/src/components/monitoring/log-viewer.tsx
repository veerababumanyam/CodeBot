import { useEffect, useRef } from "react";
import type { AgentLogEvent } from "@/types/agent";

const LEVEL_CLASSES: Record<string, string> = {
  info: "bg-blue-100 text-blue-800",
  warn: "bg-yellow-100 text-yellow-800",
  error: "bg-red-100 text-red-800",
  debug: "bg-gray-100 text-gray-800",
};

interface LogViewerProps {
  logs: AgentLogEvent[];
  maxHeight?: string;
}

export function LogViewer({
  logs,
  maxHeight = "400px",
}: LogViewerProps): React.JSX.Element {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  if (logs.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-sm text-gray-400"
        style={{ minHeight: "120px" }}
      >
        No logs yet
      </div>
    );
  }

  return (
    <div
      className="overflow-y-auto font-mono text-xs"
      style={{ maxHeight }}
    >
      {logs.map((log, idx) => (
        <div
          key={`${log.timestamp}-${String(idx)}`}
          className="flex gap-2 px-2 py-0.5 hover:bg-gray-50"
        >
          <span className="shrink-0 text-gray-400">
            {new Date(log.timestamp).toLocaleTimeString()}
          </span>
          <span
            className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${LEVEL_CLASSES[log.level] ?? "bg-gray-100 text-gray-800"}`}
          >
            {log.level}
          </span>
          <span className="break-all">{log.message}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
