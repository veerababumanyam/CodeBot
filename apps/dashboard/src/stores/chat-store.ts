import { create } from "zustand";

export type MessageType = "user" | "agent" | "system" | "clarification" | "approval" | "error";

export interface Message {
  id: string;
  type: MessageType;
  content: string;
  agent?: string;
  timestamp: string;
  meta?: any;
}

interface ChatState {
  messages: Message[];
  drawerOpen: boolean;
  isTyping: boolean;
  activeAgent: string | null;
  addMessage: (message: Message) => void;
  setDrawerOpen: (open: boolean) => void;
  setTyping: (typing: boolean, agent?: string) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  drawerOpen: true, // Start open for visibility as per docs
  isTyping: false,
  activeAgent: null,
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  setDrawerOpen: (open) => set({ drawerOpen: open }),
  setTyping: (typing, agent) => set({ isTyping: typing, activeAgent: agent || null }),
  clearMessages: () => set({ messages: [] }),
}));
