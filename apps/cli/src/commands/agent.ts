import { type Command } from "commander";
import chalk from "chalk";
import { CodeBotClient, CodeBotAPIError } from "../client/api.js";
import { streamLogs } from "../client/streaming.js";
import { formatAgentTable } from "../output/formatters.js";
import { createSpinner } from "../output/spinners.js";

function getClient(program: Command): CodeBotClient {
  const opts = program.opts<{ baseUrl: string; token?: string }>();
  return new CodeBotClient(opts.baseUrl, opts.token ?? null);
}

function handleError(err: unknown): void {
  if (err instanceof CodeBotAPIError) {
    if (err.statusCode === 401) {
      console.error(
        chalk.red(
          "Authentication required. Set CODEBOT_TOKEN or run codebot config set token <token>.",
        ),
      );
    } else {
      console.error(chalk.red(`Error: ${err.message}`));
    }
  } else if (err instanceof Error) {
    console.error(chalk.red(`Error: ${err.message}`));
  }
}

async function listAgentsAction(
  options: { pipelineId: string },
  command: Command,
): Promise<void> {
  try {
    const root = command.parent?.parent ?? command.parent!;
    const client = getClient(root);
    const spinner = createSpinner("Fetching agents...");
    spinner.start();

    const result = await client.listAgents(options.pipelineId);
    spinner.stop();

    if (result.data.length === 0) {
      console.log(chalk.dim("No agents found."));
      return;
    }

    console.log(formatAgentTable(result.data));
  } catch (err) {
    handleError(err);
  }
}

async function logsAction(
  pipelineId: string,
  _options: Record<string, unknown>,
  command: Command,
): Promise<void> {
  try {
    const root = command.parent?.parent ?? command.parent!;
    const opts = root.opts<{ baseUrl: string; token?: string }>();
    await streamLogs(opts.baseUrl, pipelineId, opts.token ?? null);
  } catch (err) {
    handleError(err);
  }
}

export function registerAgentCommands(program: Command): void {
  const agent = program
    .command("agent")
    .description("Agent monitoring commands");

  agent
    .command("list")
    .description("List agents for a pipeline")
    .requiredOption("--pipeline-id <pipelineId>", "Pipeline ID")
    .action(listAgentsAction);

  agent
    .command("logs <pipelineId>")
    .description("Stream agent logs in real-time")
    .action(logsAction);

  // Top-level convenience alias
  program
    .command("logs <pipelineId>")
    .description("Stream agent logs (shortcut for agent logs)")
    .action(logsAction);
}
