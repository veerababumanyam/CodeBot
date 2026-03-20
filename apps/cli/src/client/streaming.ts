import WebSocket from "ws";
import chalk from "chalk";
import type { AgentLogEvent } from "../types.js";

const LEVEL_COLORS = {
  info: chalk.blue,
  warn: chalk.yellow,
  error: chalk.red,
  debug: chalk.gray,
} as const;

export async function streamLogs(
  baseUrl: string,
  pipelineId: string,
  token: string | null,
): Promise<void> {
  const wsUrl = baseUrl.replace(/^http/, "ws") + "/ws/agents";
  const ws = new WebSocket(wsUrl, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  return new Promise<void>((resolve, reject) => {
    ws.on("open", () => {
      ws.send(
        JSON.stringify({ type: "subscribe", pipeline_id: pipelineId }),
      );
      console.log(
        chalk.dim("Connected. Streaming logs... (Ctrl+C to stop)\n"),
      );
    });

    ws.on("message", (raw: WebSocket.RawData) => {
      try {
        const event = JSON.parse(raw.toString()) as {
          type: string;
          data: AgentLogEvent;
        };
        if (event.type === "agent:log") {
          const log = event.data;
          const colorFn = LEVEL_COLORS[log.level] ?? chalk.white;
          const ts = chalk.dim(
            new Date(log.timestamp).toLocaleTimeString(),
          );
          const level = colorFn(`[${log.level.toUpperCase()}]`);
          const agent = chalk.bold(log.agent_id.slice(0, 8));
          console.log(`${ts} ${level} ${agent} ${log.message}`);
        } else if (event.type === "agent:status") {
          const d = event.data as unknown as {
            agent_id: string;
            status: string;
          };
          console.log(
            chalk.cyan(
              `  >> Agent ${d.agent_id.slice(0, 8)} status: ${d.status}`,
            ),
          );
        }
      } catch {
        /* ignore malformed messages */
      }
    });

    ws.on("error", (err: Error) => {
      if (err.message.includes("ECONNREFUSED")) {
        console.error(
          chalk.red(
            "Error: Could not connect to server. Is it running?",
          ),
        );
      } else {
        console.error(chalk.red(`WebSocket error: ${err.message}`));
      }
      reject(err);
    });

    ws.on("close", () => {
      console.log(chalk.dim("\nDisconnected."));
      resolve();
    });

    process.on("SIGINT", () => {
      ws.close();
    });
  });
}
