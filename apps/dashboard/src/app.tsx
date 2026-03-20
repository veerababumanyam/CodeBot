import { Suspense, lazy } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useShallow } from "zustand/react/shallow";
import { queryClient } from "@/lib/query-client";
import { useSocket } from "@/hooks/use-socket";
import { MainLayout } from "@/components/layout/main-layout";
import { BrainstormPanel } from "@/components/brainstorm/brainstorm-panel";
import { ProjectHub } from "@/components/projects/project-hub";
import { useThemeSync } from "@/hooks/use-theme-sync";
import { useUiStore } from "@/stores/ui-store";
import { useEditorStore } from "@/stores/editor-store";
import { useProjectStore } from "@/stores/project-store";

const PipelineView = lazy(async () => {
  const module = await import("@/components/pipeline/pipeline-view");
  return { default: module.PipelineView };
});

const AgentPanel = lazy(async () => {
  const module = await import("@/components/monitoring/agent-panel");
  return { default: module.AgentPanel };
});

const CostBreakdown = lazy(async () => {
  const module = await import("@/components/monitoring/cost-breakdown");
  return { default: module.CostBreakdown };
});

const CodeEditor = lazy(async () => {
  const module = await import("@/components/editor/code-editor");
  return { default: module.CodeEditor };
});

const FileTree = lazy(async () => {
  const module = await import("@/components/editor/file-tree");
  return { default: module.FileTree };
});

const TerminalPanel = lazy(async () => {
  const module = await import("@/components/terminal/terminal-panel");
  return { default: module.TerminalPanel };
});

const PreviewFrame = lazy(async () => {
  const module = await import("@/components/preview/preview-frame");
  return { default: module.PreviewFrame };
});

const ChatSidebar = lazy(async () => {
  const module = await import("@/components/chat/chat-sidebar");
  return { default: module.ChatSidebar };
});

function PanelFallback(): React.JSX.Element {
  return (
    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
      Loading workspace…
    </div>
  );
}

function ActivePanel(): React.JSX.Element {
  const activePanel = useUiStore((s) => s.activePanel);
  const activeProjectId = useProjectStore((s) => s.activeProjectId);
  const activeFile = useEditorStore((s) => s.activeFile);
  const files = useEditorStore(
    useShallow((s) =>
      Object.values(s.files).map((f) => ({
        path: f.path,
        language: f.language,
      })),
    ),
  );
  const setActiveFile = useEditorStore((s) => s.setActiveFile);

  // No project selected — show the Project Hub
  if (!activeProjectId) {
    return <ProjectHub />;
  }

  switch (activePanel) {
    case "pipeline":
      return (
        <Suspense fallback={<PanelFallback />}>
          <PipelineView />
        </Suspense>
      );
    case "brainstorm":
      return <BrainstormPanel />;
    case "monitoring":
      return (
        <Suspense fallback={<PanelFallback />}>
          <AgentPanel />
        </Suspense>
      );
    case "cost":
      return (
        <Suspense fallback={<PanelFallback />}>
          <CostBreakdown />
        </Suspense>
      );
    case "editor":
      return (
        <Suspense fallback={<PanelFallback />}>
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
        </Suspense>
      );
    case "terminal":
      return (
        <Suspense fallback={<PanelFallback />}>
          <TerminalPanel />
        </Suspense>
      );
    case "preview":
      return (
        <Suspense fallback={<PanelFallback />}>
          <PreviewFrame />
        </Suspense>
      );
    default:
      return (
        <Suspense fallback={<PanelFallback />}>
          <PipelineView />
        </Suspense>
      );
  }
}

export function App(): React.JSX.Element {
  useSocket();
  useThemeSync();

  return (
    <QueryClientProvider client={queryClient}>
      <MainLayout>
        <ActivePanel />
      </MainLayout>
      <Suspense fallback={null}>
        <ChatSidebar />
      </Suspense>
    </QueryClientProvider>
  );
}
