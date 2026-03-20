import ora from "ora";

export function createSpinner(message: string): ReturnType<typeof ora> {
  return ora({ text: message, spinner: "dots" });
}
