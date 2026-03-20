import { type Command } from "commander";
import { input, confirm } from "@inquirer/prompts";
import chalk from "chalk";
import { readFileSync } from "node:fs";
import { CodeBotClient, CodeBotAPIError } from "../client/api.js";
import { formatProjectTable } from "../output/formatters.js";
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

async function createProjectAction(
  options: { prd?: string },
  command: Command,
): Promise<void> {
  try {
    const name = await input({ message: "Project name:" });
    const description = await input({
      message: "Description (optional):",
      default: "",
    });

    let prdContent: string | undefined;
    if (options.prd) {
      prdContent = readFileSync(options.prd, "utf-8");
    }

    const client = getClient(command.parent!);
    const spinner = createSpinner("Creating project...");
    spinner.start();

    const project = await client.createProject(name, description, prdContent);
    spinner.succeed(
      chalk.green(`Project created: ${project.name} (${project.id})`),
    );
  } catch (err) {
    handleError(err);
  }
}

async function listProjectsAction(
  options: { page: string; perPage: string },
  command: Command,
): Promise<void> {
  try {
    const client = getClient(command.parent!);
    const spinner = createSpinner("Fetching projects...");
    spinner.start();

    const result = await client.listProjects(
      parseInt(options.page, 10),
      parseInt(options.perPage, 10),
    );
    spinner.stop();

    if (result.data.length === 0) {
      console.log(chalk.dim("No projects found."));
      return;
    }

    console.log(formatProjectTable(result.data));

    if (result.pagination && result.pagination.total_pages > 1) {
      console.log(
        chalk.dim(
          `\nPage ${result.pagination.page} of ${result.pagination.total_pages} (${result.pagination.total} total)`,
        ),
      );
    }
  } catch (err) {
    handleError(err);
  }
}

async function deleteProjectAction(
  projectId: string,
  _options: Record<string, unknown>,
  command: Command,
): Promise<void> {
  try {
    const confirmed = await confirm({
      message: `Are you sure you want to delete project ${projectId}?`,
      default: false,
    });

    if (!confirmed) {
      console.log(chalk.dim("Cancelled."));
      return;
    }

    const client = getClient(command.parent!);
    const spinner = createSpinner("Deleting project...");
    spinner.start();

    await client.deleteProject(projectId);
    spinner.succeed(chalk.green(`Project ${projectId} deleted.`));
  } catch (err) {
    handleError(err);
  }
}

export function registerProjectCommands(program: Command): void {
  const project = program
    .command("project")
    .description("Project management commands");

  project
    .command("create")
    .description("Create a new project")
    .option("--prd <path>", "Path to PRD file")
    .action(createProjectAction);

  project
    .command("list")
    .description("List all projects")
    .option("--page <number>", "Page number", "1")
    .option("--per-page <number>", "Items per page", "20")
    .action(listProjectsAction);

  project
    .command("delete <projectId>")
    .description("Delete a project")
    .action(deleteProjectAction);

  // Top-level convenience alias
  program
    .command("create")
    .description("Create a new project (shortcut for project create)")
    .option("--prd <path>", "Path to PRD file")
    .action(createProjectAction);
}
