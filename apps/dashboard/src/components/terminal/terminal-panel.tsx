import { useEffect, useRef } from "react";
import { useTerminalSocket } from "@/hooks/use-terminal-socket";
import "xterm/css/xterm.css";
import { TerminalManager } from "./terminal-manager";
import { agentSocket } from "@/lib/socket";

const DEFAULT_SESSION_ID = "default";

  const containerRef = useRef<HTMLDivElement>(null);
  const managerRef = useRef<TerminalManager | null>(null);
  useTerminalSocket(DEFAULT_SESSION_ID);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Defer initialization so React 18 StrictMode's double-invoke cycle
    // completes before xterm schedules internal async callbacks (setTimeout/rAF).
    // Without this, StrictMode disposes the terminal while xterm's Viewport
    // constructor callbacks are still pending, causing a crash.
    let manager: TerminalManager | null = null;
    let resizeObserver: ResizeObserver | null = null;
    let onData: ((data: { data: string }) => void) | null = null;

    const initId = setTimeout(() => {
      manager = new TerminalManager();
      managerRef.current = manager;

      const session = manager.createSession(DEFAULT_SESSION_ID);
      session.terminal.open(container);
      manager.fit(DEFAULT_SESSION_ID);

      session.terminal.writeln("CodeBot Terminal v1.0");
      session.terminal.writeln("Connected to agent runtime.");
      session.terminal.writeln("");

      onData = (data: { data: string }) => {
        session.terminal.write(data.data);
      };
      agentSocket.on("terminal:data", onData);

      session.terminal.onData((data: string) => {
        agentSocket.emit("terminal:input", { data });
      });

      resizeObserver = new ResizeObserver(() => {
        manager?.fit(DEFAULT_SESSION_ID);
      });
      resizeObserver.observe(container);
    }, 0);

    return () => {
      clearTimeout(initId);
      resizeObserver?.disconnect();
      if (onData) agentSocket.off("terminal:data", onData);
      manager?.destroyAll();
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
