import { describe, expect, it } from "vitest";
import { getExecutionPlan, getExecutionPlanLabel } from "./execution-plan";

describe("execution plan helpers", () => {
  it("returns the quick preset stages in launch order", () => {
    const plan = getExecutionPlan("quick");

    expect(plan.map((step) => step.key)).toEqual([
      "initialize",
      "design",
      "plan",
      "implement",
      "qa",
      "test",
      "fix",
      "deliver",
    ]);
  });

  it("normalizes review-only preset labels", () => {
    expect(getExecutionPlanLabel("review-only")).toBe("Review only");
    expect(getExecutionPlan("review_only")).toHaveLength(1);
  });
});
