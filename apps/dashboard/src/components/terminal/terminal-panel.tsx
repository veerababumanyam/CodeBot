import { useEffect, useRef } from "react";
import "xterm/css/xterm.css";
import { TerminalManager } from "./terminal-manager";
import { agentSocket } from "@/lib/socket";

const DEFAULT_SESSION_ID = "default";

export function TerminalPanel(): React.JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null);
  const managerRef = useRef<TerminalManager | null>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const manager = new TerminalManager();
    managerRef.current = manager;

    const session = manager.createSession(DEFAULT_SESSION_ID);
    session.terminal.open(container);
    manager.fit(DEFAULT_SESSION_ID);

    session.terminal.writeln("CodeBot Terminal v1.0");
    session.terminal.writeln("Connected to agent runtime.");
    session.terminal.writeln("");

    // Socket.IO terminal data bridge
    const onData = (data: { data: string }) => {
      session.terminal.write(data.data);
    };
    agentSocket.on("terminal:data", onData);

    session.terminal.onData((data: string) => {
      agentSocket.emit("terminal:input", { data });
    });

    // Resize observer for fitting terminal
    const resizeObserver = new ResizeObserver(() => {
      manager.fit(DEFAULT_SESSION_ID);
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      agentSocket.off("terminal:data", onData);
      manager.destroyAll();
      managerRef.current = null;
    };
  }, []);

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-2">
        <h2 className="text-sm font-semibold text-gray-700">Terminal</h2>
        <span className="text-xs text-gray-500">xterm.js</span>
      </div>
      <div ref={containerRef} className="flex-1 bg-[#1e1e1e]" />
    </div>
  );
}
