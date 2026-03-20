---
name: codebot-dashboard
description: Patterns and conventions for building features in the CodeBot React dashboard
version: "1.0"
tags:
  - react
  - typescript
  - dashboard
  - codebot
  - zustand
  - tailwind
  - vite
globs:
  - "apps/dashboard/**/*.ts"
  - "apps/dashboard/**/*.tsx"
  - "apps/dashboard/**/*.css"
---

# CodeBot Dashboard Development Skill

## Project Overview

The CodeBot dashboard lives in `apps/dashboard/`. It is a React + TypeScript application built with Vite, styled with Tailwind CSS, and using Zustand for state management. Real-time updates flow through WebSocket/Socket.IO.

**Runtime and tooling:**
- Node.js 22 LTS
- pnpm 9.x
- ESM modules
- TypeScript 5.5+ in strict mode

## Directory Structure

```
apps/dashboard/src/
  components/
    layout/        # Sidebar, Header, MainLayout
    project/       # ProjectBoard (kanban), ProjectCreate (PRD input), ProjectList
    pipeline/      # PipelineView (phases), PhaseCard, PhaseGate (approval)
    agents/        # AgentTimeline, AgentCard, AgentLogs, AgentGraph (D3/React Flow)
    code/          # CodeViewer (syntax), DiffViewer, FileTree
    review/        # ReviewPanel, SecurityFindings, QualityReport
    testing/       # TestResults, CoverageReport
    chat/          # ChatPanel (Orchestrator), MessageBubble
    terminal/      # EmbeddedTerminal (xterm.js)
    metrics/       # TokenUsage, CostDashboard, PerformanceChart
    brainstorm/    # BrainstormPanel, IdeaBoard, RequirementRefiner
    templates/     # TemplateGallery, TemplatePreview, TechStackSelector
    deployment/    # DeploymentPanel, CloudProviderSelector, DeploymentStatus, DeploymentLogs
    collaboration/ # CollaborationPanel, PresenceIndicator, ConflictResolver, LiveCursor
    mobile/        # MobilePreview, DeviceSimulator
    github/        # GitHubPanel, PRViewer, ActionsStatus
    accessibility/ # A11yReport, WCAGChecklist
    performance/   # PerformanceReport, LoadTestResults
  stores/          # Zustand stores
  services/        # API client, WebSocket client
  hooks/           # Custom React hooks
  types/           # Shared TypeScript types
```

## 1. Creating New Dashboard Components

Every component is a named export in its own file. Use functional components with TypeScript interfaces for props.

```tsx
// apps/dashboard/src/components/feature/FeaturePanel.tsx
import { type FC } from "react";

interface FeaturePanelProps {
  projectId: string;
  isActive?: boolean;
  onClose: () => void;
}

export const FeaturePanel: FC<FeaturePanelProps> = ({
  projectId,
  isActive = false,
  onClose,
}) => {
  return (
    <div className="flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <header className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Feature</h2>
        <button
          onClick={onClose}
          className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          aria-label="Close panel"
        >
          &times;
        </button>
      </header>
      <div className="flex-1">{/* content */}</div>
    </div>
  );
};
```

**Conventions:**
- One component per file, named export matching the filename.
- Props interface is declared directly above the component in the same file.
- Default props via destructuring defaults, not `defaultProps`.
- Always include `aria-label` or `aria-*` attributes on interactive elements.
- Place the component in the appropriate `components/<area>/` subdirectory.

## 2. Zustand Store Patterns

Stores live at `apps/dashboard/src/stores/`. Existing stores: `projectStore.ts`, `pipelineStore.ts`, `agentStore.ts`, `settingsStore.ts`.

### Creating a New Store

```ts
// apps/dashboard/src/stores/featureStore.ts
import { create } from "zustand";
import { devtools, subscribeWithSelector } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

interface FeatureItem {
  id: string;
  name: string;
  status: "idle" | "active" | "complete" | "error";
  updatedAt: string;
}

interface FeatureState {
  items: Record<string, FeatureItem>;
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;
}

interface FeatureActions {
  setItems: (items: FeatureItem[]) => void;
  upsertItem: (item: FeatureItem) => void;
  removeItem: (id: string) => void;
  select: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState: FeatureState = {
  items: {},
  selectedId: null,
  isLoading: false,
  error: null,
};

export const useFeatureStore = create<FeatureState & FeatureActions>()(
  devtools(
    subscribeWithSelector(
      immer((set) => ({
        ...initialState,

        setItems: (items) =>
          set((state) => {
            state.items = Object.fromEntries(items.map((i) => [i.id, i]));
            state.isLoading = false;
          }),

        upsertItem: (item) =>
          set((state) => {
            state.items[item.id] = item;
          }),

        removeItem: (id) =>
          set((state) => {
            delete state.items[id];
            if (state.selectedId === id) state.selectedId = null;
          }),

        select: (id) =>
          set((state) => {
            state.selectedId = id;
          }),

        setLoading: (loading) =>
          set((state) => {
            state.isLoading = loading;
          }),

        setError: (error) =>
          set((state) => {
            state.error = error;
            state.isLoading = false;
          }),

        reset: () => set(() => ({ ...initialState })),
      }))
    ),
    { name: "FeatureStore" }
  )
);
```

**Conventions:**
- Use `immer` middleware for mutable-style updates.
- Wrap with `devtools` (outermost) and `subscribeWithSelector`.
- Normalize collections as `Record<string, T>` keyed by ID.
- Separate state interface from actions interface, combine in `create`.
- Always include `isLoading`, `error`, and `reset`.
- Derive selectors outside the store to keep it lean:

```ts
// Selectors
export const selectFeatureList = (state: FeatureState & FeatureActions) =>
  Object.values(state.items);

export const selectSelectedFeature = (state: FeatureState & FeatureActions) =>
  state.selectedId ? state.items[state.selectedId] ?? null : null;
```

## 3. WebSocket Event Integration

The WebSocket client lives at `apps/dashboard/src/services/websocket.ts` and uses Socket.IO.

### Subscribing to Real-Time Events

```ts
// Inside a custom hook
import { useEffect } from "react";
import { socket } from "@/services/websocket";
import { useFeatureStore } from "@/stores/featureStore";

export function useFeatureSocket(projectId: string) {
  const upsertItem = useFeatureStore((s) => s.upsertItem);
  const removeItem = useFeatureStore((s) => s.removeItem);

  useEffect(() => {
    const channel = `project:${projectId}:feature`;

    socket.emit("subscribe", { channel });

    const handleUpdate = (data: { item: FeatureItem }) => {
      upsertItem(data.item);
    };

    const handleDelete = (data: { id: string }) => {
      removeItem(data.id);
    };

    socket.on("feature:updated", handleUpdate);
    socket.on("feature:deleted", handleDelete);

    return () => {
      socket.emit("unsubscribe", { channel });
      socket.off("feature:updated", handleUpdate);
      socket.off("feature:deleted", handleDelete);
    };
  }, [projectId, upsertItem, removeItem]);
}
```

**Conventions:**
- Subscribe on mount, unsubscribe on cleanup in the useEffect return.
- Use stable references from Zustand (actions are stable by default).
- Scope channels by project ID to avoid cross-project bleed.
- Name events as `<entity>:<verb>` (e.g., `feature:updated`, `agent:log`).
- The existing `useWebSocket` hook at `src/hooks/useWebSocket.ts` provides lower-level helpers; prefer it for connection state management.

## 4. API Client Integration

The API client at `apps/dashboard/src/services/api.ts` wraps fetch calls to the FastAPI backend.

### Adding a New API Module

```ts
// apps/dashboard/src/services/featureApi.ts
import { api } from "./api";

export interface CreateFeaturePayload {
  projectId: string;
  name: string;
  config?: Record<string, unknown>;
}

export const featureApi = {
  list: (projectId: string) =>
    api.get<FeatureItem[]>(`/projects/${projectId}/features`),

  get: (projectId: string, featureId: string) =>
    api.get<FeatureItem>(`/projects/${projectId}/features/${featureId}`),

  create: (payload: CreateFeaturePayload) =>
    api.post<FeatureItem>(`/projects/${payload.projectId}/features`, payload),

  update: (projectId: string, featureId: string, data: Partial<FeatureItem>) =>
    api.patch<FeatureItem>(`/projects/${projectId}/features/${featureId}`, data),

  delete: (projectId: string, featureId: string) =>
    api.delete<void>(`/projects/${projectId}/features/${featureId}`),
};
```

**Conventions:**
- Group endpoints into an object literal per domain.
- Use the shared `api` instance so auth tokens and base URL are handled.
- Type both request payloads and response generics.
- Use RESTful paths that mirror the FastAPI router structure.

## 5. Custom Hook Patterns

Hooks live at `apps/dashboard/src/hooks/`. Existing hooks: `useWebSocket.ts`, `useProject.ts`, `usePipeline.ts`, `useAgents.ts`.

### Data-Fetching Hook

```ts
// apps/dashboard/src/hooks/useFeature.ts
import { useEffect, useCallback } from "react";
import { useFeatureStore, selectFeatureList } from "@/stores/featureStore";
import { featureApi } from "@/services/featureApi";

export function useFeatures(projectId: string) {
  const items = useFeatureStore(selectFeatureList);
  const isLoading = useFeatureStore((s) => s.isLoading);
  const error = useFeatureStore((s) => s.error);
  const setItems = useFeatureStore((s) => s.setItems);
  const setLoading = useFeatureStore((s) => s.setLoading);
  const setError = useFeatureStore((s) => s.setError);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const data = await featureApi.list(projectId);
      setItems(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load features");
    }
  }, [projectId, setItems, setLoading, setError]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { items, isLoading, error, refetch: fetch };
}
```

### Action Hook

```ts
export function useCreateFeature() {
  const upsertItem = useFeatureStore((s) => s.upsertItem);

  return useCallback(
    async (payload: CreateFeaturePayload) => {
      const created = await featureApi.create(payload);
      upsertItem(created);
      return created;
    },
    [upsertItem]
  );
}
```

**Conventions:**
- Hooks that fetch data call the API, then push results into the Zustand store.
- Return `{ data, isLoading, error, refetch }` from data hooks.
- Action hooks return an async callback.
- Select individual fields from the store to minimize re-renders.
- Combine the data hook with the socket hook in the component for real-time + initial load.

## 6. Component Composition and Layout

The main layout uses `components/layout/MainLayout` with a `Sidebar` and `Header`.

### Adding a New Page/Panel

```tsx
// Compose data hook + socket hook + presentational component
import { useFeatures } from "@/hooks/useFeature";
import { useFeatureSocket } from "@/hooks/useFeatureSocket";
import { FeaturePanel } from "@/components/feature/FeaturePanel";
import { FeatureList } from "@/components/feature/FeatureList";

export const FeaturePage: FC<{ projectId: string }> = ({ projectId }) => {
  const { items, isLoading, error } = useFeatures(projectId);
  useFeatureSocket(projectId);

  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorBanner message={error} />;

  return (
    <div className="grid grid-cols-12 gap-6 p-6">
      <aside className="col-span-4">
        <FeatureList items={items} />
      </aside>
      <main className="col-span-8">
        <FeaturePanel projectId={projectId} />
      </main>
    </div>
  );
};
```

**Conventions:**
- Separate container (data) components from presentational components.
- Use CSS grid with Tailwind's `grid-cols-12` for layout.
- Loading and error states are handled at the container level.
- Panels, lists, and detail views are separate components.

## 7. Tailwind CSS Conventions

- Use Tailwind utility classes directly; avoid `@apply` except in rare shared base styles.
- Color palette: use semantic names from the project's `tailwind.config.ts` (e.g., `text-primary`, `bg-surface`, `border-muted`).
- Spacing: stick to the 4px scale (`p-1` = 4px, `p-2` = 8px, `p-4` = 16px, `p-6` = 24px).
- Responsive: mobile-first with `sm:`, `md:`, `lg:` breakpoints.
- Dark mode: use `dark:` variant classes where needed.
- Transitions: `transition-colors duration-150` for interactive elements.
- Consistent border radius: `rounded-lg` for cards/panels, `rounded` for buttons, `rounded-full` for avatars/badges.

### Common Patterns

```tsx
{/* Card */}
<div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">

{/* Primary button */}
<button className="rounded bg-primary px-4 py-2 text-sm font-medium text-white transition-colors duration-150 hover:bg-primary/90 disabled:opacity-50">

{/* Status badge */}
<span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
```

## 8. Testing React Components

Use Vitest + React Testing Library. Test files sit alongside components as `ComponentName.test.tsx`.

### Component Test

```tsx
// apps/dashboard/src/components/feature/FeaturePanel.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { FeaturePanel } from "./FeaturePanel";

describe("FeaturePanel", () => {
  const defaultProps = {
    projectId: "proj-123",
    isActive: true,
    onClose: vi.fn(),
  };

  it("renders the panel heading", () => {
    render(<FeaturePanel {...defaultProps} />);
    expect(screen.getByRole("heading", { name: /feature/i })).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    render(<FeaturePanel {...defaultProps} />);
    fireEvent.click(screen.getByLabelText("Close panel"));
    expect(defaultProps.onClose).toHaveBeenCalledOnce();
  });
});
```

### Testing with Zustand Store

```tsx
import { renderHook, act } from "@testing-library/react";
import { useFeatureStore } from "@/stores/featureStore";

describe("featureStore", () => {
  beforeEach(() => {
    useFeatureStore.getState().reset();
  });

  it("upserts an item", () => {
    const item = { id: "1", name: "Test", status: "idle" as const, updatedAt: "" };
    act(() => useFeatureStore.getState().upsertItem(item));
    expect(useFeatureStore.getState().items["1"]).toEqual(item);
  });
});
```

### Testing Hooks with Mocked API

```tsx
import { renderHook, waitFor } from "@testing-library/react";
import { useFeatures } from "@/hooks/useFeature";
import { featureApi } from "@/services/featureApi";

vi.mock("@/services/featureApi");

describe("useFeatures", () => {
  it("fetches and stores features", async () => {
    const mockData = [{ id: "1", name: "F1", status: "idle", updatedAt: "" }];
    vi.mocked(featureApi.list).mockResolvedValue(mockData);

    const { result } = renderHook(() => useFeatures("proj-123"));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.items).toEqual(mockData);
  });
});
```

**Testing conventions:**
- Reset Zustand stores in `beforeEach` using the store's `reset` action.
- Use `vi.fn()` and `vi.mock()` for mocking.
- Query elements by accessible roles and labels, not test IDs.
- Test files are co-located: `FeaturePanel.tsx` and `FeaturePanel.test.tsx` in the same directory.
- Run tests with `pnpm test` (Vitest) from `apps/dashboard/`.

## Quick Checklist for New Features

1. Define TypeScript types in `src/types/` or inline with the store.
2. Create a Zustand store at `src/stores/<feature>Store.ts` with normalized state.
3. Add API functions at `src/services/<feature>Api.ts`.
4. Build a data-fetching hook at `src/hooks/use<Feature>.ts`.
5. Build a WebSocket hook at `src/hooks/use<Feature>Socket.ts` if real-time.
6. Create presentational components at `src/components/<feature>/`.
7. Compose everything in a container/page component.
8. Write tests co-located with each component, hook, and store.

## Documentation Lookup (Context7)

Before implementing dashboard features, use Context7 to fetch current docs:

```
# Core framework
mcp__plugin_context7_context7__resolve-library-id("React")
mcp__plugin_context7_context7__query-docs(id, "hooks useTransition useDeferredValue React 19")

# State management
mcp__plugin_context7_context7__resolve-library-id("Zustand")
mcp__plugin_context7_context7__query-docs(id, "create store slices middleware persist")

# Server state
mcp__plugin_context7_context7__resolve-library-id("TanStack Query")
mcp__plugin_context7_context7__query-docs(id, "useQuery useMutation queryClient invalidation")

# Styling
mcp__plugin_context7_context7__resolve-library-id("Tailwind CSS")
mcp__plugin_context7_context7__query-docs(id, "v4 configuration theme extend")

# UI components
mcp__plugin_context7_context7__resolve-library-id("shadcn/ui")
mcp__plugin_context7_context7__query-docs(id, "component installation usage patterns")

# Visualization
mcp__plugin_context7_context7__resolve-library-id("React Flow")
mcp__plugin_context7_context7__query-docs(id, "custom nodes edges controls viewport")

# Build
mcp__plugin_context7_context7__resolve-library-id("Vite")
mcp__plugin_context7_context7__query-docs(id, "configuration proxy HMR build optimization")
```

Tailwind v4 has significant changes from v3. Always check Context7 for current class names and config syntax.
