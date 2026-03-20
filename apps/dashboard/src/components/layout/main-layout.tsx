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
  const sidebarWidth = useChatStore((s) => s.sidebarWidth);

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {sidebarOpen && <Sidebar />}
      <div className="flex flex-1 flex-col relative overflow-hidden">
        <Header />
        <div className="flex flex-1 overflow-hidden">
            <main className="flex-1 overflow-auto transition-all duration-300 relative">
                {children}
            </main>
            {/* Spacer for the fixed sidebar to push content */}
            <div 
                style={{ width: drawerOpen ? sidebarWidth : 0 }} 
                className="transition-all duration-300 shrink-0 relative z-0"
            />
        </div>
      </div>
    </div>
  );
}
