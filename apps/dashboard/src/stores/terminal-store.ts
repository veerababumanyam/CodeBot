import { create } from "zustand";

interface TerminalSessionState {
  output: string;
  cols: number;
  rows: number;
}

interface TerminalState {
  sessions: Record<string, TerminalSessionState>;
  writeData: (sessionId: string, data: string) => void;
  setResize: (sessionId: string, cols: number, rows: number) => void;
  reset: () => void;
}

const initialSession: TerminalSessionState = {
  output: "",
  cols: 80,
  rows: 24,
};

export const useTerminalStore = create<TerminalState>((set) => ({
  sessions: {},
  writeData: (sessionId, data) =>
    set((state) => {
      if (!state.sessions[sessionId]) state.sessions[sessionId] = { ...initialSession };
      state.sessions[sessionId].output += data;
    }),
  setResize: (sessionId, cols, rows) =>
    set((state) => {
      if (!state.sessions[sessionId]) state.sessions[sessionId] = { ...initialSession };
      state.sessions[sessionId].cols = cols;
      state.sessions[sessionId].rows = rows;
    }),
  reset: () => set({ sessions: {} }),
}));
