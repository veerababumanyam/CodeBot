import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

interface FileEntry {
  path: string;
  content: string;
  language: string;
}

interface EditorState {
  activeFile: string | null;
  files: Record<string, FileEntry>;
  unsavedChanges: Set<string>;
  isLoading: boolean;
}

interface EditorActions {
  setActiveFile: (path: string | null) => void;
  setFileContent: (path: string, content: string, language: string) => void;
  markUnsaved: (path: string) => void;
  markSaved: (path: string) => void;
  reset: () => void;
}

const initialState: EditorState = {
  activeFile: null,
  files: {},
  unsavedChanges: new Set<string>(),
  isLoading: false,
};

export const useEditorStore = create<EditorState & EditorActions>()(
  devtools(
    subscribeWithSelector(
      immer((set) => ({
        ...initialState,

        setActiveFile: (path: string | null) =>
          set((state) => {
            state.activeFile = path;
          }),

        setFileContent: (path: string, content: string, language: string) =>
          set((state) => {
            state.files[path] = { path, content, language };
          }),

        markUnsaved: (path: string) =>
          set((state) => {
            state.unsavedChanges.add(path);
          }),

        markSaved: (path: string) =>
          set((state) => {
            state.unsavedChanges.delete(path);
          }),

        reset: () =>
          set((state) => {
            state.activeFile = initialState.activeFile;
            state.files = initialState.files;
            state.unsavedChanges = new Set<string>();
            state.isLoading = initialState.isLoading;
          }),
      })),
    ),
    { name: "EditorStore" },
  ),
);
