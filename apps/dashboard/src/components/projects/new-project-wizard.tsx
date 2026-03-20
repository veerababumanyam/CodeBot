import { useRef, useState } from "react";
import { projectApi, type ProjectCreatePayload } from "@/api/projects";
import { useProjectStore } from "@/stores/project-store";
import type { Project } from "@/types/project";

type Step = "basics" | "prd" | "stack" | "settings";

const STEPS: { key: Step; label: string }[] = [
  { key: "basics", label: "Basics" },
  { key: "prd", label: "PRD" },
  { key: "stack", label: "Tech Stack" },
  { key: "settings", label: "Settings" },
];

const PIPELINE_PRESETS = [
  { value: "full", label: "Full Pipeline", desc: "All stages S0-S10" },
  { value: "quick", label: "Quick Build", desc: "Skip research & docs" },
  {
    value: "review-only",
    label: "Review Only",
    desc: "Code review & QA only",
  },
];

interface NewProjectWizardProps {
  onComplete: (project: Project) => void;
  onCancel: () => void;
}

export function NewProjectWizard({
  onComplete,
  onCancel,
}: NewProjectWizardProps): React.JSX.Element {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState<Step>("basics");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const addProject = useProjectStore((s) => s.addProject);

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [prdSource, setPrdSource] = useState<"text" | "file" | "url">("text");
  const [prdContent, setPrdContent] = useState("");
  const [prdFile, setPrdFile] = useState<{
    data: string;
    name: string;
    type: string;
  } | null>(null);
  const [techStack, setTechStack] = useState<Record<string, string>>({
    language: "",
    framework: "",
    database: "",
  });
  const [preset, setPreset] = useState("full");

  const stepIdx = STEPS.findIndex((s) => s.key === step);

  function goNext(): void {
    const nextStep = STEPS[stepIdx + 1];
    if (nextStep) setStep(nextStep.key);
  }

  function goBack(): void {
    const prevStep = STEPS[stepIdx - 1];
    if (prevStep) setStep(prevStep.key);
  }

  async function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ): Promise<void> {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const isSupported = [".md", ".markdown", ".txt", ".pdf", ".docx"].some(
      (extension) => file.name.toLowerCase().endsWith(extension),
    );

    if (!isSupported) {
      setError("Unsupported file type. Use .md, .txt, .pdf, or .docx.");
      event.target.value = "";
      return;
    }

    const data = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === "string") {
          resolve(reader.result);
          return;
        }
        reject(new Error("Unable to read selected file"));
      };
      reader.onerror = () => reject(new Error("Unable to read selected file"));
      reader.readAsDataURL(file);
    });

    setError(null);
    setPrdFile({ data, name: file.name, type: file.type });
    event.target.value = "";
  }

  function buildCreatePayload(): ProjectCreatePayload {
    const stackObj = Object.fromEntries(
      Object.entries(techStack).filter(([, value]) => value.trim() !== ""),
    );
    const normalizedPreset = preset === "review-only" ? "review_only" : preset;

    const payload: ProjectCreatePayload = {
      name,
      description,
      prd_source: prdSource,
      project_type: "greenfield",
      settings: {
        kickoff_flow: "brainstorm",
        pipeline_preset: normalizedPreset,
      },
    };

    if (Object.keys(stackObj).length > 0) {
      payload.tech_stack = stackObj;
    }

    if (prdSource === "text") {
      payload.prd_content = prdContent.trim();
    }

    if (prdSource === "url") {
      payload.prd_url = prdContent.trim();
    }

    if (prdSource === "file" && prdFile) {
      payload.prd_file = prdFile.data;
      payload.source_name = prdFile.name;
      payload.source_media_type = prdFile.type;
    }

    return payload;
  }

  async function handleQuickCreate(): Promise<void> {
    await handleSubmit();
  }

  async function handleSubmit(): Promise<void> {
    setSubmitting(true);
    setError(null);
    try {
      const res = await projectApi.create(buildCreatePayload());
      const project = res.data;
      addProject(project);
      onComplete(project);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  }

  const canProceed =
    step === "basics"
      ? name.trim().length > 0
      : step === "prd"
        ? prdSource === "text"
          ? prdContent.trim().length > 0
          : prdSource === "url"
            ? prdContent.trim().length > 0
            : prdFile !== null
        : true;

  return (
    <div className="mx-auto w-full max-w-2xl">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          New Project
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
                  ? "bg-blue-500"
                  : "bg-gray-200 dark:bg-gray-700"
              }`}
            />
            <span
              className={`text-xs ${
                i === stepIdx
                  ? "font-medium text-blue-600 dark:text-blue-400"
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

      {/* Step content */}
      <div className="min-h-[280px]">
        {step === "basics" && (
          <div className="space-y-4">
            <div>
              <label
                htmlFor="project-name"
                className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Project Name *
              </label>
              <input
                id="project-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My Awesome App"
                className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                autoFocus
              />
            </div>
            <div>
              <label
                htmlFor="project-desc"
                className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Description
              </label>
              <textarea
                id="project-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What does this project do?"
                rows={3}
                className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
              />
            </div>
            <button
              type="button"
              onClick={handleQuickCreate}
              disabled={!canProceed || submitting}
              className="text-sm text-blue-600 underline hover:text-blue-700 disabled:text-gray-400 disabled:no-underline dark:text-blue-400"
            >
              Quick create with defaults
            </button>
          </div>
        )}

        {step === "prd" && (
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
                PRD Source
              </label>
              <div className="flex gap-2">
                {(["text", "file", "url"] as const).map((src) => (
                  <button
                    key={src}
                    type="button"
                    onClick={() => setPrdSource(src)}
                    className={`rounded-lg px-4 py-2 text-sm capitalize ${
                      prdSource === src
                        ? "bg-blue-500 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300"
                    }`}
                  >
                    {src}
                  </button>
                ))}
              </div>
            </div>
            {prdSource === "text" && (
              <div>
                <label
                  htmlFor="prd-content"
                  className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Product Requirements
                </label>
                <textarea
                  id="prd-content"
                  value={prdContent}
                  onChange={(e) => setPrdContent(e.target.value)}
                  placeholder="Describe what you want to build in natural language, or paste a PRD..."
                  rows={8}
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 font-mono text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                />
              </div>
            )}
            {prdSource === "url" && (
              <div>
                <label
                  htmlFor="prd-url"
                  className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  PRD URL
                </label>
                <input
                  id="prd-url"
                  type="url"
                  value={prdContent}
                  onChange={(e) => setPrdContent(e.target.value)}
                  placeholder="https://docs.google.com/document/d/..."
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                />
              </div>
            )}
            {prdSource === "file" && (
              <div className="space-y-3 rounded-lg border-2 border-dashed border-gray-300 p-6 dark:border-gray-600">
                <div className="flex flex-col items-center justify-center gap-2 text-center">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Upload a PRD document to seed the brainstorm
                  </p>
                  <p className="text-xs text-gray-400">
                    Supports .md, .txt, .pdf, and .docx
                  </p>
                </div>
                <div className="flex items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    Browse files
                  </button>
                  {prdFile && (
                    <span className="text-sm text-gray-600 dark:text-gray-300">
                      {prdFile.name}
                    </span>
                  )}
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".md,.markdown,.txt,.pdf,.docx"
                  onChange={(event) => {
                    void handleFileChange(event);
                  }}
                  className="hidden"
                />
              </div>
            )}
          </div>
        )}

        {step === "stack" && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Optional. Leave blank to let agents auto-detect the best stack.
            </p>
            {Object.entries(techStack).map(([key, value]) => (
              <div key={key}>
                <label
                  htmlFor={`stack-${key}`}
                  className="mb-1 block text-sm font-medium capitalize text-gray-700 dark:text-gray-300"
                >
                  {key}
                </label>
                <input
                  id={`stack-${key}`}
                  type="text"
                  value={value}
                  onChange={(e) =>
                    setTechStack((prev) => ({
                      ...prev,
                      [key]: e.target.value,
                    }))
                  }
                  placeholder={
                    key === "language"
                      ? "e.g. TypeScript, Python"
                      : key === "framework"
                        ? "e.g. Next.js, FastAPI"
                        : "e.g. PostgreSQL, MongoDB"
                  }
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
                />
              </div>
            ))}
          </div>
        )}

        {step === "settings" && (
          <div className="space-y-4">
            <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Pipeline Preset
            </label>
            <div className="space-y-2">
              {PIPELINE_PRESETS.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setPreset(p.value)}
                  className={`flex w-full items-center rounded-lg border p-4 text-left transition-colors ${
                    preset === p.value
                      ? "border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-blue-950"
                      : "border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600"
                  }`}
                >
                  <div
                    className={`mr-3 h-4 w-4 rounded-full border-2 ${
                      preset === p.value
                        ? "border-blue-500 bg-blue-500"
                        : "border-gray-300 dark:border-gray-600"
                    }`}
                  >
                    {preset === p.value && (
                      <div className="m-0.5 h-2 w-2 rounded-full bg-white" />
                    )}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {p.label}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {p.desc}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4 dark:border-gray-700">
        <button
          type="button"
          onClick={stepIdx === 0 ? onCancel : goBack}
          className="rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
        >
          {stepIdx === 0 ? "Cancel" : "Back"}
        </button>

        {stepIdx < STEPS.length - 1 ? (
          <button
            type="button"
            onClick={goNext}
            disabled={!canProceed}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500"
          >
            Next
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting || !name.trim()}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:text-gray-500"
          >
            {submitting ? "Creating..." : "Create Project"}
          </button>
        )}
      </div>
    </div>
  );
}
