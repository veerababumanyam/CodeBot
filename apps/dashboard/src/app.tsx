import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query-client";
import { useSocket } from "@/hooks/use-socket";
import { MainLayout } from "@/components/layout/main-layout";
import { PipelineView } from "@/components/pipeline/pipeline-view";
import { AgentPanel } from "@/components/monitoring/agent-panel";
import { CostBreakdown } from "@/components/monitoring/cost-breakdown";
import { CodeEditor } from "@/components/editor/code-editor";
import { FileTree } from "@/components/editor/file-tree";
import { TerminalPanel } from "@/components/terminal/terminal-panel";
import { PreviewFrame } from "@/components/preview/preview-frame";
import { useUiStore } from "@/stores/ui-store";
import { useEditorStore } from "@/stores/editor-store";

function ActivePanel(): React.JSX.Element {
  const activePanel = useUiStore((s) => s.activePanel);
  const activeFile = useEditorStore((s) => s.activeFile);
  const files = useEditorStore((s) =>
    Object.values(s.files).map((f) => ({
      path: f.path,
      language: f.language,
    })),
  );
  const setActiveFile = useEditorStore((s) => s.setActiveFile);

  switch (activePanel) {
    case "pipeline":
      return <PipelineView />;
    case "monitoring":
      return <AgentPanel />;
    case "cost":
      return <CostBreakdown />;
    case "editor":
      return (
        <div className="flex h-full">
          <div className="w-60 shrink-0 overflow-y-auto border-r border-gray-200">
            <FileTree
              files={files}
              activePath={activeFile}
              onSelect={setActiveFile}
            />
          </div>
          <div className="flex-1">
            <CodeEditor filePath={activeFile} />
          </div>
        </div>
      );
    case "terminal":
      return <TerminalPanel />;
    case "preview":
      return <PreviewFrame />;
    default:
      return <PipelineView />;
  }
}

export function App(): React.JSX.Element {
  useSocket();

  return (
    <QueryClientProvider client={queryClient}>
      <MainLayout>
        <ActivePanel />
      </MainLayout>
    </QueryClientProvider>
  );
}
