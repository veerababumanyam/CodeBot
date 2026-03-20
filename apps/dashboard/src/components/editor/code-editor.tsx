import { useEffect, useRef, useCallback, Suspense, lazy } from "react";
// Dynamically import Monaco editor at module scope
const MonacoEditor = lazy(() => import("@monaco-editor/react"));
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

  // Use any for OnMount to avoid type import from monaco-editor
  const handleMount = useCallback((editor: any) => {
    editorRef.current = editor;
  }, []);

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
    <Suspense fallback={<div className="flex h-full items-center justify-center text-sm text-gray-400">Loading editor…</div>}>
      <MonacoEditor
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
    </Suspense>
  );
}
