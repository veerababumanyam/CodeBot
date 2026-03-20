import { type Command } from "commander";
import { confirm } from "@inquirer/prompts";
import chalk from "chalk";
import { CodeBotClient, CodeBotAPIError } from "../client/api.js";
import { formatPipelineStatus } from "../output/formatters.js";
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

function mapPreset(preset: string): string {
  if (preset === "review-only") return "review_only";
  return preset;
}

async function startPipelineAction(
  projectId: string,
  options: { preset: string },
  command: Command,
): Promise<void> {
  try {
    const root = command.parent?.parent ?? command.parent!;
    const client = getClient(root);
    const mode = mapPreset(options.preset);
    const spinner = createSpinner("Creating and starting pipeline...");
    spinner.start();

    const pipeline = await client.createPipeline(projectId, mode);
    const started = await client.startPipeline(pipeline.id);
    spinner.stop();

    console.log(formatPipelineStatus(started));
  } catch (err) {
    handleError(err);
  }
}

async function pausePipelineAction(
  pipelineId: string,
  _options: Record<string, unknown>,
  command: Command,
): Promise<void> {
  try {
    const root = command.parent?.parent ?? command.parent!;
    const client = getClient(root);
    const spinner = createSpinner("Pausing pipeline...");
    spinner.start();

    const result = await client.pausePipeline(pipelineId);
    spinner.stop();

    console.log(formatPipelineStatus(result));
  } catch (err) {
    handleError(err);
  }
}

async function resumePipelineAction(
  pipelineId: string,
  _options: Record<string, unknown>,
  command: Command,
): Promise<void> {
  try {
    const root = command.parent?.parent ?? command.parent!;
    const client = getClient(root);
    const spinner = createSpinner("Resuming pipeline...");
    spinner.start();

    const result = await client.resumePipeline(pipelineId);
    spinner.stop();

    console.log(formatPipelineStatus(result));
  } catch (err) {
    handleError(err);
  }
}

async function stopPipelineAction(
  pipelineId: string,
  _options: Record<string, unknown>,
  command: Command,
): Promise<void> {
  try {
    const confirmed = await confirm({
      message: `Are you sure you want to stop pipeline ${pipelineId}?`,
      default: false,
    });

    if (!confirmed) {
      console.log(chalk.dim("Cancelled."));
      return;
    }

    const root = command.parent?.parent ?? command.parent!;
    const client = getClient(root);
    const spinner = createSpinner("Stopping pipeline...");
    spinner.start();

    const result = await client.stopPipeline(pipelineId);
    spinner.stop();

    console.log(formatPipelineStatus(result));
  } catch (err) {
    handleError(err);
  }
}

export function registerPipelineCommands(program: Command): void {
  const pipeline = program
    .command("pipeline")
    .description("Pipeline control commands");

  pipeline
    .command("start <projectId>")
    .description("Create and start a pipeline for a project")
    .option(
      "--preset <preset>",
      "Pipeline preset (full, quick, review-only)",
      "full",
    )
    .action(startPipelineAction);

  pipeline
    .command("pause <pipelineId>")
    .description("Pause a running pipeline")
    .action(pausePipelineAction);

  pipeline
    .command("resume <pipelineId>")
    .description("Resume a paused pipeline")
    .action(resumePipelineAction);

  pipeline
    .command("stop <pipelineId>")
    .description("Stop a pipeline")
    .action(stopPipelineAction);

  // Top-level convenience alias
  program
    .command("start <projectId>")
    .description("Start a pipeline (shortcut for pipeline start)")
    .option(
      "--preset <preset>",
      "Pipeline preset (full, quick, review-only)",
      "full",
    )
    .action(startPipelineAction);
}
