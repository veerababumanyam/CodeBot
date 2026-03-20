import { useEffect } from "react";
import { pipelineSocket } from "@/lib/socket";
import { usePipelineStore } from "@/stores/pipeline-store";
import type {
  PipelinePhaseEvent,
  PipelineUpdateEvent,
  StageStartEvent,
  StageCompleteEvent,
  StageErrorEvent,
} from "@/types/pipeline";

export function usePipelineEvents(
  pipelineId: string | null,
  projectId: string | null,
): void {
  useEffect(() => {
    if (!pipelineId) return;

    const { applyPipelineUpdate, applyStageEvent } = usePipelineStore.getState();

    const channel = projectId ? `project:${projectId}` : null;
    if (channel) {
      pipelineSocket.emit("subscribe", { channels: [channel] });
    }

    const resolveActivePipeline = (eventPipelineId?: string) => {
      const state = usePipelineStore.getState();
      const resolvedPipelineId = eventPipelineId && eventPipelineId.length > 0
        ? eventPipelineId
        : pipelineId;
      return resolvedPipelineId ? state.pipelines[resolvedPipelineId] ?? null : null;
    };

    const handlePhaseStarted = (event: PipelinePhaseEvent): void => {
      const pipeline = resolveActivePipeline(event.pipeline_id);
      if (!pipeline) {
        return;
      }

      applyPipelineUpdate({
        pipelineId: pipeline.id,
        status: "running",
        currentPhase: event.phase,
        startedAt: pipeline.started_at,
        completedAt: null,
        totalTokensUsed: pipeline.total_tokens_used,
        totalCostUsd: pipeline.total_cost_usd,
        errorMessage: null,
      });

      const stage = pipeline.stages.find(
        (item) => item.stage_number === event.phase_idx || item.name === event.phase,
      );

      if (stage) {
        applyStageEvent({
          pipelineId: pipeline.id,
          stageId: stage.id,
          status: "running",
          stageName: event.phase,
          errorMessage: null,
        });
      }
    };

    const handlePhaseCompleted = (event: PipelinePhaseEvent): void => {
      const pipeline = resolveActivePipeline(event.pipeline_id);
      if (!pipeline) {
        return;
      }

      const stage = pipeline.stages.find(
        (item) => item.stage_number === event.phase_idx || item.name === event.phase,
      );

      if (stage) {
        applyStageEvent({
          pipelineId: pipeline.id,
          stageId: stage.id,
          status: "completed",
          stageName: event.phase,
          errorMessage: null,
        });
        return;
      }

      applyPipelineUpdate({
        pipelineId: pipeline.id,
        status: pipeline.status,
        currentPhase: event.phase,
        startedAt: pipeline.started_at,
        completedAt: pipeline.completed_at,
        totalTokensUsed: pipeline.total_tokens_used,
        totalCostUsd: pipeline.total_cost_usd,
        errorMessage: pipeline.error_message ?? null,
      });
    };

    const handleStageStart = (event: StageStartEvent): void => {
      applyStageEvent({
        pipelineId: event.pipeline_id,
        stageId: event.stage_id,
        status: "running",
        stageName: event.name,
        errorMessage: null,
      });
    };

    const handleStageComplete = (event: StageCompleteEvent): void => {
      applyStageEvent({
        pipelineId: event.pipeline_id,
        stageId: event.stage_id,
        status: "completed",
        stageName: event.name,
        errorMessage: null,
      });
    };

    const handleStageError = (event: StageErrorEvent): void => {
      applyStageEvent({
        pipelineId: event.pipeline_id,
        stageId: event.stage_id,
        status: "failed",
        errorMessage: event.error,
      });
    };

    const handlePipelineUpdate = (event: PipelineUpdateEvent): void => {
      applyPipelineUpdate({
        pipelineId: event.pipeline_id,
        status: event.status,
        currentPhase: event.current_phase,
        startedAt: event.started_at,
        completedAt: event.completed_at,
        totalTokensUsed: event.total_tokens_used,
        totalCostUsd: event.total_cost_usd,
        errorMessage: event.error_message,
      });
    };

    pipelineSocket.on("phase.started", handlePhaseStarted);
    pipelineSocket.on("phase.completed", handlePhaseCompleted);
    pipelineSocket.on("stage:start", handleStageStart);
    pipelineSocket.on("stage:complete", handleStageComplete);
    pipelineSocket.on("stage:error", handleStageError);
    pipelineSocket.on("pipeline:update", handlePipelineUpdate);

    return () => {
      if (channel) {
        pipelineSocket.emit("unsubscribe", { channels: [channel] });
      }
      pipelineSocket.off("phase.started", handlePhaseStarted);
      pipelineSocket.off("phase.completed", handlePhaseCompleted);
      pipelineSocket.off("stage:start", handleStageStart);
      pipelineSocket.off("stage:complete", handleStageComplete);
      pipelineSocket.off("stage:error", handleStageError);
      pipelineSocket.off("pipeline:update", handlePipelineUpdate);
    };
  }, [pipelineId, projectId]);
}
