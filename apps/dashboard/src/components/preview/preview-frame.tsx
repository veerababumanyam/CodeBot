import { useState, useCallback } from "react";

interface PreviewFrameProps {
  url?: string;
  title?: string;
}

export function PreviewFrame({
  url,
  title = "Live Preview",
}: PreviewFrameProps): React.JSX.Element {
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  if (!url) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-2">
          <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
        </div>
        <div className="flex flex-1 items-center justify-center text-sm text-gray-400">
          No preview available. Start a pipeline to see live output.
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-4 py-2">
        <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
        <div className="flex items-center gap-2">
          <span className="truncate text-xs text-gray-500 max-w-xs">
            {url}
          </span>
          <button
            type="button"
            onClick={handleRefresh}
            className="rounded border border-gray-300 px-2 py-0.5 text-xs text-gray-600 hover:bg-gray-100 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>
      <iframe
        key={refreshKey}
        src={url}
        title={title}
        sandbox="allow-scripts allow-same-origin"
        className="flex-1 w-full border-0"
      />
    </div>
  );
}
