import { useState } from "react";
import { projectApi, type ProjectCreatePayload } from "@/api/projects";
import {
  pickLocalDirectory,
  supportsDirectoryPicker,
} from "@/lib/directory-picker";
import { useProjectStore } from "@/stores/project-store";
import type { Project } from "@/types/project";

type ImportStep = "connect" | "detect" | "review" | "create";

const STEPS: { key: ImportStep; label: string }[] = [
  { key: "connect", label: "Connect" },
  { key: "detect", label: "Detect" },
  { key: "review", label: "Review" },
  { key: "create", label: "Create" },
];

interface DetectedStack {
  language: string;
  framework: string;
  database: string;
  package_manager: string;
  test_framework: string;
  has_ci: boolean;
  has_docker: boolean;
}

interface ImportProjectWizardProps {
  onComplete: (project: Project) => void;
  onCancel: () => void;
}

const LOCAL_PATH_PATTERN = /^(\/|~\/|[A-Za-z]:[\\/]|\\\\)/;

function inferProjectNameFromPath(rawPath: string): string {
  const trimmedPath = rawPath.trim();

  if (!trimmedPath) {
    return "imported-project";
  }

  const parts = trimmedPath.split(/[\\/]/).filter(Boolean);
  return parts.at(-1) ?? "imported-project";
}

export function ImportProjectWizard({
  onComplete,
  onCancel,
}: ImportProjectWizardProps): React.JSX.Element {
  const [step, setStep] = useState<ImportStep>("connect");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const addProject = useProjectStore((s) => s.addProject);

  // Form state
  const [sourceType, setSourceType] = useState<"local" | "git">("local");
  const [path, setPath] = useState("");
  const [projectName, setProjectName] = useState("");
  const [detecting, setDetecting] = useState(false);
  const [detected, setDetected] = useState<DetectedStack | null>(null);
  const [selectedDirectoryName, setSelectedDirectoryName] = useState<
    string | null
  >(null);

  const stepIdx = STEPS.findIndex((s) => s.key === step);
  const directoryPickerSupported = supportsDirectoryPicker();
  const trimmedPath = path.trim();
  const hasValidLocalPath = LOCAL_PATH_PATTERN.test(trimmedPath);
  const canAnalyze =
    sourceType === "local" ? hasValidLocalPath : trimmedPath.length > 0;

  async function handleBrowseDirectory(): Promise<void> {
    setError(null);

    try {
      const selectedDirectory = await pickLocalDirectory();

      if (!selectedDirectory) {
        return;
      }

      setSelectedDirectoryName(selectedDirectory.name);
      setProjectName((currentName) => currentName || selectedDirectory.name);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to open folder picker",
      );
    }
  }

  async function handleDetect(): Promise<void> {
    setDetecting(true);
    setError(null);
    setStep("detect");

    // Simulate detection — in production this calls the backend project_detector
    try {
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const name = inferProjectNameFromPath(path);
      setProjectName(name);

      setDetected({
        language: "TypeScript",
        framework: "React + Vite",
        database: "PostgreSQL",
        package_manager: "pnpm",
        test_framework: "Vitest",
        has_ci: true,
        has_docker: true,
      });
      setStep("review");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to analyze project",
      );
      setStep("connect");
    } finally {
      setDetecting(false);
    }
  }

  async function handleCreate(): Promise<void> {
    setSubmitting(true);
    setError(null);
    setStep("create");

    try {
      const techStack = detected
        ? {
            language: detected.language,
            framework: detected.framework,
            database: detected.database,
            package_manager: detected.package_manager,
            test_framework: detected.test_framework,
            has_ci: detected.has_ci,
            has_docker: detected.has_docker,
          }
        : null;

      const payload: ProjectCreatePayload = {
        name: projectName,
        description: `Imported from ${path}`,
        project_type: "brownfield",
        prd_source: "text",
        prd_content: detected
          ? `Imported repository analysis for ${projectName}\n\nDetected stack:\n- Language: ${detected.language}\n- Framework: ${detected.framework}\n- Database: ${detected.database}\n- Package manager: ${detected.package_manager}\n- Test framework: ${detected.test_framework}`
          : `Imported repository from ${path}`,
        settings: {
          kickoff_flow: "brainstorm",
          import_source: sourceType,
        },
      };

      if (sourceType === "local") {
        payload.repository_path = path;
      }

      if (sourceType === "git") {
        payload.repository_url = path;
      }

      if (techStack) {
        payload.tech_stack = techStack;
      }

      const res = await projectApi.create(payload);
      const project = res.data;
      addProject(project);
      onComplete(project);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create project",
      );
      setStep("review");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-2xl">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Import Existing Project
        </h2>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Step indicators */}
      <div className="mb-8 flex gap-2">
        {STEPS.map((s, i) => (
          <div key={s.key} className="flex flex-1 flex-col items-center gap-1">
            <div
              className={`h-1.5 w-full rounded-full ${
                i <= stepIdx
                  ? "bg-purple-500"
                  : "bg-gray-200 dark:bg-gray-700"
              }`}
            />
            <span
              className={`text-xs ${
                i === stepIdx
                  ? "font-medium text-purple-600 dark:text-purple-400"
                  : "text-gray-400"
              }`}
            >
              {s.label}
            </span>
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-800 dark:bg-red-950 dark:text-red-400">
          {error}
        </div>
      )}

      <div className="min-h-[280px]">
        {step === "connect" && (
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Source Type
              </label>
              <div className="flex gap-2">
                {(["local", "git"] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setSourceType(t)}
                    className={`rounded-lg px-4 py-2 text-sm ${
                      sourceType === t
                        ? "bg-purple-500 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300"
                    }`}
                  >
                    {t === "local" ? "Local Path" : "Git URL"}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label
                htmlFor="import-path"
                className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                {sourceType === "local" ? "Project Path" : "Repository URL"}
              </label>
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  id="import-path"
                  type="text"
                  value={path}
                  onChange={(e) => setPath(e.target.value)}
                  placeholder={
                    sourceType === "local"
                      ? "/Users/you/projects/my-app"
                      : "https://github.com/org/repo.git"
                  }
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 font-mono text-sm text-gray-900 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                  autoFocus
                />
                {sourceType === "local" && (
                  <button
                    type="button"
                    onClick={() => {
                      void handleBrowseDirectory();
                    }}
                    disabled={!directoryPickerSupported || detecting || submitting}
                    className="rounded-lg border border-gray-300 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 disabled:cursor-not-allowed disabled:text-gray-400 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800"
                  >
                    Browse Folder
                  </button>
                )}
              </div>

              {sourceType === "local" && (
                <div className="mt-2 space-y-2 text-xs text-gray-500 dark:text-gray-400">
                  <p>
                    {directoryPickerSupported
                      ? "Browse to inspect a local folder, then paste the full path above to analyze and import it."
                      : "Paste the full local path above to continue. Folder browsing is available in supported Chromium-based browsers."}
                  </p>

                  {selectedDirectoryName && (
                    <div
                      className="rounded-lg border border-purple-200 bg-purple-50 px-3 py-2 text-purple-700 dark:border-purple-900 dark:bg-purple-950 dark:text-purple-300"
                      aria-live="polite"
                    >
                      Selected folder: <span className="font-medium">{selectedDirectoryName}</span>. Paste the full path above to continue.
                    </div>
                  )}

                  {trimmedPath.length > 0 && !hasValidLocalPath && (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-700 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-300">
                      Enter an absolute local path such as <span className="font-mono">/Users/you/projects/my-app</span>.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {step === "detect" && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="mb-4 h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-purple-500" />
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Analyzing project structure...
            </p>
            <p className="mt-1 text-xs text-gray-400">
              Detecting tech stack, dependencies, and configuration
            </p>
          </div>
        )}

        {step === "review" && detected && (
          <div className="space-y-4">
            <div>
              <label
                htmlFor="import-name"
                className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Project Name
              </label>
              <input
                id="import-name"
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>

            <div>
              <h3 className="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                Detected Stack
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(detected)
                  .filter(([, v]) => typeof v === "string" && v)
                  .map(([key, value]) => (
                    <div
                      key={key}
                      className="rounded-lg bg-gray-50 p-3 dark:bg-gray-800"
                    >
                      <div className="text-xs capitalize text-gray-400">
                        {key.replace(/_/g, " ")}
                      </div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {String(value)}
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            <div className="flex gap-3">
              {detected.has_ci && (
                <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900 dark:text-green-300">
                  CI/CD
                </span>
              )}
              {detected.has_docker && (
                <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                  Docker
                </span>
              )}
            </div>
          </div>
        )}

        {step === "create" && (
          <div className="flex flex-col items-center justify-center py-12">
            <div className="mb-4 h-10 w-10 animate-spin rounded-full border-4 border-gray-200 border-t-purple-500" />
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Creating project...
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4 dark:border-gray-700">
        <button
          type="button"
          onClick={step === "connect" ? onCancel : () => setStep("connect")}
          disabled={detecting || submitting}
          className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 disabled:text-gray-400 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          {step === "connect" ? "Cancel" : "Back"}
        </button>

        {step === "connect" && (
          <button
            type="button"
            onClick={handleDetect}
            disabled={!canAnalyze}
            className="rounded-lg bg-purple-600 px-6 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:bg-gray-300 disabled:text-gray-500"
          >
            Analyze Project
          </button>
        )}

        {step === "review" && (
          <button
            type="button"
            onClick={handleCreate}
            disabled={!projectName.trim()}
            className="rounded-lg bg-purple-600 px-6 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:bg-gray-300 disabled:text-gray-500"
          >
            Import Project
          </button>
        )}
      </div>
    </div>
  );
}
