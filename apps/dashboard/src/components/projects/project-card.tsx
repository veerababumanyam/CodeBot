import type { Project, ProjectStatus } from "@/types/project";

const STATUS_STYLES: Record<ProjectStatus, { dot: string; label: string }> = {
  created: { dot: "bg-gray-400", label: "Created" },
  planning: { dot: "bg-blue-400", label: "Planning" },
  in_progress: { dot: "bg-green-400 animate-pulse", label: "Running" },
  review: { dot: "bg-yellow-400", label: "Review" },
  completed: { dot: "bg-green-500", label: "Completed" },
  failed: { dot: "bg-red-500", label: "Failed" },
  paused: { dot: "bg-orange-400", label: "Paused" },
  cancelled: { dot: "bg-gray-500", label: "Cancelled" },
};

function timeAgo(dateStr: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(dateStr).getTime()) / 1000,
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${String(minutes)}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${String(hours)}h ago`;
  const days = Math.floor(hours / 24);
  return `${String(days)}d ago`;
}

interface ProjectCardProps {
  project: Project;
  isActive: boolean;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
}

export function ProjectCard({
  project,
  isActive,
  onOpen,
  onDelete,
}: ProjectCardProps): React.JSX.Element {
  const status = STATUS_STYLES[project.status] ?? STATUS_STYLES.created;

  return (
    <button
      type="button"
      onClick={() => onOpen(project.id)}
      className={`group relative flex w-full flex-col rounded-xl border p-5 text-left transition-all hover:shadow-md ${
        isActive
          ? "border-blue-500 bg-blue-50 shadow-sm dark:border-blue-400 dark:bg-blue-950"
          : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-900 dark:hover:border-gray-600"
      }`}
    >
      <div className="mb-3 flex items-start justify-between">
        <h3 className="truncate text-sm font-semibold text-gray-900 dark:text-white">
          {project.name}
        </h3>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(project.id);
          }}
          className="ml-2 shrink-0 rounded p-1 text-gray-400 opacity-0 transition-opacity hover:bg-red-50 hover:text-red-500 group-hover:opacity-100 dark:hover:bg-red-950"
          aria-label={`Delete ${project.name}`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      </div>

      {project.description && (
        <p className="mb-3 line-clamp-2 text-xs text-gray-500 dark:text-gray-400">
          {project.description}
        </p>
      )}

      <div className="mt-auto flex items-center justify-between">
        <span className="inline-flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
          <span className={`inline-block h-2 w-2 rounded-full ${status.dot}`} />
          {status.label}
        </span>
        <span className="text-xs text-gray-400 dark:text-gray-500">
          {timeAgo(project.updated_at)}
        </span>
      </div>
    </button>
  );
}
