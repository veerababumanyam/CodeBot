import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { Pipeline, StageStatus } from "@/types/pipeline";

interface PipelineState {
  pipelines: Record<string, Pipeline>;
  activePipelineId: string | null;
  isLoading: boolean;
  error: string | null;
}

interface PipelineActions {
  setPipelines: (list: Pipeline[]) => void;
  upsertPipeline: (pipeline: Pipeline) => void;
  setActivePipeline: (id: string | null) => void;
  updateStageStatus: (
    pipelineId: string,
    stageId: string,
    status: StageStatus,
  ) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState: PipelineState = {
  pipelines: {},
  activePipelineId: null,
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
