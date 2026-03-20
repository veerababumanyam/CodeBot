import { type Command } from "commander";
import chalk from "chalk";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { CLIConfig } from "../types.js";

const CONFIG_DIR = join(homedir(), ".codebot");
const CONFIG_PATH = join(CONFIG_DIR, "config.json");

const VALID_PRESETS = ["full", "quick", "review-only"];
const VALID_CONFIG_KEYS = ["server_url", "preset", "token"] as const;
type ConfigKey = (typeof VALID_CONFIG_KEYS)[number];

function loadConfig(): CLIConfig {
  try {
    const raw = readFileSync(CONFIG_PATH, "utf-8");
    return JSON.parse(raw) as CLIConfig;
  } catch {
    return { server_url: "http://localhost:8000", preset: "full" };
  }
}

function saveConfig(config: CLIConfig): void {
  mkdirSync(CONFIG_DIR, { recursive: true });
  writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2) + "\n", "utf-8");
}

function isValidConfigKey(key: string): key is ConfigKey {
  return (VALID_CONFIG_KEYS as readonly string[]).includes(key);
}

export function registerConfigCommands(program: Command): void {
  const config = program
    .command("config")
    .description("Configuration management");

  config
    .command("preset <preset>")
    .description("Set the default pipeline preset")
    .action((preset: string) => {
      if (!VALID_PRESETS.includes(preset)) {
        console.error(
          chalk.red(
            `Invalid preset: ${preset}. Must be one of: ${VALID_PRESETS.join(", ")}`,
          ),
        );
        return;
      }

      const cfg = loadConfig();
      cfg.preset = preset;
      saveConfig(cfg);
      console.log(chalk.green(`Default preset set to: ${preset}`));
    });

  config
    .command("show")
    .description("Show current configuration")
    .action(() => {
      const cfg = loadConfig();
      console.log(chalk.bold("Configuration:"));
      console.log(`  ${chalk.cyan("server_url")}: ${cfg.server_url}`);
      console.log(`  ${chalk.cyan("preset")}:     ${cfg.preset}`);
      console.log(
        `  ${chalk.cyan("token")}:      ${cfg.token ? chalk.dim("[set]") : chalk.dim("[not set]")}`,
      );
    });

  config
    .command("set <key> <value>")
    .description("Set a configuration value (server_url, preset, token)")
    .action((key: string, value: string) => {
      if (!isValidConfigKey(key)) {
        console.error(
          chalk.red(
            `Invalid key: ${key}. Valid keys: ${VALID_CONFIG_KEYS.join(", ")}`,
          ),
        );
        return;
      }

      if (key === "preset" && !VALID_PRESETS.includes(value)) {
        console.error(
          chalk.red(
            `Invalid preset: ${value}. Must be one of: ${VALID_PRESETS.join(", ")}`,
          ),
        );
        return;
      }

      const cfg = loadConfig();
      cfg[key] = value;
      saveConfig(cfg);
      console.log(chalk.green(`${key} = ${key === "token" ? "[redacted]" : value}`));
    });
}
