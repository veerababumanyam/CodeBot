import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { Pipeline, PipelineStatus, StageStatus } from "@/types/pipeline";

interface StageEventUpdate {
  pipelineId: string;
  stageId: string;
  status: StageStatus;
  stageName?: string;
  errorMessage?: string | null;
}

interface PipelineUpdate {
  pipelineId: string;
  status: PipelineStatus;
  currentPhase: string;
  startedAt: string | null;
  completedAt: string | null;
  totalTokensUsed: number;
  totalCostUsd: number;
  errorMessage: string | null;
}

interface PipelineState {
  pipelines: Record<string, Pipeline>;
  activePipelineId: string | null;
  focusedStageId: string | null;
  isLoading: boolean;
  error: string | null;
}

interface PipelineActions {
  setPipelines: (list: Pipeline[]) => void;
  upsertPipeline: (pipeline: Pipeline) => void;
  setActivePipeline: (id: string | null) => void;
  setFocusedStage: (id: string | null) => void;
  updateStageStatus: (
    pipelineId: string,
    stageId: string,
    status: StageStatus,
  ) => void;
  applyStageEvent: (update: StageEventUpdate) => void;
  applyPipelineUpdate: (update: PipelineUpdate) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

function derivePipelineStatus(
  currentStatus: PipelineStatus,
  stages: Pipeline["stages"],
  incomingStatus: StageStatus,
): PipelineStatus {
  if (incomingStatus === "failed") {
    return "failed";
  }

  if (incomingStatus === "running") {
    return "running";
  }

  const allDone = stages.every(
    (stage) => stage.status === "completed" || stage.status === "skipped",
  );

  if (allDone) {
    return "completed";
  }

  if (currentStatus === "failed" || currentStatus === "cancelled") {
    return currentStatus;
  }

  return "running";
}

const initialState: PipelineState = {
  pipelines: {},
  activePipelineId: null,
  focusedStageId: null,
  isLoading: false,
  error: null,
};

export const usePipelineStore = create<PipelineState & PipelineActions>()(
  devtools(
    subscribeWithSelector(
      immer((set) => ({
        ...initialState,

        setPipelines: (list: Pipeline[]) =>
          set((state) => {
            state.pipelines = {};
            for (const pipeline of list) {
              state.pipelines[pipeline.id] = pipeline;
            }
          }),

        upsertPipeline: (pipeline: Pipeline) =>
          set((state) => {
            state.pipelines[pipeline.id] = pipeline;
          }),

        setActivePipeline: (id: string | null) =>
          set((state) => {
            state.activePipelineId = id;
          }),

        setFocusedStage: (id: string | null) =>
          set((state) => {
            state.focusedStageId = id;
          }),

        updateStageStatus: (
          pipelineId: string,
          stageId: string,
          status: StageStatus,
        ) =>
          set((state) => {
            const pipeline = state.pipelines[pipelineId];
            if (!pipeline) return;
            const stage = pipeline.stages.find((s) => s.id === stageId);
            if (stage) {
              stage.status = status;
            }
          }),

        applyStageEvent: ({
          pipelineId,
          stageId,
          status,
          stageName,
          errorMessage,
        }: StageEventUpdate) =>
          set((state) => {
            const pipeline = state.pipelines[pipelineId];
            if (!pipeline) return;

            const stage = pipeline.stages.find((s) => s.id === stageId);
            if (!stage) return;

            stage.status = status;
            if (stageName) {
              stage.name = stageName;
            }

            if (status === "failed") {
              stage.error_message = errorMessage ?? stage.error_message ?? null;
            } else if (errorMessage === null || status === "running" || status === "completed") {
              stage.error_message = null;
            }

            pipeline.current_phase = stageName ?? stage.name;
            pipeline.status = derivePipelineStatus(pipeline.status, pipeline.stages, status);

            if (status === "failed") {
              pipeline.error_message = errorMessage ?? pipeline.error_message ?? null;
            } else if (status === "running" || status === "completed") {
              pipeline.error_message = null;
            }
          }),

        applyPipelineUpdate: ({
          pipelineId,
          status,
          currentPhase,
          startedAt,
          completedAt,
          totalTokensUsed,
          totalCostUsd,
          errorMessage,
        }: PipelineUpdate) =>
          set((state) => {
            const pipeline = state.pipelines[pipelineId];
            if (!pipeline) return;

            pipeline.status = status;
            pipeline.current_phase = currentPhase;
            pipeline.started_at = startedAt;
            pipeline.completed_at = completedAt;
            pipeline.total_tokens_used = totalTokensUsed;
            pipeline.total_cost_usd = totalCostUsd;
            pipeline.error_message = errorMessage;
          }),

        setLoading: (loading: boolean) =>
          set((state) => {
            state.isLoading = loading;
          }),

        setError: (error: string | null) =>
          set((state) => {
            state.error = error;
          }),

        reset: () =>
          set((state) => {
            state.pipelines = initialState.pipelines;
            state.activePipelineId = initialState.activePipelineId;
            state.focusedStageId = initialState.focusedStageId;
            state.isLoading = initialState.isLoading;
            state.error = initialState.error;
          }),
      })),
    ),
    { name: "PipelineStore" },
  ),
);

export const selectPipelineList = (state: PipelineState): Pipeline[] =>
  Object.values(state.pipelines);

export const selectActivePipeline = (
  state: PipelineState & PipelineActions,
): Pipeline | null =>
  state.activePipelineId
    ? (state.pipelines[state.activePipelineId] ?? null)
    : null;
