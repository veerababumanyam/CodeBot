import type { ReactNode } from "react";
import { useUiStore } from "@/stores/ui-store";
import { useChatStore } from "@/stores/chat-store";
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
    <div className="app-shell flex h-screen overflow-hidden text-foreground">
      {sidebarOpen && <Sidebar />}
      <div className="relative flex flex-1 flex-col overflow-hidden">
        <Header />
        <div className="flex flex-1 overflow-hidden">
          <main className="relative flex-1 overflow-auto px-4 pb-4 transition-all duration-300 sm:px-5 sm:pb-5">
            {children}
          </main>
          {/* Spacer for the fixed sidebar to push content */}
          <div
            style={{ width: drawerOpen ? sidebarWidth : 0 }}
            className="relative z-0 shrink-0 transition-all duration-300"
          />
        </div>
      </div>
    </div>
  );
}
