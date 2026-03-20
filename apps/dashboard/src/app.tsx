import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/query-client";
import { useSocket } from "@/hooks/use-socket";
import { MainLayout } from "@/components/layout/main-layout";
import { PipelineView } from "@/components/pipeline/pipeline-view";

export function App(): React.JSX.Element {
  useSocket();

  return (
    <QueryClientProvider client={queryClient}>
      <MainLayout>
        <PipelineView />
      </MainLayout>
    </QueryClientProvider>
  );
}
