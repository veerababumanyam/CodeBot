#!/usr/bin/env node
import { Command } from "commander";
import { registerProjectCommands } from "./commands/project.js";
import { registerPipelineCommands } from "./commands/pipeline.js";
import { registerAgentCommands } from "./commands/agent.js";
import { registerConfigCommands } from "./commands/config.js";

const program = new Command();

program
  .name("codebot")
  .description("CodeBot CLI - autonomous software development platform")
  .version("0.1.0")
  .option(
    "--base-url <url>",
    "Server URL",
    process.env["CODEBOT_URL"] ?? "http://localhost:8000",
  )
  .option("--token <token>", "Auth token", process.env["CODEBOT_TOKEN"]);

registerProjectCommands(program);
registerPipelineCommands(program);
registerAgentCommands(program);
registerConfigCommands(program);

program.parse();

export { program };
