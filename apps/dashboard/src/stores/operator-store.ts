import { create } from "zustand";

interface OperatorAction {
  action: string;
  payload: any;
  timestamp: string;
}

interface OperatorState {
  actions: Record<string, OperatorAction[]>; // projectId -> actions
  status: Record<string, string>; // projectId -> status
  addAction: (projectId: string, action: string, payload: any) => void;
  setStatus: (projectId: string, status: string, detail?: string) => void;
  reset: () => void;
}

export const useOperatorStore = create<OperatorState>((set) => ({
  actions: {},
  status: {},
  addAction: (projectId, action, payload) =>
    set((state) => {
      const prevActions = state.actions[projectId] || [];
      return {
        ...state,
        actions: {
          ...state.actions,
          [projectId]: [
            ...prevActions,
            {
              action,
              payload,
              timestamp: new Date().toISOString(),
            },
          ],
        },
      };
    }),
  setStatus: (projectId, status, detail) =>
    set((state) => ({
      ...state,
      status: {
        ...state.status,
        [projectId]: detail ? `${status}: ${detail}` : status,
      },
    })),
  reset: () => set({ actions: {}, status: {} }),
}));
