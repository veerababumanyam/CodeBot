import { create } from "zustand";
import { devtools, persist } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";
import type { Project } from "@/types/project";

interface ProjectState {
  projects: Project[];
  openProjectIds: string[];
  activeProjectId: string | null;
}

interface ProjectActions {
  setProjects: (projects: Project[]) => void;
  addProject: (project: Project) => void;
  updateProject: (id: string, patch: Partial<Project>) => void;
  removeProject: (id: string) => void;
  openProject: (id: string) => void;
  closeProject: (id: string) => void;
  setActiveProject: (id: string | null) => void;
}

export const useProjectStore = create<ProjectState & ProjectActions>()(
  devtools(
    persist(
      immer((set) => ({
        projects: [],
        openProjectIds: [],
        activeProjectId: null,

        setProjects: (projects) =>
          set((state) => {
            state.projects = projects;
          }),

        addProject: (project) =>
          set((state) => {
            state.projects.push(project);
          }),

        updateProject: (id, patch) =>
          set((state) => {
            const idx = state.projects.findIndex((p) => p.id === id);
            if (idx !== -1) {
              Object.assign(state.projects[idx]!, patch);
            }
          }),

        removeProject: (id) =>
          set((state) => {
            state.projects = state.projects.filter((p) => p.id !== id);
            state.openProjectIds = state.openProjectIds.filter(
              (pid) => pid !== id,
            );
            if (state.activeProjectId === id) {
              state.activeProjectId =
                state.openProjectIds[0] ?? null;
            }
          }),

        openProject: (id) =>
          set((state) => {
            if (!state.openProjectIds.includes(id)) {
              state.openProjectIds.push(id);
            }
            state.activeProjectId = id;
          }),

        closeProject: (id) =>
          set((state) => {
            state.openProjectIds = state.openProjectIds.filter(
              (pid) => pid !== id,
            );
            if (state.activeProjectId === id) {
              state.activeProjectId =
                state.openProjectIds[0] ?? null;
            }
          }),

        setActiveProject: (id) =>
          set((state) => {
            state.activeProjectId = id;
          }),
      })),
      {
        name: "codebot-projects",
        partialize: (state) => ({
          openProjectIds: state.openProjectIds,
          activeProjectId: state.activeProjectId,
        }),
      },
    ),
    { name: "ProjectStore" },
  ),
);
