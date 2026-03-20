# Project Layer Design

## Problem
Dashboard has no project creation/selection UI. Users land on Pipeline panel with no way to create, import, or switch between projects. Backend CRUD APIs exist at `/api/v1/projects` but have no frontend counterpart.

## Design

### Navigation Architecture
Three complementary patterns:
1. **Gateway** — Project Hub as landing page when no project is open
2. **Sidebar** — Active project switcher at top of sidebar
3. **Tabs** — Multiple open projects as tabs above the header

### Components
- `project-store.ts` — Zustand store with projects[], openProjectIds[], activeProjectId
- `project-hub.tsx` — Landing page with project grid, new/import buttons
- `project-card.tsx` — Card component for project grid
- `new-project-wizard.tsx` — Multi-step form (basics, PRD, tech stack, settings)
- `import-project-wizard.tsx` — Brownfield import (connect, detect, review, create)
- `project-tabs.tsx` — Tab bar for multiple open projects
- `project-switcher.tsx` — Sidebar dropdown for quick project switching

### State
```typescript
interface ProjectState {
  projects: Project[];
  openProjectIds: string[];
  activeProjectId: string | null; // null = show Project Hub
}
```

### Modified Files
- `ui-store.ts` — add "projects" panel
- `sidebar.tsx` — add ProjectSwitcher at top
- `header.tsx` — integrate tab bar
- `app.tsx` — gate panels behind active project
