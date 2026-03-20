interface FileSystemDirectoryHandleLike {
  kind?: "directory";
  name: string;
}

interface ShowDirectoryPickerOptionsLike {
  mode?: "read" | "readwrite";
  id?: string;
  startIn?:
    | "desktop"
    | "documents"
    | "downloads"
    | "music"
    | "pictures"
    | "videos";
}

interface DirectoryPickerWindowLike extends Window {
  showDirectoryPicker?: (
    options?: ShowDirectoryPickerOptionsLike,
  ) => Promise<FileSystemDirectoryHandleLike>;
}

export interface PickedDirectory {
  name: string;
  source: "native-picker";
}

function getDirectoryPickerWindow(): DirectoryPickerWindowLike | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window as DirectoryPickerWindowLike;
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

export function supportsDirectoryPicker(): boolean {
  const directoryPickerWindow = getDirectoryPickerWindow();
  return typeof directoryPickerWindow?.showDirectoryPicker === "function";
}

export async function pickLocalDirectory(): Promise<PickedDirectory | null> {
  const directoryPickerWindow = getDirectoryPickerWindow();
  const showDirectoryPicker = directoryPickerWindow?.showDirectoryPicker;

  if (!showDirectoryPicker) {
    throw new Error(
      "Folder browsing is not available in this browser. Paste the full project path to continue.",
    );
  }

  try {
    const handle = await showDirectoryPicker({
      mode: "read",
      id: "codebot-import-project",
      startIn: "documents",
    });

    if (!handle?.name) {
      return null;
    }

    return {
      name: handle.name,
      source: "native-picker",
    };
  } catch (error) {
    if (isAbortError(error)) {
      return null;
    }

    throw error instanceof Error
      ? error
      : new Error("Failed to open the folder picker.");
  }
}