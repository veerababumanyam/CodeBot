import chalk from "chalk";
import type {
  ProjectResponse,
  PipelineResponse,
  AgentResponse,
} from "../types.js";

const STATUS_COLORS: Record<string, (s: string) => string> = {
  created: chalk.gray,
  planning: chalk.blue,
  in_progress: chalk.cyan,
  running: chalk.cyan,
  completed: chalk.green,
  failed: chalk.red,
  paused: chalk.yellow,
  cancelled: chalk.gray,
  idle: chalk.gray,
  executing: chalk.blue,
  reviewing: chalk.magenta,
};

function colorStatus(status: string): string {
  const colorFn = STATUS_COLORS[status] ?? chalk.white;
  return colorFn(status);
}

function padRight(s: string, len: number): string {
  return s.length >= len ? s.slice(0, len) : s + " ".repeat(len - s.length);
}

export function formatProjectTable(projects: ProjectResponse[]): string {
  const header = `${padRight("ID", 14)} ${padRight("Name", 30)} ${padRight("Status", 14)} ${padRight("Type", 12)} Created`;
  const sep = "-".repeat(header.length);
  const rows = projects.map((p) => {
    const created = chalk.dim(new Date(p.created_at).toLocaleDateString());
    return `${padRight(p.id.slice(0, 12), 14)} ${padRight(p.name, 30)} ${padRight(p.status, 14)} ${padRight(p.project_type, 12)} ${created}`;
  });
  return `${chalk.bold(header)}\n${sep}\n${rows.join("\n")}`;
}

export function formatPipelineStatus(pipeline: PipelineResponse): string {
  const statusStr = colorStatus(pipeline.status);
  return [
    chalk.bold("Pipeline Status"),
    `  ID:      ${chalk.dim(pipeline.id)}`,
    `  Mode:    ${pipeline.mode}`,
    `  Status:  ${statusStr}`,
    `  Stage:   ${pipeline.current_stage}/${pipeline.total_stages}`,
    `  Created: ${chalk.dim(new Date(pipeline.created_at).toLocaleString())}`,
  ].join("\n");
}

export function formatAgentTable(agents: AgentResponse[]): string {
  const header = `${padRight("ID", 10)} ${padRight("Name", 25)} ${padRight("Type", 18)} ${padRight("Status", 14)} ${padRight("Tokens", 10)} Cost`;
  const sep = "-".repeat(header.length);
  const rows = agents.map((a) => {
    const id = a.id.slice(0, 8);
    const cost = `$${a.cost_usd.toFixed(4)}`;
    return `${padRight(id, 10)} ${padRight(a.name, 25)} ${padRight(a.agent_type, 18)} ${padRight(a.status, 14)} ${padRight(String(a.tokens_used), 10)} ${cost}`;
  });
  return `${chalk.bold(header)}\n${sep}\n${rows.join("\n")}`;
}
