import type { ReactNode } from "react";
import { useUiStore } from "@/stores/ui-store";
import { useChatStore } from "@/stores/chat-store";
import { cn } from "@/lib/utils";
import { Sidebar } from "./sidebar";
import { Header } from "./header";

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps): React.JSX.Element {
  const sidebarOpen = useUiStore((s) => s.sidebarOpen);
  const drawerOpen = useChatStore((s) => s.drawerOpen);

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {sidebarOpen && <Sidebar />}
      <div className="flex flex-1 flex-col relative overflow-hidden">
        <Header />
        <main className={cn(
            "flex-1 overflow-auto transition-all duration-500",
            drawerOpen ? "pb-[450px]" : "pb-12"
        )}>
            {children}
        </main>
      </div>
    </div>
  );
}
