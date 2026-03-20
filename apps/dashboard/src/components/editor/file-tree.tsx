const LANGUAGE_ICONS: Record<string, string> = {
  typescript: "TS",
  javascript: "JS",
  python: "PY",
  json: "{}",
  yaml: "YA",
  markdown: "MD",
  css: "CS",
  html: "HT",
  sql: "SQ",
  rust: "RS",
  go: "GO",
};

interface FileEntry {
  path: string;
  language: string;
}

interface FileTreeProps {
  files: FileEntry[];
  activePath: string | null;
  onSelect: (path: string) => void;
}

function getFileName(path: string): string {
  return path.split("/").pop() ?? path;
}

function getDepth(path: string): number {
  return path.split("/").length - 1;
}

export function FileTree({
  files,
  activePath,
  onSelect,
}: FileTreeProps): React.JSX.Element {
  if (files.length === 0) {
    return (
      <div className="flex items-center justify-center p-4 text-xs text-gray-400">
        No files loaded
      </div>
    );
  }

  return (
    <div className="overflow-y-auto text-sm">
      {files.map((file) => {
        const isActive = file.path === activePath;
        const depth = getDepth(file.path);
        const icon = LANGUAGE_ICONS[file.language] ?? "..";

        return (
          <button
            key={file.path}
            type="button"
            onClick={() => onSelect(file.path)}
            className={`flex w-full items-center gap-2 px-2 py-1 text-left transition-colors ${
              isActive
                ? "bg-blue-50 text-blue-700"
                : "text-gray-700 hover:bg-gray-50"
            }`}
            style={{ paddingLeft: `${String(8 + depth * 12)}px` }}
          >
            <span className="shrink-0 rounded bg-gray-100 px-1 py-0.5 font-mono text-[10px] text-gray-500">
              {icon}
            </span>
            <span className="truncate">{getFileName(file.path)}</span>
          </button>
        );
      })}
    </div>
  );
}
