import { useEffect } from "react";
import { pipelineSocket } from "@/lib/socket";
import { usePipelineStore } from "@/stores/pipeline-store";
import type {
  StageStartEvent,
  StageCompleteEvent,
  StageErrorEvent,
} from "@/types/pipeline";

export function usePipelineEvents(pipelineId: string | null): void {
  useEffect(() => {
    if (!pipelineId) return;

    const { updateStageStatus } = usePipelineStore.getState();

    pipelineSocket.emit("subscribe", { pipeline_id: pipelineId });

    const handleStageStart = (event: StageStartEvent): void => {
      updateStageStatus(event.pipeline_id, event.stage_id, "running");
    };

    const handleStageComplete = (event: StageCompleteEvent): void => {
      updateStageStatus(event.pipeline_id, event.stage_id, "completed");
    };

    const handleStageError = (event: StageErrorEvent): void => {
      updateStageStatus(event.pipeline_id, event.stage_id, "failed");
    };

    pipelineSocket.on("stage:start", handleStageStart);
    pipelineSocket.on("stage:complete", handleStageComplete);
    pipelineSocket.on("stage:error", handleStageError);

    return () => {
      pipelineSocket.emit("unsubscribe", { pipeline_id: pipelineId });
      pipelineSocket.off("stage:start", handleStageStart);
      pipelineSocket.off("stage:complete", handleStageComplete);
      pipelineSocket.off("stage:error", handleStageError);
    };
  }, [pipelineId]);
}
