#!/usr/bin/env node
import { Command } from "commander";

const program = new Command();

program
  .name("codebot")
  .description("Multi-agent autonomous software development platform")
  .version("0.1.0");

program.parse(process.argv);
