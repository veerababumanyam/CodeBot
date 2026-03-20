import { create } from "zustand";

export type MessageType = "user" | "agent" | "system" | "clarification" | "approval" | "error";

export interface Attachment {
  type: "image" | "file";
  url: string;
  name: string;
  size?: number;
}

export interface Message {
  id: string;
  type: MessageType;
  content: string;
  agent?: string;
  timestamp: string;
  meta?: any;
  attachments?: Attachment[];
}

interface ChatState {
  messages: Message[];
  drawerOpen: boolean;
  sidebarWidth: number;
  isTyping: boolean;
  activeAgent: string | null;
  addMessage: (message: Message) => void;
  setDrawerOpen: (open: boolean) => void;
  setSidebarWidth: (width: number) => void;
  setTyping: (typing: boolean, agent?: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  drawerOpen: true, // Start open for visibility as per docs
  sidebarWidth: 400, // Default width for Microsoft Copilot style
  isTyping: false,
  activeAgent: null,
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  setDrawerOpen: (open) => set({ drawerOpen: open }),
  setSidebarWidth: (width) => set({ sidebarWidth: width }),
  setTyping: (typing, agent) => set({ isTyping: typing, activeAgent: agent || null }),
  clearMessages: () => set({ messages: [] }),
}));
