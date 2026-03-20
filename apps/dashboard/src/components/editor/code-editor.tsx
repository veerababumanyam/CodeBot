import { useEffect, useRef, useCallback } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";
import type { editor as monacoEditor } from "monaco-editor";
import { MonacoBinding } from "y-monaco";
import { useEditorStore } from "@/stores/editor-store";
import { useUiStore } from "@/stores/ui-store";
import { useYjs } from "@/hooks/use-yjs";

interface CodeEditorProps {
  filePath: string | null;
  language?: string;
  readOnly?: boolean;
}

export function CodeEditor({
  filePath,
  language,
  readOnly = false,
}: CodeEditorProps): React.JSX.Element {
  const file = useEditorStore((s) =>
    filePath ? s.files[filePath] : undefined,
  );
  const markUnsaved = useEditorStore((s) => s.markUnsaved);
  const theme = useUiStore((s) => s.theme);
  const editorRef = useRef<monacoEditor.IStandaloneCodeEditor | null>(null);
  const bindingRef = useRef<MonacoBinding | null>(null);

  const { doc, provider } = useYjs(filePath);

  const handleMount: OnMount = useCallback(
    (editor) => {
      editorRef.current = editor;
    },
    [],
  );

  // Yjs binding lifecycle
  useEffect(() => {
    const editor = editorRef.current;
    if (!editor || !doc || !provider) return;

    const model = editor.getModel();
    if (!model) return;

    const yText = doc.getText("monaco");
    const binding = new MonacoBinding(yText, model, new Set([editor]), provider.awareness);
    bindingRef.current = binding;

    return () => {
      binding.destroy();
      bindingRef.current = null;
    };
  }, [doc, provider]);

  const handleChange = useCallback(() => {
    if (filePath) {
      markUnsaved(filePath);
    }
  }, [filePath, markUnsaved]);

  if (!filePath) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-gray-400">
        Select a file to edit
      </div>
    );
  }

  return (
    <Editor
      height="100%"
      language={language ?? file?.language ?? "plaintext"}
      value={file?.content ?? ""}
      theme={theme === "dark" ? "vs-dark" : "vs-light"}
      onMount={handleMount}
      onChange={handleChange}
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        lineNumbers: "on",
        scrollBeyondLastLine: false,
        automaticLayout: true,
        wordWrap: "on",
        tabSize: 2,
      }}
    />
  );
}
